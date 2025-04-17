from fastapi import FastAPI, UploadFile, File, HTTPException
import httpx
import logging
import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import aiohttp
import re
# 환경 변수 로드
load_dotenv()

RUNPOD_API_URL = os.getenv("RUNPOD_API_URL").strip()
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY").strip()

# # 헤더 설정
# headers = {
#     "Authorization": f"Bearer {RUNPOD_API_KEY}",
#     "Content-Type": "application/json"
# }

# FastAPI 서버 초기화
app = FastAPI()

headers = {
                "Authorization": f"Bearer {RUNPOD_API_KEY}",
                "Content-Type": "application/json"
            }

# 이력서 텍스트와 채용공고 텍스트를 RunPod Worker에 전달하여 추론 요청
async def call_runpod_worker_api(resume_text: str, job_text: str) -> str:
    try:
        # runpod API 엔드포인트 설정 (환경 변수 사용)
        runpod_api_url = RUNPOD_API_URL  # 환경 변수에서 엔드포인트 가져오기
        
        # API Key를 환경 변수에서 가져오기
        runpod_api_key = RUNPOD_API_KEY 
        
        if not runpod_api_key:
            raise ValueError("Runpod API key is missing. Please set it as an environment variable.")

        # 요청 본문 설정
        payload = {
            "input": {
                "resume": resume_text,
                "jobpost": job_text
            }
        }

        # 비동기 HTTP 요청 보내기
        async with aiohttp.ClientSession() as session:
            # POST 요청 보내기
            async with session.post(runpod_api_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    raw = await response.text()  # XML 형식으로 받기
                    logging.info(f"[Runpod 응답]: {raw}")

                    # <result> 태그 추출
                    match = re.search(r"<result>.*?</result>", raw, re.DOTALL)
                    if match:
                        return match.group(0)
                    else:
                        logging.error("No <result> tag found in response")
                        return "<result><total_score>0</total_score><summary>No <result> tag found</summary></result>"

                logging.error(f"Runpod API 요청 실패, 상태 코드: {response.status}")
                return "<result><total_score>0</total_score><summary>API 요청 실패</summary></result>"

    except Exception as e:
        logging.error(f"[모델 호출 실패]: {e}")
        return "<result><total_score>0</total_score><summary>모델 호출 실패</summary></result>"
    
    # ==== total_score 순 sorting할때 ====
def _extract_score_from_result(xml_string: str) -> int:
    try:
        root = ET.fromstring(xml_string)
        return int(root.findtext("total_score", default="0"))
    except Exception:
        return 0
    
# async def analyze_job_resume_matching(resume_text: str, job_text: str) -> dict:
#     try:
#         raw = await call_runpod_worker_api()
#         logging.info(f"[HF 응답]: {raw}")

#         if not raw:
#             raise ValueError("모델 응답이 비었습니다.")

#         return {
#             "result": raw.strip()
#         }

#     except Exception as e:
#         logging.error(f"[모델 호출 또는 응답 실패]: {e}")
#         return {
#             "result": "<result><total_score>0</total_score><summary>모델 호출 실패</summary></result>"
#         }