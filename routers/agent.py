from fastapi import APIRouter,  HTTPException
from pydantic import BaseModel
from services.agent_service import run_resume_agent
from exception.base import GptEvaluationNotValidException, AIAnalylizeException
import logging

router = APIRouter()


class AgentRequest(BaseModel):
    gpt_answer: str


@router.post("/analyze")
async def analyze_with_agent(req: AgentRequest):
    gpt_answer = req.gpt_answer.strip() 
    logging.info(f"gpt_answer: {gpt_answer}")
    
    if not gpt_answer or len(gpt_answer) < 10:
        raise GptEvaluationNotValidException()

    try:
        feedback = await run_resume_agent(gpt_answer)
        return {
            "agent_feedback": feedback
        }
    except Exception as e:
        logging.error(f"[Agent 분석 오류]: {e}")
        raise AIAnalylizeException()