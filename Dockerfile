# 베이스 이미지
FROM python:3.12-slim

# 시스템 패키지 설치 (필요시 빌드 도구 포함)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 앱 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
