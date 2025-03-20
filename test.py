import os
import requests
import json
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from typing import List
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 키 불러오기
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# FastAPI 앱 생성
app = FastAPI()

# OCR 요청 함수
def extract_text_from_file(file: UploadFile):
    """업로드된 파일을 OCR을 통해 텍스트 변환"""
    url = "https://api.upstage.ai/v1/document-ai/ocr"
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}

    files = {"document": (file.filename, file.file, file.content_type)}
    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        print(f"❌ OCR 오류: {response.json()}")
        return None

# GPT 요청 함수
def analyze_resume_with_gpt(resume_text: str, job_posting_text: str):
    """GPT를 사용하여 이력서와 채용공고 비교 분석"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    넌 세계 최고의 IT 기업 인사 담당자이자 이력서 분석 전문가야.  
    지원자의 이력서와 채용공고를 비교하여 지원자가 해당 기업의 채용공고에 맞는 인재인지 판별해줘.

    ** 분석 기준 **  
    1. **직무 적합성**: 해당 이력서가 채용공고에서 요구하는 직무와 얼마나 일치하는지 평가하세요.  
    2. **요구 기술 및 경험 매칭**: 채용공고에서 요구하는 기술/경험과 이력서에 기재된 내용이 얼마나 일치하는지 분석하세요.  
    3. **추가적인 강점**: 지원자가 채용공고의 요구사항을 초과하는 강점이 있다면 설명하세요.  
    4. **부족한 부분**: 해당 지원자가 직무에 적합하지 않은 이유나 부족한 점을 지적하세요.  
    5. **채용 가능성**: 종합적으로 채용 가능성이 어느 정도인지 점수(0~100)로 평가하고, 근거를 설명하세요.  

    ---

    ### 채용공고 요약
    ```
    {job_posting_text[:1000]}  # 길이 제한 적용
    ```

    ### 이력서 요약
    ```
    {resume_text[:1000]}  # 길이 제한 적용
    ```

    **결과 형식 (Markdown 출력 필수)**
    ```
    ### 분석 결과
    - **직무 적합성**: (설명)
    - **요구 기술 및 경험 매칭**: (설명)
    - **추가적인 강점**: (설명)
    - **부족한 부분**: (설명)
    - **채용 가능성**: XX/100 (근거 설명)
    ```
    Markdown 형식으로 출력하여 가독성을 높여서 한번만 설명해줘.
    """

    payload = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"GPT 오류: {response.json()}")
        return None

# FastAPI 엔드포인트 (파일 업로드)
@app.post("/upload")
async def upload_files(resumes: List[UploadFile] = File(...), job_postings: List[UploadFile] = File(...)):
    """
    여러 개의 이력서(PDF) 및 채용공고(이미지/PDF)를 업로드하여
    OCR을 통해 텍스트 변환 후 GPT 분석 진행.
    """
    resume_texts = []
    job_posting_texts = []

    # OCR을 통해 파일에서 텍스트 추출
    for resume in resumes:
        text = extract_text_from_file(resume)
        if text:
            resume_texts.append(text)

    for job_posting in job_postings:
        text = extract_text_from_file(job_posting)
        if text:
            job_posting_texts.append(text)

    if not resume_texts or not job_posting_texts:
        return {"error": "OCR 변환에 실패하였습니다."}

    # 분석 결과 저장
    results = []
    for resume_text in resume_texts:
        for job_posting_text in job_posting_texts:
            result = analyze_resume_with_gpt(resume_text, job_posting_text)
            if result:
                results.append({"이력서": resume.filename, "채용공고": job_posting.filename, "분석결과": result})

    return {"results": results}

# FastAPI 서버 실행
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
