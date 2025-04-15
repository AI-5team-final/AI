import httpx
import asyncio
import logging
import os
import xml.etree.ElementTree as ET
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_URL = os.getenv("RUNPOD_API_URL").strip()

headers = {
    "Content-Type": "application/json"
}

async def call_runpod_model_api(input_text: str) -> Optional[str]:
    payload = {
        "inputs": input_text
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(RUNPOD_API_URL, headers=headers, json=payload)

                if resp.status_code == 503:
                    wait_sec = 10 + attempt * 5
                    logging.warning(f"[모델 로딩 중] {wait_sec}초 후 재시도 ({attempt+1}/3)")
                    await asyncio.sleep(wait_sec)
                    continue

                resp.raise_for_status()
                output = resp.json()
                
                if isinstance(output, list) and "generated_text" in output[0]:
                    return output[0]["generated_text"]
                elif isinstance(output, dict) and "output" in output:
                    return output["output"]
                else:
                    logging.error(f"[RunPod 응답 포맷 오류]: 예상치 못한 형식 - {output}")
                    return None

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
        input_prompt = resume_text + "\n\n" + job_text  # 모델 학습 형식에 따라 조정 가능
        raw = await call_runpod_model_api(input_prompt)
        logging.info(f"[RunPod 응답]: {raw}")

        if not raw:
            raise ValueError("RunPod 모델 응답이 비었습니다.")

        return {
            "result": raw.strip()
        }

    except Exception as e:
        logging.error(f"[RunPod 모델 추론 실패]: {e}")
        return {
            "result": "<result><total_score>0</total_score><summary>RunPod 모델 호출 실패</summary></result>"
        }

