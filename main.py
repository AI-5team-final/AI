import asyncio
import time
import logging
import os
import uvicorn
import certifi
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from services.ocr_service import extract_text_from_uploadfile, extract_text_from_path
from services.gpt_service import analyze_resume_job_matching
from postings import (
    store_job_posting,
    get_embedding_async,
    search_similar_documents_with_score
)
from resumes import (
    search_similar_resumes_with_score
)
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ca = certifi.where()
client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=ca)
db = client["Rezoom"]
CSV_DIR = "csv_uploads"
PDF_DIR = "document"
TEMP_DIR = "temp_uploads"
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# 채용공고 PDF OCR + 임베딩 저장
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

# 이력서 매칭
@app.post("/match_resume")
async def match_resume_endpoint(resume: UploadFile = File(...)):
    resume_text = await extract_text_from_uploadfile(resume)
    if not resume_text:
        raise HTTPException(400, "이력서 텍스트 없음")

    top_matches = await search_similar_documents_with_score(resume_text, top_k=5)

    tasks = [
        analyze_resume_job_matching(resume_text, m.get("description", ""))
        for m in top_matches
    ]
    analyses = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for i, match in enumerate(top_matches):
        results.append({
            "title": match.get("title", "제목 없음"),
            "similarity_score": round(match.get("score", 0.0), 4),
            "detailed_analysis": analyses[i] if not isinstance(analyses[i], Exception) else "GPT 분석 실패"
        })

    return {
        "message": "매칭 완료",
        "matching_jobs": sorted(results, key=lambda x: x["similarity_score"], reverse=True)
    }

# 채용공고 → 이력서 매칭
@app.post("/match_job_posting")
async def match_job_posting_endpoint(job_posting: UploadFile = File(...)):
    posting_text = await extract_text_from_uploadfile(job_posting)
    print("채용공고 텍스트:", posting_text[:300])  # 일부 확인

    top_matches = search_similar_resumes_with_score(posting_text, top_k=5)
    print(f"[유사도 검색 결과 수]: {len(top_matches)}")

    for m in top_matches:
        print(m)

    results = [
    {
        "name": m.get("structured", {}).get("name", "이름 없음"),
        "phone": m.get("structured", {}).get("phone", ""),
        "email": m.get("structured", {}).get("email", ""),
        "skills": m.get("structured", {}).get("skills", []),
        "education": m.get("structured", {}).get("education", ""),
        "experience": m.get("structured", {}).get("experience", ""),
        "self_intro": m.get("structured", {}).get("self_intro", ""),
        "similarity_score": round(m.get("score", 0.0), 4),
    }
    for m in top_matches
    if m.get("structured", {}).get("name") and m.get("structured", {}).get("name") != "이름 없음"
]

    return {
        "message": "채용공고와 가장 적합한 이력서를 찾았습니다.",
        "matching_resumes": sorted(results, key=lambda x: x["similarity_score"], reverse=True)
    }


# 채용공고 PDF 일괄 처리
@app.post("/upload_postings_pdf")
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

# CSV 이력서 업로드 및 저장
@app.post("/upload_resume_csv")
async def upload_resume_csv(file: UploadFile = File(...)):
    try:
        filename = file.filename
        filepath = os.path.join(CSV_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(await file.read())

        from resumes import process_resume_csv
        inserted_count = process_resume_csv(filepath)
        os.remove(filepath)

        return {
            "message": f"{filename}에서 {inserted_count}개의 유효한 이력서를 저장했습니다.",
            "file": filename,
            "inserted": inserted_count
        }

    except Exception as e:
        logging.error(f"[CSV 이력서 처리 실패] {e}")
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
