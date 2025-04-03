import os
import logging
import httpx
import asyncio
import json

from dotenv import load_dotenv
from typing import Optional

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_URL = "https://api.openai.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

# GPT API 호출 함수
async def call_gpt_api(prompt: str, temperature: float = 0.7) -> Optional[str]:
    payload = {
        "model": "gpt-4o-mini",  # 여기서 gpt-3.5-turbo도 가능
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 1500
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(GPT_URL, headers=headers, json=payload)

                if resp.status_code == 429:
                    wait_sec = 10 + attempt * 5
                    logging.warning(f"[GPT Rate Limit] {wait_sec}초 후 재시도 ({attempt+1}/3)")
                    await asyncio.sleep(wait_sec)
                    continue

                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logging.error(f"[GPT 응답 오류]: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logging.error(f"[GPT async 호출 실패]: {e}")
            break

    return None


# 이력서와 채용공고 비교 분석 함수
async def analyze_resume_job_matching(resume_text: str, job_text: str) -> str:
    prompt = f"""
    
    너는 AI 채용 평가 전문가야. 아래와 같은 JSON 포맷으로만 응답해. **절대 설명이나 추가 텍스트 없이** JSON만 출력해.
    
    JSON 답변 예시 : {{
     "total_score": 85,
     "summary": "핵심 강점: ... / 보완점: ... / 종합 의견: 추천"
    }}


    ✅ 총점: 100점 (아래 항목별 점수 합산)
    ✅ 각 항목 점수 기준 및 배점 방식:

    1. 필수 자격요건 충족도 (30점)
    - 전혀 충족하지 않음: 0점
    - 50% 미만 충족: 10점
    - 50% 이상 충족: 20점
    - 모두 충족: 30점

    2. 기술 스택 일치도 (25점)
    - 전혀 일치하지 않음: 0점
    - 일부 기술 1~2개만 일치: 10점
    - 절반 이상 기술 일치: 20점
    - 주요 기술스택 대부분 일치: 25점

    3. 업무 경험 연관성 (20점)
    - 전혀 관련 없음: 0점
    - 일부 비슷한 경험 있음: 10점
    - 유사한 프로젝트나 경험 다수: 15점
    - 매우 높은 연관성 (직접적 경험 다수): 20점

    4. 직무 적합성 (15점)
    - 지원자가 직무와 전혀 맞지 않음: 0점
    - 가능성은 있으나 부족함: 5점
    - 직무 수행 가능 수준: 10점
    - 매우 적합하며 즉시 투입 가능: 15점

    5. 기업 문화 및 가치관 적합성 (10점)
    - 맞지 않음: 0점
    - 일부 맞음: 5점
    - 가치관/문화 완벽히 부합: 10점

    ⚠️ 반드시 위 기준을 적용해 평가할 것.

    마지막으로 종합 점수와 함께 아래 내용을 반드시 작성하라:
    - 종합 매칭 의견 (추천 여부 명확히)

    절대로 항목 기준과 점수표를 벗어나지 마라. 
    점수 기준 외 임의 판단이나 추가 감상은 금지한다.

    아래 형식으로 분석을 시작해라.

    [채용공고]
    {job_text}

    [이력서]
    {resume_text}
    """

    try:
          raw = await call_gpt_api(prompt, temperature=0.3)
          logging.info(f"[GPT 응답]: {raw}")
          result = json.loads(raw)
          return result  # { title, total_score, summary }
    except Exception as e:
         logging.error(f"[GPT JSON 파싱 실패]: {e}")
         return {
               "total_score": 0,
               "summary": "GPT 평가 실패"
           }
    
# === 일단 보류
# async def analyze_job_resume_matching(resume_text: str, job_text: str) -> dict:
#     prompt = f"""

#      너는 AI 채용 평가 전문가야. 아래와 같은 JSON 포맷으로만 응답해. **절대 설명이나 추가 텍스트 없이** JSON만 출력해.

#      다음 이력서 텍스트에서 이름, 이메일, 전화번호를 아래 JSON 형식으로 추출해줘. 설명 없이 순수한 JSON만 출력해.

#     {{
#       "name": "name",
#       "email": "email",
#       "phone": "phone",
#       "total_score": "total_score",
#       "summary": "핵심 강점: ... / 보완점: ... / 종합 의견: 추천"
#     }}

#     ✅ 총점: 100점 (아래 항목별 점수 합산)
#     ✅ 각 항목 점수 기준 및 배점 방식:

#     1. 필수 자격요건 충족도 (30점)
#     - 전혀 충족하지 않음: 0점
#     - 50% 미만 충족: 10점
#     - 50% 이상 충족: 20점
#     - 모두 충족: 30점

#     2. 기술 스택 일치도 (25점)
#     - 전혀 일치하지 않음: 0점
#     - 일부 기술 1~2개만 일치: 10점
#     - 절반 이상 기술 일치: 20점
#     - 주요 기술스택 대부분 일치: 25점

#     3. 업무 경험 연관성 (20점)
#     - 전혀 관련 없음: 0점
#     - 일부 비슷한 경험 있음: 10점
#     - 유사한 프로젝트나 경험 다수: 15점
#     - 매우 높은 연관성 (직접적 경험 다수): 20점

#     4. 직무 적합성 (15점)
#     - 지원자가 직무와 전혀 맞지 않음: 0점
#     - 가능성은 있으나 부족함: 5점
#     - 직무 수행 가능 수준: 10점
#     - 매우 적합하며 즉시 투입 가능: 15점

#     5. 기업 문화 및 가치관 적합성 (10점)
#     - 맞지 않음: 0점
#     - 일부 맞음: 5점
#     - 가치관/문화 완벽히 부합: 10점

#     ⚠️ 반드시 위 기준을 적용해 평가할 것.

#     마지막으로 종합 점수와 함께 아래 내용을 반드시 작성하라:
#     - 종합 매칭 의견 (추천 여부 명확히)

#     절대로 항목 기준과 점수표를 벗어나지 마라. 
#     점수 기준 외 임의 판단이나 추가 감상은 금지한다.

#     아래 형식으로 분석을 시작해라.

#     [채용공고]
#     {job_text}

#     [이력서]
#     {resume_text}
#     """

#     try:
#         raw = await call_gpt_api(prompt)
#         logging.info(f"[GPT 추출 응답]: {raw}")

#         # 백틱(```) 포함된 경우 제거
#         cleaned = re.sub(r"```(?:json)?", "", raw).strip("`\n ")

#         # JSON 파싱 시도
#         data = json.loads(cleaned)

#         return {
#             "name": data.get("name", "이름 없음"),
#             "email": data.get("email", ""),
#             "phone": data.get("phone", ""),
#             "total_score": data.get("total_score", 0),
#             "summary": data.get("summary", "GPT 평가 실패")
#         }
#     except Exception as e:
#         logging.error(f"[GPT 추출 실패]: {e}")
#         return {
#             "name": "이름 없음",
#             "email": "",
#             "phone": "",
#             "total_score": 0,
#             "summary": "GPT 평가 실패"
#         }



async def analyze_job_resume_matching(resume_text: str, job_text: str) -> str:
    prompt = f"""
    너는 전문 채용 매니저이자 AI 평가 모델로서 다음 평가 기준과 점수표에 따라 매우 객관적으로 지원자의 이력서와 채용공고를 비교·분석한다.

    평가 기준과 점수는 아래 절대 평가 방식으로만 판단해라. 주관적 감정이나 추가 설명 없이, 아래 기준을 벗어나면 안 된다.

    ✅ 총점: 100점 (아래 항목별 점수 합산)
    ✅ 각 항목 점수 기준 및 배점 방식:

    1. 필수 자격요건 충족도 (30점)
    - 전혀 충족하지 않음: 0점
    - 50% 미만 충족: 10점
    - 50% 이상 충족: 20점
    - 모두 충족: 30점

    2. 기술 스택 일치도 (25점)
    - 전혀 일치하지 않음: 0점
    - 일부 기술 1~2개만 일치: 10점
    - 절반 이상 기술 일치: 20점
    - 주요 기술스택 대부분 일치: 25점

    3. 업무 경험 연관성 (20점)
    - 전혀 관련 없음: 0점
    - 일부 비슷한 경험 있음: 10점
    - 유사한 프로젝트나 경험 다수: 15점
    - 매우 높은 연관성 (직접적 경험 다수): 20점

    4. 직무 적합성 (15점)
    - 지원자가 직무와 전혀 맞지 않음: 0점
    - 가능성은 있으나 부족함: 5점
    - 직무 수행 가능 수준: 10점
    - 매우 적합하며 즉시 투입 가능: 15점

    5. 기업 문화 및 가치관 적합성 (10점)
    - 맞지 않음: 0점
    - 일부 맞음: 5점
    - 가치관/문화 완벽히 부합: 10점

    ⚠️ 반드시 위 기준을 적용해 평가하고, 각 항목별 점수와 객관적 근거, 이력서와 공고의 문장 매칭 예시를 작성해라.

    마지막으로 종합 점수와 함께 아래 내용을 반드시 작성하라:
    - 핵심 강점
    - 보완이 필요한 부분
    - 종합 매칭 의견 (추천 여부 명확히)

    절대로 항목 기준과 점수표를 벗어나지 마라. 
    점수 기준 외 임의 판단이나 추가 감상은 금지한다.

    아래 형식으로 분석을 시작해라.

    [채용공고]
    {job_text}

    [이력서]
    {resume_text}
    """

    try:
        full_result = await call_gpt_api(prompt, temperature=0.3)
        if not full_result:
            return {
                "gpt_evaluation": "GPT 평가 실패",
                "summary": "요약 실패"
            }

        # 요약 부분 추출: 마지막 3줄 찾기
        summary_lines = []
        for line in full_result.splitlines():
            if any(key in line for key in ["핵심 강점", "보완이 필요한 부분", "종합 매칭 의견"]):
                summary_lines.append(line.strip())

        summary = "\n".join(summary_lines) if summary_lines else "요약 정보 없음"

        return {
            "gpt_evaluation": full_result.strip(),
            "summary": summary
        }

    except Exception as e:
        logging.error(f"[GPT 평가 실패]: {e}")
        return {
            "gpt_evaluation": "GPT 평가 실패",
            "summary": "요약 실패"
        }
