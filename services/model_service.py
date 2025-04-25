import asyncio
import aiohttp
import logging
import os
import xml.etree.ElementTree as ET
import re
from typing import Optional
from dotenv import load_dotenv
from fastapi import HTTPException
from xml.etree.ElementTree import Element, tostring
from xml.dom import minidom

load_dotenv()


async def analyze_job_resume_matching(resume_text: str, job_text: str) -> dict:
    try:
        # 1. RunPod 호출
        raw = await send_to_runpod(resume_text, job_text)

        if not raw or "result" not in raw:
            raise ValueError("RunPod 모델 응답이 없거나 형식이 잘못되었습니다.")

        # 2. 정제된 XML + JSON 파싱
        pretty_xml, result_dict = clean_and_prettify_xml_and_parse(raw["result"])

        # 3. 디버깅용 출력
        print(result_dict)
        # 4. 결과 반환
        return {
            "markup": pretty_xml,   # → 보기 좋은 XML
            "data": result_dict     # → 실제 분석 결과 JSON
        }

    except Exception as e:
        logging.error(f"[모델 호출 또는 응답 실패]: {e}")
        raise HTTPException(status_code=500, detail="모델 호출 또는 응답 실패")


async def send_to_runpod(resume_text: str, job_text: str) -> dict:
    try:
        runpod_api_key = os.getenv("RUNPOD_API_KEY")
        runpod_model_id = "x1l6wnb2e1etw3"  # 👈 모델 ID 여기 직접 명시

        if not runpod_api_key:
            raise ValueError("API Key missing")

        # RunPod API endpoint 동적 생성
        run_endpoint = f"https://api.runpod.ai/v2/{runpod_model_id}/run"
        status_endpoint_template = f"https://api.runpod.ai/v2/{runpod_model_id}/status/{{}}"

        headers = {
            "Authorization": f"Bearer {runpod_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "input": {
                "resume": resume_text,
                "jobpost": job_text
            }
        }

        logging.info("[INFO] RunPod 작업 생성 요청 시작")

        # Step 1: 작업 생성
        async with aiohttp.ClientSession() as session:
            async with session.post(run_endpoint, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    raise Exception(f"[RunPod 오류] 작업 요청 실패 - 상태코드 {resp.status}")
                data = await resp.json()
                job_id = data.get("id")
                if not job_id:
                    raise Exception(f"[RunPod 오류] 작업 ID 없음: {data}")

        logging.info(f"[INFO] RunPod 작업 생성됨: ID = {job_id}")

        # Step 2: 상태 polling (최대 30회, 4초 간격 = 2분)
        for attempt in range(150):
            await asyncio.sleep(4)

            async with aiohttp.ClientSession() as session:
                async with session.get(status_endpoint_template.format(job_id), headers=headers) as status_resp:
                    status_data = await status_resp.json()
                    status = status_data.get("status")

                    logging.info(f"[RunPod 상태 확인] {status} (시도 {attempt + 1}/150)")

                    if status == "COMPLETED":
                        result = status_data.get("output")
                        logging.info(f"[RunPod 결과 수신 완료]: {result}")
                        return result
                    elif status == "FAILED":
                        raise Exception(f"[RunPod 오류] 작업 실패: {status_data}")

        raise TimeoutError("[RunPod 오류] 작업 시간이 초과되었습니다.")

    except Exception as e:
        logging.error(f"[RunPod 예외 발생]: {e}")
        return {
            "result": "<result><total_score>0</total_score><summary>RunPod 평가 실패</summary></result>"
        }



def clean_and_prettify_xml_and_parse(raw: str) -> tuple[str, dict]:
    """
    RunPod 응답 문자열을 예쁘게 정리된 XML(str)로 반환하고,
    동시에 JSON(dict) 구조로 파싱된 결과도 반환
    """
    # 1. \n 및 들여쓰기 제거
    cleaned = raw.replace("\\n", "\n").strip()

    # 2. 태그 목록 및 파싱 함수
    tags = ["total_score", "resume_score", "selfintro_score", "opinion1", "summary", "eval_resume", "eval_selfintro"]

    def extract(tag):
        match = re.search(rf"<{tag}>(.*?)</{tag}>", cleaned, re.DOTALL)
        return match.group(1).strip() if match and match.group(1).strip() else None

    parsed_dict = {}

    # 3. XML 트리 구성
    root = Element("result")
    for tag in tags:
        content = extract(tag)
        if content:
            parsed_dict[tag] = content
            child = Element(tag)
            child.text = content
            root.append(child)

    # 4. 예쁘게 정리된 XML 문자열
    rough_string = tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ").strip()

    # 5. (XML 문자열, JSON dict) 튜플로 반환
    return pretty_xml, parsed_dict