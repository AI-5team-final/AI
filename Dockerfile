FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y curl build-essential

ENV POETRY_VERSION=2.1.2
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

FROM python:3.12-slim
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /root/.local /root/.local
ENV PATH="/root/.local/bin:$PATH"

COPY . .

# FastAPI 앱 실행
CMD ["poetry","run","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]