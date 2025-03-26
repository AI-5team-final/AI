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
    if not resume_text or not job_text:
        print("오류: 이력서 또는 채용공고 텍스트가 비어있습니다.")
        return None

    prompt = f"""
    당신은 세계 최고 기업의 기업채용 담당자입니다.
    다음 이력서와 채용공고를 기반으로 매칭 점수를 실제 내용을 기반으로 점수와 이유를 구체적으로 작성해주세요..

    총점은 100점이며, 아래 항목에 따라 평가해주세요:
    1. 자격요건 충족도 (30): 학력, 경력, 자격
    2. 기술 일치도 (25): 보유 기술, 숙련도
    3. 업무 경험 유사성 (20): 유사 업무/도메인
    4. 직무 적합성 (15): 직무 이해도, 성과
    5. 문화 적합성 (10): 조직문화, 가치관

    [채용공고]
    {job_text}

    [이력서]
    {resume_text}

    다음 형식으로 출력해주세요:

    ## 종합 평가
    - 총점:
    - 매칭 수준: (매우 높음/높음/보통/낮음/매우 낮음)
    - 강점:
    - 보완점:

    ## 상세 평가
    1. 자격요건 (점수):
    - 이유:

    2. 기술 일치도 (점수):
    - 이유:

    3. 업무 경험 (점수):
    - 이유:

    4. 직무 적합성 (점수):
    - 이유:

    5. 문화 적합성 (점수):
    - 이유:

    ## 최종 의견
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