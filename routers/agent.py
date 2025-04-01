from fastapi import APIRouter,  HTTPException
from pydantic import BaseModel
from services.agent_service import run_resume_agent

import logging

router = APIRouter()


class AgentRequest(BaseModel):
    evaluation_result: str


@router.post("/analyze")
async def analyze_with_agent(req: AgentRequest):
    evaluation_result = req.evaluation_result.strip()
    if not evaluation_result or len(evaluation_result) < 10:
        raise HTTPException(status_code=400, detail="GPT 평가 결과가 유효하지 않습니다.")

    try:
        feedback = await run_resume_agent(evaluation_result)
        return {
            "message": "AI 분석 완료",
            "agent_feedback": feedback
        }
    except Exception as e:
        logging.error(f"[Agent 분석 오류]: {e}")
        raise HTTPException(status_code=500, detail="AI 분석 중 서버 오류 발생")