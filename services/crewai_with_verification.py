import logging
import time
from services.langgraph.gan_graph import graph_executor


# LangGraph 실행용 wrapper
async def run_graph_with_scores(resume_eval: str, selfintro_eval: str, resume_score: int, selfintro_score: int):
    logging.info("[run_graph_with_scores] LangGraph 실행 시작")
    logging.info(f"[점수 로그] resume_score: {resume_score}, selfintro_score: {selfintro_score}")
    start = time.time()
    result = await graph_executor.ainvoke({
        "resume_eval": resume_eval,
        "selfintro_eval": selfintro_eval,
        "resume_score": resume_score,
        "selfintro_score": selfintro_score
    })

    elapsed = time.time() - start
    logging.info(f"[run_graph_with_scores] LangGraph 실행 완료 - 총 소요시간: {elapsed:.2f}초")

    # 최종 결과만 추출해서 반환
    final = result.get("final_result")
    if isinstance(final, dict) and "type" in final:
        return final

    # fallback
    logging.warning("[run_graph_with_scores] final_result 누락됨, 상태 그대로 반환함")
    return result


