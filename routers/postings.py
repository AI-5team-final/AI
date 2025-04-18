from fastapi import APIRouter, UploadFile, File
from services.ocr_service import extract_text_from_uploadfile, extract_text_from_path
from services.model_service import _extract_score_from_result
from db.resumes import search_similar_resumes_with_score
from db.postings import store_job_posting, get_embedding_async
from exception.base import (
 JobPostingTextMissingException, SimilarFoundException
)   
from services.model_service import analyze_job_resume_matching
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



# ==== 채용공고 이력서 매칭 ====
@router.post("/match_job_posting")
async def match_job_posting(job_posting: UploadFile = File(...)):
    # 1. 채용공고 텍스트 추출
    posting_text = await extract_text_from_uploadfile(job_posting)  # 채용공고 텍스트 추출
    if not posting_text or len(posting_text.strip()) < 10:
        raise JobPostingTextMissingException()  # 텍스트가 너무 짧으면 예외 발생

    # 2. 유사한 이력서 검색
    try:
        top_matches = await search_similar_resumes_with_score(posting_text, top_k=5)  # 유사한 이력서 검색
        logging.info(f"[탑 매치 수]: {len(top_matches)}")
    except Exception as e:
        logging.error(f"[유사 이력서 검색 실패]: {e}")
        raise SimilarFoundException()  # 예외 발생 시

    # 3. 모델 평가 비동기 실행 (이제 RunPod Worker로 추론 요청)
    model_tasks = [
        analyze_job_resume_matching(
            resume_text=match.get("original_text", ""),  # 이력서 텍스트
            job_text=posting_text  # 채용공고 텍스트
        )
        for match in top_matches
    ]
    model_results = await asyncio.gather(*model_tasks, return_exceptions=True)  # 비동기 평가 수행

    # 4. 결과 정리
    results = []
    for i, match in enumerate(top_matches):
        model_result = model_results[i]

        # 기본적으로 모델 평가 실패 결과
        raw_result = "<result><total_score>0</total_score><summary>모델 평가 실패</summary></result>"  # 기본 평가 결과
        score = 0

        # 모델 응답이 <result> 형식일 경우
        if isinstance(model_result, str) and model_result.strip().startswith("<result>"):
            raw_result = model_result.strip()
            score = _extract_score_from_result(raw_result)  # 점수 추출

        results.append({
            "object_id": str(match.get("_id")),  # 이력서의 MongoDB _id
            "result": raw_result,
            "total_score": score  # 임시로 총점 포함 (정렬 후 제외)
        })

    # 결과를 총점 기준으로 내림차순 정렬 후 총점 제외
    final_results = [
        {k: v for k, v in item.items() if k != "total_score"}  # 총점 제외
        for item in sorted(results, key=lambda x: x["total_score"], reverse=True)
    ]

    return {
        "matching_resumes": final_results  # 최종 결과 반환
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
    
    