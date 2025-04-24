import logging
import time
from services.langgraph.gan_graph import graph_executor
from typing import Optional

async def run_graph_with_scores(resume_eval: str, selfintro_eval: str, resume_score: int, selfintro_score: int, resume_text: Optional[str] = None):
    logging.info("[run_graph_with_scores] LangGraph 실행 시작")
    logging.info(f"[점수 로그] resume_score: {resume_score}, selfintro_score: {selfintro_score}")
    logging.info(f"[입력 확인] resume_text: {resume_text[:50]}...")

    start = time.time()
    result = await graph_executor.ainvoke({
        "resume_eval": resume_eval,
        "selfintro_eval": selfintro_eval,
        "resume_score": resume_score,
        "selfintro_score": selfintro_score,
        "resume_text": resume_text
    })

    elapsed = time.time() - start
    logging.info(f"[run_graph_with_scores] LangGraph 실행 완료 - 총 소요시간: {elapsed:.2f}초")

    final = result.get("final_result", {})
    feedback = result.get("self_intro_feedback")

    if feedback:
        final["self_intro_feedback"] = feedback
        logging.info("[run_graph_with_scores] 자기소개서 첨삭 피드백 포함됨")
        

    if isinstance(final, dict) and "type" in final:
        return final

    logging.warning("[run_graph_with_scores] final_result 누락됨, 상태 그대로 반환함")
    return result
