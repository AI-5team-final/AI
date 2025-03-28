import os
import openai
import logging
import httpx
import asyncio
import json
from dotenv import load_dotenv
from typing import Optional
from typing import Dict, Any

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GPT_URL = "https://api.openai.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

async def call_gpt_api(prompt: str, temperature: float = 0.7) -> Optional[str]:
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 1000
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

async def analyze_resume_job_matching(resume_text: str, job_text: str) -> Optional[str]:
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

    return await call_gpt_api(prompt, temperature=0.7)

def summarize_self_intro(text: str, max_length: int = 300) -> str:
    if len(text) <= max_length:
        return text
    try:
        logging.info("[GPT 요약 시작]")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"다음 자기소개를 {max_length}자 이내로 간결하게 요약해줘. 핵심 경력과 강점만 남겨줘."},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=300
        )
        summary = response['choices'][0]['message']['content'].strip()
        return summary
    except Exception as e:
        return text

def extract_fields_from_line(line: str) -> Dict[str, Any] | None:
    try:
        prompt = f"""
            다음 텍스트는 한 명의 이력서입니다. 아래의 JSON 형식에 맞춰 정확하게 추출해주세요. 
            각 항목은 해당 필드에 해당하는 정보만 포함하며, 항목 간 섞임이 없도록 주의하세요.

            형식:
            {{  
                "name": "이름",
                "phone": "전화번호",
                "email": "이메일",
                "skills": "기술1, 기술2, ...",
                "education": "최종 학력 및 전공",
                "experience": "주요 경력 또는 직무",
                "self_intro": "자기소개 전체 문장"
            }}

            필수 조건:
            - 항목 간 중복 없이 정확히 분리
            - `skills`, `education`, `experience` 는 혼동하지 말 것
            - `self_intro`는 완전한 문장이어야 함 (중간에 끊기지 않게)
            반드시 JSON만 출력하고, 설명은 생략하세요.

            [이력서 텍스트]
            {line.strip()}
            """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 JSON 형식에 맞춰 이력서를 정확히 필드별로 분리하는 전문가야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=700
            
        )

        result = response['choices'][0]['message']['content'].strip()
        parsed = json.loads(result)

        parsed['skills'] = [s.strip() for s in parsed.get('skills', '').split(',') if s.strip()]
        return parsed

    except Exception as e:
        logging.error(f"[GPT 필드 추출 실패]: {e}")
        return None