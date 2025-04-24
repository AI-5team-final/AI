# 1단계: 빌드 단계 (Poetry 설치 및 의존성 설정)
FROM python:3.12-slim AS builder

# 필수 패키지 설치
RUN apt-get update && apt-get install -y curl build-essential

# Poetry 설치
ENV POETRY_VERSION=2.1.2
RUN curl -sSL https://install.python-poetry.org | python3 -

# Poetry 경로 설정
ENV PATH="/root/.local/bin:$PATH"
ENV POETRY_VIRTUALENVS_CREATE=false

# 작업 디렉토리 설정
WORKDIR /

# pyproject.toml 및 poetry.lock 복사
COPY pyproject.toml poetry.lock ./

# 의존성 설치
RUN poetry install --no-root --only main

# 2단계: 실행 단계
FROM python:3.12-slim

# 작업 디렉토리
WORKDIR /

# 위에서 설치한 패키지를 복사
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /root/.local /root/.local
ENV PATH="/root/.local/bin:$PATH"

# 앱 소스 코드 복사
COPY . .

# FastAPI 앱 실행
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]