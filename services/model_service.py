import httpx
import asyncio
import logging
import os
import xml.etree.ElementTree as ET
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv(""HF_API_KEY).strip()
HF_API_URL = "https://api-inference.huggingface.co/models/ninky0/rezoom-llama3.1-8b-4bit-b16"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

async def call_hf_model_api() -> Optional[str]:
    payload = {
        "inputs": ""
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(HF_API_URL, headers=headers, json=payload)

                if resp.status_code == 503:
                    wait_sec = 10 + attempt * 5
                    logging.warning(f"[모델 로딩 중] {wait_sec}초 후 재시도 ({attempt+1}/3)")
                    await asyncio.sleep(wait_sec)
                    continue

                resp.raise_for_status()
                output = resp.json()
                return output[0]["generated_text"]

        except httpx.HTTPStatusError as e:
            logging.error(f"[모델 응답 오류]: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logging.error(f"[모델 호출 실패]: {e}")
            break

    return None

# ==== total_score 순 sorting할때 ====
def _extract_score_from_result(xml_string: str) -> int:
    try:
        root = ET.fromstring(xml_string)
        return int(root.findtext("total_score", default="0"))
    except Exception:
        return 0

async def analyze_job_resume_matching(resume_text: str, job_text: str) -> dict:
    try:
        # 이력서와 채용공고를 runpod로 보내고 결과를 받음
        raw = await send_to_runpod(resume_text,job_text)

        if not raw:
            raise ValueError("모델 응답이 비었습니다.")

        # 정상적으로 모델 응답이 오면, 결과를 반환
        return {
            "result": raw
        }

    except Exception as e:
        logging.error(f"[모델 호출 또는 응답 실패]: {e}")
        raise HTTPException(status_code=500, detail="모델 호출 또는 응답 실패")

async def send_to_runpod(resume_text: str, job_text: str) -> dict:
    try:
        # runpod API 엔드포인트 설정 (실제 엔드포인트로 변경)
        runpod_endpoint = "https://api.runpod.ai/v2/x1l6wnb2e1etw3/runsync"  # 실제 프로젝트 엔드포인트로 변경 필요
        
        # API Key를 환경 변수에서 가져오기
        runpod_api_key = os.getenv("RUNPOD_API_KEY")  # API 키는 환경 변수로 설정 (보안상 좋음)
        
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
            # Authorization 헤더에 API Key 추가
            headers = {
                "Authorization": f"Bearer {runpod_api_key}",
                "Content-Type": "application/json"
            }
            
            # POST 요청 보내기
            async with session.post(runpod_endpoint, json=payload, headers=headers) as response:
                if response.status == 200:
                    raw = await response.json()
                    logging.info(f"[Runpod 응답]: {raw}")
                    return raw
                else:
                    logging.error(f"Runpod API 요청 실패, 상태 코드: {response.status}")
                    return {"result": "<result><total_score>0</total_score><summary>API 요청 실패</summary></result>"}

    except Exception as e:
        logging.error(f"[모델 호출 실패]: {e}")
        return {"result": "<result><total_score>0</total_score><summary>모델 호출 실패</summary></result>"}