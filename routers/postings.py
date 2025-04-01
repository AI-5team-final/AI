from fastapi import APIRouter, UploadFile, File
from services.ocr_service import extract_text_from_uploadfile, extract_text_from_path
from services.gpt_service import analyze_resume_job_matching
from db.resumes import search_similar_resumes_with_score
from db.postings import store_job_posting, get_embedding_async
from exception.base import (
 JobPostingTextMissingException, SimilarFoundException
)   
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

# def extract_from_original_text(text: str) -> dict:
#     """비정형 original_text에서 이름 추출"""
#     name_match = re.search(r"(?:이름[:：]?\s*)?([가-힣]{2,4})", text)
#     return {
#         "name": name_match.group(1) if name_match else "이름 없음"
#     }


@router.post("/match_job_posting_summary")
async def match_job_posting_summary(job_posting: UploadFile = File(...)):
    posting_text = await extract_text_from_uploadfile(job_posting)
    if not posting_text or len(posting_text.strip()) < 10:
        raise JobPostingTextMissingException()

    try:
        top_matches = await search_similar_resumes_with_score(posting_text, top_k=5)
        logging.info(f"[탑 매치 수]: {len(top_matches)}")
    except Exception as e:
        logging.error(f"[유사 이력서 검색 실패]: {e}")
        raise SimilarFoundException()

    # GPT 평가 요청
    gpt_tasks = [
        analyze_resume_job_matching(
            resume_text=match.get("original_text", ""),
            job_text=posting_text
        )
        for match in top_matches
    ]
    gpt_results = await asyncio.gather(*gpt_tasks, return_exceptions=True)

    # 결과 정리
    results = []
    for i, match in enumerate(top_matches):
        gpt_result = gpt_results[i]
        evaluation = {
            "total_score": 0,
            "summary": "GPT 평가 실패"
        }

        if isinstance(gpt_result, dict):
            evaluation["total_score"] = gpt_result.get("total_score", 0)
            evaluation["summary"] = gpt_result.get("summary", "요약 실패")

        results.append({
            "similarity_score": round(match.get("score", 0.0), 4),
            "gpt_evaluation": evaluation
        })

    return {
        "matching_resumes": sorted(results, key=lambda x: x["gpt_evaluation"]["total_score"], reverse=True)
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