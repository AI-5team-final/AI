from fastapi import APIRouter, UploadFile, File, Path, Form
from bson import ObjectId, errors
from pydantic import BaseModel
from services.ocr_service import extract_text_from_uploadfile
from services.gpt_service import analyze_job_resume_matching , analyze_resume_job_matching
from services.agent_service import run_resume_agent
from db.resumes import (
    get_embedding, store_resume_from_pdf, process_resume_csv, resumes_collection
)
from db.postings import (
    search_similar_documents_with_score, collection
)
from exception.base import (
    JobSearchException, ResumeTextMissingException,InvalidObjectIdException, MongoSaveException,
    ResumeNotFoundException ,BothNotFoundException, GptEvaluationFailedException, GptProcessingException
)
import asyncio, logging

router = APIRouter()

class ResumeSaveRequest(BaseModel):
    resume_text: str
class ResumeAnalysisRequest(BaseModel):
    resume_text: str 
    job_id: str
    

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
        analyze_job_resume_matching(resume_text, m.get("description", ""))
        for m in top_matches
    ]
    gpt_results = await asyncio.gather(*gpt_tasks, return_exceptions=True)

    results = []
    for i, match in enumerate(top_matches):
        gpt_result = gpt_results[i]

        # 기본값
        total_score = 0
        summary = "GPT 평가 실패"
        gpt_answer = "분석 실패"

        if isinstance(gpt_result, dict):
            total_score = gpt_result.get("total_score", 0)
            summary = gpt_result.get("summary", "요약 실패")
            gpt_answer = gpt_result.get("gpt_answer", "분석 실패")
        else:
            logging.error(f"[GPT 분석 실패 - {i}번째 공고]: {gpt_result}")

        results.append({
            "title": match.get("title", "제목 없음"),
            "total_score": total_score,
            "summary": summary,
            "gpt_answer": gpt_answer
        })

    return {
        "matching_jobs": sorted(results, key=lambda x: x.get("total_score", 0), reverse=True)
    }



# ==== 이력서 하나 저장 -> objectId 응답 ====
@router.post("/upload-pdf")
async def upload_pdf_endpoint(resume: UploadFile = File(...)):
    try:
        print("저장요청")
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

        if not isinstance(evaluation_result, dict) or not all(
            k in evaluation_result for k in ("total_score", "summary", "gpt_answer")
        ):
            raise GptEvaluationFailedException()

        return {
            "total_score": evaluation_result["total_score"],
            "summary": evaluation_result["summary"],
            "gpt_answer": evaluation_result["gpt_answer"]
        }

    except Exception as e:
        logging.error(f"[GPT 분석 오류]: {e}")
        raise GptProcessingException()



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

    
