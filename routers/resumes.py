from fastapi import APIRouter, UploadFile, File, HTTPException, Path
from bson import ObjectId, errors
from pydantic import BaseModel
from services.ocr_service import extract_text_from_uploadfile
from services.gpt_service import analyze_resume_job_matching, analyze_job_resume_matching
from services.agent_service import run_resume_agent
from db.resumes import (
    get_embedding, store_resume_from_pdf, process_resume_csv, resumes_collection
)
from db.postings import (
    search_similar_documents_with_score
)
from exception.base import (
    JobSearchException, ResumeTextMissingException,InvalidObjectIdException, MongoSaveException,
    ResumeNotFoundException ,BothNotFoundException, GptEvaluationFailedException, GptProcessingException
)
import os, asyncio, logging

router = APIRouter()


class ResumeSaveRequest(BaseModel):
    resume_text: str

# ==== 이력서 업로드 및 매칭 ====
@router.post("/match_resume")
async def match_resume_endpoint(resume: UploadFile = File(...)):
    resume_text = await extract_text_from_uploadfile(resume)
    if not resume_text:
        raise ResumeTextMissingException()

    try:
        top_matches = await search_similar_documents_with_score(resume_text, top_k=5)
        logging.info(f"[유사 공고 수]: {len(top_matches)}")
    except Exception as e:
        logging.error(f"[유사 공고 검색 실패]: {e}")
        raise JobSearchException()

    # GPT 평가 비동기 병렬 호출
    gpt_tasks = [
        analyze_resume_job_matching(resume_text, m.get("description", ""))
        for m in top_matches
    ]
    gpt_results = await asyncio.gather(*gpt_tasks, return_exceptions=True)

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
            "title": match.get("title", "제목 없음"),
            "similarity_score": round(match.get("score", 0.0), 4),
            "gpt_evaluation": evaluation
        })

    return {
            "message": "매칭 완료 (점수 순)",
            "matching_jobs": sorted(results, key=lambda x: x["gpt_evaluation"].get("total_score", 0), reverse=True)
}



# ==== 이력서 하나 저장 -> objectId 응답 ====
@router.post("/upload-pdf")
async def upload_pdf_endpoint(resume: UploadFile = File(...)):
    try:
        resume_text = await extract_text_from_uploadfile(resume)
        if not resume_text or len(resume_text.strip()) < 10:
            raise ResumeTextMissingException()

        embedding = await get_embedding(resume_text) 
        resume_id = await store_resume_from_pdf(resume_text, embedding)
        if not resume_id:
            raise MongoSaveException()

        return {"object_id": resume_id}
    
    except Exception as e:
        logging.error(f"[업로드 실패]: {e}")
        raise

# ==== 이력서 ObjectId로 하나 삭제 ====
@router.delete("/delete_resume/{resume_id}")
async def delete_resume(resume_id: str = Path(..., description="MongoDB resume 문서의 ObjectId")):
    try:
        object_id = ObjectId(resume_id)
    except (errors.InvalidId, TypeError):
        raise InvalidObjectIdException()

    result = resumes_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise ResumeNotFoundException()

    return {"message": "이력서 삭제 완료", "object_id": resume_id}


# ==== 이력서 & 채용공고 1:1 매칭 ====  agent 연동 
@router.post("/compare_resume_posting")
async def compare_resume_posting(
    resume: UploadFile = File(...),
    job_posting: UploadFile = File(...)
):
    resume_text = await extract_text_from_uploadfile(resume)
    posting_text = await extract_text_from_uploadfile(job_posting)

    if not resume_text or not posting_text:
        raise BothNotFoundException()

    try:
        evaluation_result = await analyze_job_resume_matching(resume_text, posting_text)
        if not evaluation_result or not isinstance(evaluation_result, dict) or 'summary' not in evaluation_result:
            raise GptEvaluationFailedException
    except Exception as e:
        logging.error(f"[GPT 분석 오류]: {e}")
        raise GptProcessingException()

    try:
        feedback = await run_resume_agent(evaluation_result)
    except Exception as e:
        logging.error(f"[Agent 분석 오류]: {e}")
        feedback = "AI Agent 분석 실패"

    return {
        "message": "이력서-공고 비교 완료",
        "gpt_evaluation": evaluation_result,
        "agent_feedback": feedback
    }


# ==== CSV 이력서 업로드 ====
@router.post("/upload_resume_csv")
async def upload_resume_csv(file: UploadFile = File(...)):
    try:
        content = await file.read()
        inserted_count = process_resume_csv(content)

        return {
            "message": f"{file.filename}에서 {inserted_count}개의 유효한 이력서를 저장했습니다.",
            "file": file.filename,
            "inserted": inserted_count
        }

    except Exception as e:
        logging.error(f"[CSV 이력서 처리 실패] {e}")
        raise ResumeTextMissingException()

    
