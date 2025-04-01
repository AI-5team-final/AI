from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import resumes, postings, agent

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(resumes.router, prefix="/resume", tags=["Resume"])
app.include_router(postings.router, prefix="/posting", tags=["Posting"])
app.include_router(agent.router, prefix="/agent", tags=["Agent"])