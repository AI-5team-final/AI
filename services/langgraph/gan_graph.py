import logging
import time
import asyncio
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda
from typing import TypedDict, Literal
from services.crewai_core import (
    analyze_with_raw_output,
    verify_crew_output,
    generate_simple_feedback
)


# ---- 1. 상태 정의 ----
class AgentState(TypedDict):
    resume_eval: str
    selfintro_eval: str
    resume_score: int
    selfintro_score: int
    resume_level: Literal['상', '중', '하']
    selfintro_level: Literal['상', '중', '하']
    gap_text: str
    plan_text: str
    retry_count: int
    simple_feedback_text: str


# ---- 2. 점수 등급 분류 함수 ----
def classify_level(score):
    if score >= 40:
        return "상"
    elif score >= 25:
        return "중"
    else:
        return "하"

# ---- 3. 상태 초기화 Node ----
def init_state(state: AgentState) -> AgentState:
    logging.debug("[init_state] 상태 초기화 시작")
    resume_eval = state.get("resume_eval", "").strip()
    selfintro_eval = state.get("selfintro_eval", "").strip()

    if not resume_eval or not selfintro_eval:
        raise ValueError("이력서 및 자기소개서 평가 결과가 필요합니다.")
    
    logging.info("[init_state] 상태 초기화 완료")
    return {
        **state,
        "resume_level": classify_level(state["resume_score"]),
        "selfintro_level": classify_level(state["selfintro_score"]),
        "retry_count": 0,
        "simple_feedback_text": ""
    }

# ---- 4. 조건 분기 Node: 등급 판단 ----
# def decide_path(state: AgentState) -> dict:
#     logging.info("[decide_path] 분기 판단 중")
#     rl = state["resume_level"]
#     sl = state["selfintro_level"]
    
#     result = "perfect" if rl == "상" and sl == "상" else "crew" if rl == "하" or sl == "하" else "improve"
    
#     logging.info(f"[decide_path] 분기 결과: {result}")
    
#     return {"next": result}
def decide_path(state: AgentState) -> Literal["perfect", "improve", "crew"]:
    logging.info("[decide_path] 분기 판단 중")
    rl = state["resume_level"]
    sl = state["selfintro_level"]
    result = "perfect" if rl == "상" and sl == "상" else "crew" if rl == "하" or sl == "하" else "improve"
    logging.info(f"[decide_path] 분기 결과: {result}")
    return result


# ---- 5. 간단 피드백 생성 (LLM 기반) ----
def generate_simple_feedback_node(state: AgentState) -> AgentState:
    start = time.time()
    logging.info("[simple_feedback_gen] 간단 피드백 생성 시작")
    feedback = generate_simple_feedback(state["resume_eval"], state["selfintro_eval"])
    elapsed = time.time() - start
    logging.info(f"[simple_feedback_gen] 완료 - {elapsed:.2f}초")
    return {
        **state,
        "simple_feedback_text": feedback
    }

# ---- 6. 간단 피드백 검증 Node ----
def verify_simple_feedback(state: AgentState) -> Literal["valid", "invalid"]:
    logging.info("[simple_feedback_verify] 검증 시작")
    result = verify_crew_output(
        resume_eval=state["resume_eval"],
        selfintro_eval=state["selfintro_eval"],
        gap_text=state["simple_feedback_text"],
        plan_text=""
    )
    logging.info(f"[simple_feedback_verify] 검증 결과: {result}")
    return "valid" if "YES" in result else "invalid"

# ---- 7. 간단 피드백 최종 응답 Node ----
def return_simple_feedback(state: AgentState) -> dict:
    logging.info("[simple_feedback_return] 피드백 반환")
    return {
        "type": "improve",
        "message": "지원서는 전반적으로 괜찮지만 일부 개선이 가능합니다.",
        "suggestion": state["simple_feedback_text"]
    }


# ---- 8. 축하 메시지 반환 ----
def return_perfect(state: AgentState) -> dict:
    logging.info("[perfect_result] 완벽 판정 반환")
    return {
        "type": "perfect",
        "message": "이력서와 자기소개서가 모두 매우 우수하여 별도의 피드백이 필요하지 않습니다."
    }


# ---- 9. CrewAI 실행 Node ----
def run_crew_agent_sync(state: AgentState) -> AgentState:
    try:
        start = time.time()
        logging.info("[crew_generate] CrewAI 실행 시작")
        result = asyncio.run(analyze_with_raw_output(state["resume_eval"], state["selfintro_eval"]))
        elapsed = time.time() - start
        logging.info(f"[crew_generate] 완료 - {elapsed:.2f}초")

        result_state = {
            **state,
            "gap_text": result.get("gap", ""),
            "plan_text": result.get("plan", ""),
            "retry_count": state["retry_count"] + 1,
            "evaluation": result.get("evaluation", {})
        }
        result_state.pop("next", None)

        logging.info(f"[crew_generate] 상태 반환: {result_state}")
        return result_state
    except Exception as e:
        logging.error(f"[crew_generate] 오류 발생: {e}")
        return {
            **state,
            "gap_text": "",
            "plan_text": "",
            "retry_count": state.get("retry_count", 0) + 1,
            "evaluation": {"verdict": "NO", "reason": str(e)}
        }


# ---- 10. 결과 검증 Node ----
def verify_output(state: AgentState) -> Literal["valid", "invalid"]:
    logging.info("[verify] 검증 시작")
    result = state.get("evaluation", {})
    
    verdict = result.get("verdict", "") if isinstance(result, dict) else ""
    logging.info(f"[verify] verdict: {verdict}")

    return "valid" if verdict == "YES" else "invalid"


# ---- 11. 최종 결과 반환 Node ----
def return_result(state: AgentState) -> dict:
    logging.info("[return_result] 결과 반환")
    return {
        "type": "crew",
        "message": "CrewAI 결과가 타당하다고 판단됨",
        "gap_text": state["gap_text"],
        "plan_text": state["plan_text"]
    }


# ---- 12. 실패 판단 Node ----
def retry_or_fail(state: AgentState):
    result = "retry" if state["retry_count"] < 2 else "fail"
    logging.info(f"[retry_check] 판단 결과: {result}")
    return result

# ---- 13. 실패 반환 Node ----
def return_fail(state: AgentState) -> dict:
    logging.info("[fail_result] 최종 실패 반환")
    return {
        "type": "fail",
        "message": (
            "CrewAI가 생성한 결과가 2회 이상 검증을 통과하지 못했습니다. "
            "입력된 평가 결과가 모호하거나, 모델 간 판단이 엇갈렸을 가능성이 있습니다.\n"
            "더 나은 결과를 원하신다면 평가 결과를 구체화하거나, 직접 피드백 요청을 검토해보세요."
        ),
        "gap_text": state.get("gap_text", ""),
        "plan_text": state.get("plan_text", "")
    }


# ---- 14. 그래프 구성 ----
workflow = StateGraph(AgentState)
# 모든 Runnable 객체 선언
# ---- 14. 그래프 구성 ----
workflow = StateGraph(AgentState)

# 모든 Runnable 객체 선언
init_node = RunnableLambda(init_state)
decide_node = RunnableLambda(decide_path)
crew_generate_node = RunnableLambda(run_crew_agent_sync)
verify_node = RunnableLambda(verify_output)
return_result_node = RunnableLambda(return_result)
fail_result_node = RunnableLambda(return_fail)
simple_feedback_gen_node = RunnableLambda(generate_simple_feedback_node)
simple_feedback_verify_node = RunnableLambda(verify_simple_feedback)
simple_feedback_return_node = RunnableLambda(return_simple_feedback)
perfect_result_node = RunnableLambda(return_perfect)
retry_check_node = RunnableLambda(retry_or_fail)

# 노드 등록
workflow.add_node("init", init_node)
workflow.add_node("decide", decide_node)
workflow.add_node("crew_generate", crew_generate_node)
workflow.add_node("verify", verify_node)
workflow.add_node("return_result", return_result_node)
workflow.add_node("fail_result", fail_result_node)
workflow.add_node("simple_feedback_gen", simple_feedback_gen_node)
workflow.add_node("simple_feedback_verify", simple_feedback_verify_node)
workflow.add_node("simple_feedback_return", simple_feedback_return_node)
workflow.add_node("perfect_result", perfect_result_node)
workflow.add_node("retry_check", retry_check_node)

# 흐름 구성
workflow.set_entry_point("init")
workflow.add_edge("init", "decide")
workflow.add_conditional_edges(
    "decide",
    {
        "perfect": perfect_result_node,
        "improve": simple_feedback_gen_node,
        "crew": crew_generate_node
    },
    # decide_path
    lambda state: decide_path(state)
)

workflow.add_edge("simple_feedback_gen", "simple_feedback_verify")
workflow.add_conditional_edges(
    "simple_feedback_verify",
    {
        "valid": simple_feedback_return_node,
        "invalid": fail_result_node
    },
    verify_simple_feedback
)

workflow.add_edge("crew_generate", "verify")
workflow.add_conditional_edges(
    "verify",
    {
        "valid": return_result_node,
        "invalid": retry_check_node
    },
    verify_output
)

workflow.add_conditional_edges(
    "retry_check",
    {
        "retry": crew_generate_node,
        "fail": fail_result_node
    },
    retry_or_fail
)


workflow.set_finish_point(["return_result", "simple_feedback_return", "perfect_result", "fail_result"])

# 최종 실행기
graph_executor = workflow.compile()
