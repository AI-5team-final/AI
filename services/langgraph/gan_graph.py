import logging
import time
import asyncio
import json
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
    final_result: dict
    evaluation: dict

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
    logging.info(f"[init_state] 분류 결과: resume_level={classify_level(state['resume_score'])}, selfintro_level={classify_level(state['selfintro_score'])}")
    if not resume_eval or not selfintro_eval:
        raise ValueError("이력서 및 자기소개서 평가 결과가 필요합니다.")
    
    logging.info("[init_state] 상태 초기화 완료")
    return {
        **state,
        "resume_level": classify_level(state["resume_score"]),
        "selfintro_level": classify_level(state["selfintro_score"]),
        "retry_count": 0,
        "simple_feedback_text": "",
        "final_result": {}
    }

# ---- 4. 조건 분기 Node: 등급 판단 ----
def decide_path(state: AgentState) -> Literal["simple", "full"]:
    logging.info("[decide_path] 분기 판단 중")
    rl = state["resume_level"]
    sl = state["selfintro_level"]
    result = "simple" if rl == "상" and sl == "상" else "full"
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
def verify_simple_feedback(state: AgentState) -> AgentState:
    logging.info("[simple_feedback_verify] 검증 시작")
    logging.info(f"[simple_feedback_verify] state.keys(): {list(state.keys())}")
    logging.info(f"[simple_feedback_verify] state['next']: {state.get('next')}")
    
    result = verify_crew_output(
        resume_eval=state["resume_eval"],
        selfintro_eval=state["selfintro_eval"],
        gap_text=state["simple_feedback_text"],
        plan_text=""
    )
    logging.info(f"[simple_feedback_verify] 검증 결과: {result}")
    if not isinstance(result, dict):
        logging.warning("[simple_feedback_verify] evaluation이 dict가 아님!")
        verdict = ""
    else:
        verdict = result.get("verdict", "")
        logging.info(f"[simple_feedback_verify] evaluation.verdict: {verdict}")
    
    outcome = "valid" if verdict == "YES" else "invalid"
    logging.info(f"[simple_feedback_verify] outcome: {outcome}")
    return {**state, "next": outcome}
    

# ---- 7. 간단 피드백 최종 응답 Node ----
def return_simple_feedback(state: AgentState) -> AgentState:
    logging.info("[simple_feedback_return] 피드백 반환")
    suggestion_text = state["simple_feedback_text"].content
    return {
        **state,
        "final_result": {
            "type": "simple",
            "message": "지원자의 이력서와 자기소개서는 매우 우수하여 큰 개선점은 발견되지 않았습니다. \n하지만 다음 단계로의 성장을 위한 제안을 드립니다.",
            "gap_text": suggestion_text
        }
    }



# ---- 9. CrewAI 실행 Node ----
USE_MOCK_MODE = False
def run_crew_agent_sync(state: AgentState) -> AgentState:
    if USE_MOCK_MODE:
        logging.info("[crew_generate] MOCK 실행 시작")

        mock_gap = "1. Git 학습 필요\n2. Redux 실습 필요"
        mock_plan = "1주차: Git 실습\n2주차: Redux 미니 프로젝트"
        mock_evaluation = {
            "verdict": "YES",
            "reason": "테스트 목업: 평가 결과와 잘 일치함"
        }
        logging.info(f"[crew_generate] MOCK 반환값: evaluation={mock_evaluation}")

        mock_result = {
            **state,
            "gap_text": mock_gap,
            "plan_text": mock_plan,
            "evaluation": mock_evaluation,
            "retry_count": state.get("retry_count", 0) + 1,
            "resume_level": classify_level(state["resume_score"]),
            "selfintro_level": classify_level(state["selfintro_score"]),
            "next": "verify"
        }
        logging.info(f"[crew_generate] 리턴 전체 상태 keys: {list(mock_result.keys())}")
        logging.info(f"[crew_generate] 리턴 next 값: {mock_result['next']}")

        return mock_result
    else:
        try:
            start = time.time()
            logging.info("[crew_generate] CrewAI 실행 시작")
            result = asyncio.run(analyze_with_raw_output(state["resume_eval"], state["selfintro_eval"]))
            elapsed = time.time() - start
            logging.info(f"[crew_generate] 완료 - {elapsed:.2f}초")

            # JSON 구조화 시도 (검증 후 단계)
            try:
                plan_obj = json.loads(result.get("plan", ""))
            except json.JSONDecodeError:
                plan_obj = {
                    "weeks": [
                        {
                            "week": "1주차",
                            "focus": "학습 계획을 파악할 수 없습니다.",
                            "tasks": [result.get("plan", "")]
                        }
                    ]
                }
            plan_json = json.dumps(plan_obj, ensure_ascii=False)

            result_state = {
                **state,
                "gap_text": result.get("gap", ""),
                "plan_text": plan_json,
                "retry_count": state["retry_count"] + 1,
                "evaluation": result.get("evaluation", {}),
                "resume_level": classify_level(state["resume_score"]),
                "selfintro_level": classify_level(state["selfintro_score"]),
                "next": "verify"
            }
            return result_state
        except Exception as e:
            logging.error(f"[crew_generate] 오류 발생: {e}")
            return {
                **state,
                "gap_text": "",
                "plan_text": "",
                "retry_count": state.get("retry_count", 0) + 1,
                "evaluation": {"verdict": "NO", "reason": str(e)},
                "resume_level": classify_level(state["resume_score"]),
                "selfintro_level": classify_level(state["selfintro_score"]),
                "next": "verify"
            }


# ---- 10. 결과 검증 Node ----
def verify_output(state: AgentState) -> AgentState:
    logging.info("[verify] 검증 시작")
    logging.info(f"[verify] state.keys(): {list(state.keys())}")
    logging.info(f"[verify] state['next']: {state.get('next')}")
    result = state.get("evaluation", None)
    logging.info(f"[verify] evaluation 타입: {type(result)} 값: {result}")

    if not isinstance(result, dict):
        logging.warning("[verify] evaluation이 dict가 아님!")
        verdict = ""
    else:
        verdict = result.get("verdict", "")
        logging.info(f"[verify] evaluation.verdict: {verdict}")
        
    logging.info(f"[verify] verdict: {verdict}")
    outcome = "valid" if verdict == "YES" else "invalid"
    logging.info(f"[verify] outcome: {outcome}")
    return {**state, "next": outcome}


# ---- 11. 최종 결과 반환 Node ----
def return_result(state: AgentState) -> AgentState:
    logging.info("[return_result] 결과 반환")
    return {
        **state,
        "final_result": {
            "type": "full",
            "message": "이력서와 자기소개서 분석 결과, 일부 개선이 필요한 항목이 확인되었습니다. \n아래 피드백과 함께, AI가 제안하는 맞춤형 학습 로드맵을 확인해보세요.",
            "gap_text": state["gap_text"],
            "plan_text": state["plan_text"]
        }
    }


# ---- 12. 실패 판단 Node ----
def retry_or_fail(state: AgentState) -> dict:
    result = "retry" if state["retry_count"] < 2 else "fail"
    logging.info(f"[retry_check] 판단 결과: {result}")
    return {**state, "next": result}

# ---- 13. 실패 반환 Node ----
def return_fail(state: AgentState) -> AgentState:
    logging.info("[fail_result] 최종 실패 반환")
    return {
        **state,
        "final_result": {
            "type": "fail",
            "message": (
                "AI가 분석한 결과가 일관되지 않아 명확한 로드맵을 생성하지 못했습니다. "
                "이는 입력된 평가 내용이 중립적이거나, AI 모델 간 해석이 달랐기 때문일 수 있습니다.\n\n"
                "더 구체적인 이력서 및 자기소개서를 입력하거나, 추가 피드백 요청을 통해 분석 정확도를 높일 수 있습니다."
            ),
            "gap_text": state.get("gap_text", ""),
            "plan_text": state.get("plan_text", "")
        }
    }



# ---- 14. 그래프 구성 ----
workflow = StateGraph(AgentState)

workflow.add_node("init", RunnableLambda(init_state))
workflow.add_node("decide", RunnableLambda(decide_path))
workflow.add_node("crew_generate", RunnableLambda(run_crew_agent_sync))
workflow.add_node("verify", RunnableLambda(verify_output))
workflow.add_node("return_result", RunnableLambda(return_result))
workflow.add_node("fail_result", RunnableLambda(return_fail))
workflow.add_node("simple_feedback_gen", RunnableLambda(generate_simple_feedback_node))
workflow.add_node("simple_feedback_verify", RunnableLambda(verify_simple_feedback))
workflow.add_node("simple_feedback_return", RunnableLambda(return_simple_feedback))
workflow.add_node("retry_check", RunnableLambda(retry_or_fail))

# 흐름 구성
workflow.set_entry_point("init")

workflow.add_conditional_edges("init", decide_path, {
    "simple": "simple_feedback_gen",
    "full": "crew_generate"
})

workflow.add_edge("crew_generate", "verify")


workflow.add_conditional_edges("verify", lambda s: s["next"], {
    "valid": "return_result",
    "invalid": "retry_check"
})

def get_retry_decision(state: AgentState) -> Literal["retry", "fail"]:
    return state.get("next", "fail")
workflow.add_conditional_edges("retry_check", get_retry_decision, {
    "retry": "crew_generate",
    "fail": "fail_result"
})


workflow.add_edge("simple_feedback_gen", "simple_feedback_verify")
workflow.add_conditional_edges("simple_feedback_verify", lambda s: s["next"], {
    "valid": "simple_feedback_return",
    "invalid": "fail_result"
})


workflow.set_finish_point(["return_result", "simple_feedback_return","fail_result"])

# 최종 실행기
graph_executor = workflow.compile()
