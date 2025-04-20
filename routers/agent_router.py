from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.crewai_with_verification import analyze_resume_with_agent
from exception.base import GptEvaluationNotValidException, AIAnalylizeException
import logging

router = APIRouter()


class AgentRequest(BaseModel):
    resume_eval: str
    selfintro_eval: str


@router.post("/analyze-test")
async def analyze_with_agent(req: AgentRequest):
    resume_eval = req.resume_eval.strip()
    selfintro_eval = req.selfintro_eval.strip()
    
    logging.info(f"[이력서 평가 결과]\n{resume_eval}")
    logging.info(f"[자기소개서 평가 결과]\n{selfintro_eval}")

    if not resume_eval or not selfintro_eval:
        raise GptEvaluationNotValidException()

    try:
        feedback = await analyze_resume_with_agent(resume_eval, selfintro_eval)
        return {
            "agent_feedback": feedback
        }
    except Exception as e:
        logging.error(f"[Agent 분석 오류]: {e}")
        raise AIAnalylizeException()
