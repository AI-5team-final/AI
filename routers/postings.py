from fastapi import APIRouter, UploadFile, File, HTTPException
from services.ocr_service import extract_text_from_uploadfile, extract_text_from_path
from services.gpt_service import analyze_job_resume_matching
from db.resumes import search_similar_resumes_with_score
from db.postings import store_job_posting, get_embedding_async
import os, time, asyncio, re
import logging

router = APIRouter()
PDF_DIR = "document"

# ==== 채용공고 PDF OCR + 임베딩 저장 ====
async def process_pdf_async(pdf_file: str):
    filepath = os.path.join(PDF_DIR, pdf_file)
    filename = os.path.basename(filepath)
    try:
        text = await extract_text_from_path(filepath)
        if not text:
            return filename, False
        embedding = await get_embedding_async(text)
        store_job_posting(filename[:-4], text, embedding)
        return filename, True
    except Exception as e:
        logging.error(f"[{filename} 처리 실패] {e}")
        return filename, False

def extract_from_original_text(text: str) -> dict:
    """비정형 original_text에서 이름 추출"""
    name_match = re.search(r"(?:이름[:：]?\s*)?([가-힣]{2,4})", text)
    return {
        "name": name_match.group(1) if name_match else "이름 없음"
    }


@router.post("/match_job_posting_summary")
async def match_job_posting_summary(job_posting: UploadFile = File(...)):
    posting_text = await extract_text_from_uploadfile(job_posting)
    if not posting_text or len(posting_text.strip()) < 10:
        raise HTTPException(400, "채용공고 텍스트가 유효하지 않습니다.")

    try:
        top_matches = await search_similar_resumes_with_score(posting_text, top_k=5)
        logging.info(f"[탑 매치 수]: {len(top_matches)}")
    except Exception as e:
        logging.error(f"[유사 이력서 검색 실패]: {e}")
        raise HTTPException(500, "유사 이력서 검색 중 오류 발생")

    resume_texts = []
    raw_infos = []

    for match in top_matches:
        structured = match.get("structured", {})
        original_text = match.get("original_text", "")
        resume_text = structured.get("self_intro") or original_text
        resume_texts.append(resume_text)

        raw_infos.append({
            "structured": structured,
            "original_text": original_text,
            "resume_text": resume_text
        })

    gpt_tasks = [
        analyze_job_resume_matching(data["resume_text"], posting_text)
        for data in raw_infos
    ]
    gpt_results = await asyncio.gather(*gpt_tasks, return_exceptions=True)

    results = []
    for i, gpt_result in enumerate(gpt_results):
        if isinstance(gpt_result, dict):
            name = gpt_result.get("name")
            if not name:
                fallback = extract_from_original_text(raw_infos[i]["original_text"])
                name = fallback["name"]
            results.append({
                "name": name,
                "summary": gpt_result.get("summary", "요약 없음")
        })
        else:
            fallback = extract_from_original_text(raw_infos[i]["original_text"])
            results.append({
                "name": fallback["name"],
                "summary": "GPT 평가 실패"
        })

    return {
        "message": "이력서 요약 및 분석 결과입니다.",
        "matching_resumes": results
    }






# ==== 채용공고 PDF 일괄 처리 ==== 채용공고는 하나씩 올리는게 번거로워 document에 있는 폴더의 pdf를 등록하게끔 해놨습니다. 나중에 수정 예정
@router.post("/upload_postings_pdf")
async def store_all_documents_endpoint_async():
    start = time.time()
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    tasks = [process_pdf_async(f) for f in pdf_files]
    results = await asyncio.gather(*tasks)

    success = [f for f, ok in results if ok]
    failed = [f for f, ok in results if not ok]

    return {
        "total": len(pdf_files),
        "success": len(success),
        "failed": failed,
        "elapsed_time": round(time.time() - start, 2)
    }