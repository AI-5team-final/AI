from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
import logging
import os
from dotenv import load_dotenv
from services.ocr_service import extract_text_from_uploadfile  # OCR 서비스 예시

# 환경 변수 로드
load_dotenv()

RUNPOD_API_URL = os.getenv("RUNPOD_API_URL").strip()
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY").strip()

# 헤더 설정
headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

# FastAPI 서버 초기화
app = FastAPI()


# 이력서 텍스트와 채용공고 텍스트를 RunPod Worker에 전달하여 추론 요청
async def call_runpod_worker_api(resume_text: str, job_text: str) -> dict:
    # input_prompt = resume_text + "\n\n" + job_text  # RunPod Worker에 보낼 텍스트 형식
    
    payload = {
        "inputs": {
            "resume":resume_text,
            "jobpost":job_text
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(RUNPOD_API_URL, headers=headers, json=payload)

            if resp.status_code != 200:
                logging.error(f"[모델 응답 오류]: {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=500, detail="RunPod 모델 응답 오류")
            
            output = resp.json()
            return output  # 모델 응답 데이터 반환
    except Exception as e:
        logging.error(f"[RunPod 호출 실패]: {e}")
        raise HTTPException(status_code=500, detail="모델 호출 실패")