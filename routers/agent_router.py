from fastapi import APIRouter,  HTTPException
from pydantic import BaseModel
from services.agent_service import run_resume_agent
from exception.base import GptEvaluationNotValidException, AIAnalylizeException
import logging
from services.langgraph_service import build_langgraph

router = APIRouter()

class AgentRequest(BaseModel):
    resume_eval: str
    selfintro_eval: str


@router.post("/analyze-loop")
async def analyze_loop(req: AgentRequest):
    if not req.resume_eval or not req.selfintro_eval:
        raise GptEvaluationNotValidException()

    try:
        graph = build_langgraph()

        initial_state = {
            "resume_eval": req.resume_eval.strip(),
            "selfintro_eval": req.selfintro_eval.strip(),
            # "feedback_summary": "",
            # "previous_score": None,
            # "current_score": 0,
            # "iteration": 0
        }

        result = await graph.invoke(initial_state)
        return {"final_feedback": result["feedback_summary"]}
    except Exception as e:
        logging.error(f"[LangGraph 분석 오류]: {e}")
        raise AIAnalylizeException()
