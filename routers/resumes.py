from fastapi import APIRouter, UploadFile, File, Path, Form
from bson import ObjectId, errors
from pydantic import BaseModel
from typing import Optional
from services.ocr_service import extract_text_from_uploadfile
from services.model_service import analyze_job_resume_matching
from db.postings import store_job_posting, search_similar_postings_with_score
from db.resumes import (
    store_resume_from_pdf, process_resume_csv, resumes_collection
)
from exception.base import (
    SimilarFoundException, ResumeTextMissingException,InvalidObjectIdException, MongoSaveException,
    ResumeNotFoundException ,BothNotFoundException, ModelProcessingException, HTTPException
)
import asyncio, logging
from datetime import datetime
import xml.etree.ElementTree as ET

router = APIRouter()


@router.post("/match_resume")
async def match_resume(resume: UploadFile = File(...)):

    resume_text = await extract_text_from_uploadfile(resume)

    if not resume_text or len(resume_text.strip()) < 10:
        raise ResumeTextMissingException()

    # 2. 유사한 채용공고 검색
    try:
        top_matches = await search_similar_postings_with_score(resume_text, top_k=5)
        logging.info(f"[탑 매치 수]: {len(top_matches)}")
    except Exception as e:
        logging.error(f"[유사 채용공고 검색 실패]: {e}")
        raise SimilarFoundException()

    # 3. 모델 평가 비동기 실행
    model_tasks = [
        analyze_job_resume_matching(
            resume_text=resume_text,
            job_text=match.get("original_text", "")
        )
        for match in top_matches
    ]
    model_results = await asyncio.gather(*model_tasks, return_exceptions=True)
    results = []
    for i, match in enumerate(top_matches):
        model_result = model_results[i]

        if isinstance(model_result, dict) and "data" in model_result:
            raw_result = model_result["data"]
            
            # dict에서 직접 total_score 추출
            if isinstance(raw_result, dict) and "total_score" in raw_result:
                score = int(raw_result["total_score"])
            else:
                score = 0
        else:
            raw_result = "모델 평가 실패 ~~"
            score = 0

        results.append({
            "object_id": str(match.get("_id")),
            "result": raw_result,
            "startDay": match.get("startDay", ""),
            "endDay": match.get("endDay", ""),
            "total_score": score
        })

        final_results = sorted(results, key=lambda x: float(x["total_score"]), reverse=True)
        print(score)
    return {
        "resume_text": resume_text,
        "matching_resumes": [
            {k: v for k, v in item.items() if k != "total_score"}
            for item in final_results
        ]
    }


def parse_date(date_str: str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}. Use YYYY-MM-DD.")


# # ==== 이력서 / 채용공고 저장 -> objectId 응답 ====
@router.post("/upload-pdf")
async def upload_pdf_endpoint(
    file: UploadFile = File(...),
    start_day: Optional[str] = Form(None),
    end_day: Optional[str] = Form(None)
):
    try:
        print("저장요청")
        text  = await extract_text_from_uploadfile(file)

        if not text  or len(text .strip()) < 10:
            raise ResumeTextMissingException()

        # 저장 경로 분기
        if start_day and end_day:
            start_date = parse_date(start_day)
            end_date = parse_date(end_day)
            object_id = await store_job_posting(
                job_text=text ,
                start_day=start_date,
                end_day=end_date
            )
        else:
            object_id = await store_resume_from_pdf(text)

        if not object_id:
            raise MongoSaveException()

        return {"object_id": object_id}

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
        evaluation_result["data"]["resume_text"] = resume_text
        logging.info(f"result: {evaluation_result}")

        return {
            "result": evaluation_result
        }

    except Exception as e:
        logging.error(f"[런팟 오류]: {e}")
        raise ModelProcessingException()


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