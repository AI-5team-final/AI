from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import resumes, postings, agent
from exception.handlers import register_exception_handlers

app = FastAPI()

register_exception_handlers(app)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(resumes.router, prefix="/resumes", tags=["Resume"])
app.include_router(postings.router, prefix="/postings", tags=["Posting"])
app.include_router(agent.router, prefix="/agent", tags=["Agent"])

@app.get("/")
async def root():
    return {"message": "AI 이력서 매칭 API입니다."}
