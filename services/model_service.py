import httpx
import asyncio
import logging
import os
import xml.etree.ElementTree as ET
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY").strip()
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
        raw = await call_hf_model_api()
        logging.info(f"[HF 응답]: {raw}")

        if not raw:
            raise ValueError("모델 응답이 비었습니다.")

        return {
            "result": raw.strip()
        }

    except Exception as e:
        logging.error(f"[모델 호출 또는 응답 실패]: {e}")
        return {
            "result": "<result><total_score>0</total_score><summary>모델 호출 실패</summary></result>"
        }

