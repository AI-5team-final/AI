import logging
import time
from services.langgraph.gan_graph import graph_executor


# LangGraph 실행용 wrapper
async def run_graph_with_scores(resume_eval: str, selfintro_eval: str, resume_score: int, selfintro_score: int):
    logging.info("[run_graph_with_scores] LangGraph 실행 시작")
    start = time.time()
    result = await graph_executor.ainvoke({
        "resume_eval": resume_eval,
        "selfintro_eval": selfintro_eval,
        "resume_score": resume_score,
        "selfintro_score": selfintro_score
    })
    elapsed = time.time() - start
    logging.info(f"[run_graph_with_scores] LangGraph 실행 완료 - 총 소요시간: {elapsed:.2f}초")

    # 결과가 타입 명시된 dict인지 확인하고 아니면 fallback 처리
    if isinstance(result, dict) and "type" in result:
        return result

    logging.warning("[run_graph_with_scores] 반환값에 'type' 필드 없음. 상태 그대로 반환함")
    return result


