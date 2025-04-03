FROM python:3.9-slim

# Poetry 설치
RUN pip install --no-cache-dir "poetry==2.1.1"

# 작업 디렉토리 설정
WORKDIR /app

# pyproject.toml & poetry.lock 복사 → 의존성 설치
COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# 애플리케이션 소스 복사
COPY . /app

# FastAPI 실행 (필요 시 main:app 위치 수정)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
