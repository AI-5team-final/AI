from fastapi import APIRouter,  HTTPException
from pydantic import BaseModel
from services.agent_service import run_resume_agent
from exception.base import GptEvaluationNotValidException, AIAnalylizeException
import logging

router = APIRouter()


class AgentRequest(BaseModel):
    evaluation_result: str


@router.post("/analyze")
async def analyze_with_agent(req: AgentRequest):
    evaluation_result = req.evaluation_result.strip()
    if not evaluation_result or len(evaluation_result) < 10:
        raise GptEvaluationNotValidException()

    try:
        feedback = await run_resume_agent(evaluation_result)
        return {
            "agent_feedback": feedback
        }
    except Exception as e:
        logging.error(f"[Agent 분석 오류]: {e}")
        raise AIAnalylizeException()