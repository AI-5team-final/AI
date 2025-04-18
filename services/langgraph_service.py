# langgraph_service.py

from langgraph.graph import StateGraph
from typing import TypedDict
from .crewai_service import run_resume_agent  # 기존 Agent 평가 함수 재사용
from models.local_model_runner import get_score_from_feedback  # 학습 모델로 점수 추출

class ResumeAnalysisState(TypedDict):
    resume_eval: str
    selfintro_eval: str
    feedback_summary: str
    previous_score: int
    current_score: int
    iteration: int

async def generate_feedback(state: ResumeAnalysisState) -> ResumeAnalysisState:
    feedback = await run_resume_agent(
        resume_eval=state["resume_eval"],
        selfintro_eval=state["selfintro_eval"]
    )

    score = get_score_from_feedback(feedback)

    return {
        **state,
        "feedback_summary": feedback,
        "current_score": score
    }

def check_improvement(state: ResumeAnalysisState) -> str:
    return "improved" if (state["current_score"] > state["previous_score"]) or (state["iteration"] >= 3) else "not_improved"

def loop_update(state: ResumeAnalysisState) -> ResumeAnalysisState:
    return {
        **state,
        "previous_score": state["current_score"],
        "iteration": state["iteration"] + 1
    }

def build_langgraph():
    builder = StateGraph(ResumeAnalysisState)
    builder.add_node("generate_feedback", generate_feedback)
    builder.add_node("loop_update", loop_update)
    builder.add_conditional_edges("generate_feedback", check_improvement, {
        "improved": "END",
        "not_improved": "loop_update"
    })
    builder.add_edge("loop_update", "generate_feedback")
    builder.set_entry_point("generate_feedback")
    return builder.compile()
