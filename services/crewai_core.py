import logging
import time
import json
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# Agent 정의
gap_analyzer = Agent(
    role="Gap Analyzer",
    goal="개선 포인트 도출",
    backstory="이력서/자소서 평가 결과를 분석하여 부족한 점을 도출합니다.",
    llm=llm,
    verbose=True
)

learning_coach = Agent(
    role="Learning Coach",
    goal="학습 계획 추천",
    backstory="분석된 부족한 항목에 대해 학습 계획을 제안합니다.",
    llm=llm,
    verbose=True
)



# CrewAI 결과 검증 (Discriminator 역할)
def verify_crew_output(resume_eval: str, selfintro_eval: str, gap_text: str, plan_text: str) -> dict:
    prompt = f"""
    다음은 AI가 생성한 이력서 개선 분석 결과와 학습 로드맵입니다.
    이 결과가 실제 평가 결과와 비교했을 때 타당하고 설득력 있는지 검토해주세요.

    [이력서 평가 결과]
    {resume_eval}

    [자기소개서 평가 결과]
    {selfintro_eval}

    [Gap 분석 결과]
    {gap_text}

    [학습 로드맵]
    {plan_text}

    응답은 아래 형식의 JSON으로 주세요:
    {{
        "verdict": "YES" 또는 "NO",
        "reason": "간단한 사유"
    }}
    """
    raw = llm.invoke(prompt)
    content = raw.content if hasattr(raw, "content") else raw

    try:
        # JSON이 코드블록에 감싸져 있으므로 파싱 처리
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        json_str = content[json_start:json_end]
        return json.loads(json_str)
    except Exception as e:
        logging.warning(f"[verify_crew_output] JSON 파싱 실패: {e}")
        return {"verdict": "NO", "reason": "JSON 형식이 아님"}


# CrewAi 실행
async def analyze_with_raw_output(resume_eval: str, selfintro_eval: str) -> dict:
    try:
        overall_start = time.time()

        # 1. Task 구성
        t1 = time.time()
        task1 = Task(
            description=f"""
                        다음 이력서/자소서 평가 결과를 분석해 개선이 필요한 기술, 경험, 자격 요건을 제시하세요.

                        - 이력서 평가:
                        {resume_eval}

                        - 자기소개서 평가:
                        {selfintro_eval}

                        결과는 리스트로 출력하세요.
                        """,
            expected_output="개선 포인트 리스트",
            agent=gap_analyzer
        )

        task2 = Task(
            description="앞선 항목을 기반으로 학습 로드맵을 작성해주세요 (2~4주 계획).",
            expected_output="주차별 학습 계획",
            agent=learning_coach
        )
        t2 = time.time()
        print(f"[Task 구성] {t2 - t1:.2f}초")

        # 2. Crew 실행
        t3 = time.time()
        crew = Crew(
            agents=[gap_analyzer, learning_coach],
            tasks=[task1, task2],
            verbose=True
        )
        await crew.kickoff_async()
        t4 = time.time()
        print(f"[Crew 실행] {t4 - t3:.2f}초")

        # 3. 출력 추출
        gap = str(task1.output.raw_output if hasattr(task1.output, "raw_output") else task1.output)
        plan = str(task2.output.raw_output if hasattr(task2.output, "raw_output") else task2.output)

        # 4. 검증
        evaluation = verify_crew_output(
            resume_eval=resume_eval,
            selfintro_eval=selfintro_eval,
            gap_text=gap,
            plan_text=plan
        )

        overall_end = time.time()
        print(f"[전체 소요 시간] {overall_end - overall_start:.2f}초")

        
        logging.info("[analyze_with_raw_output] 완료")
        return {
            "gap": gap,
            "plan": plan,
            "evaluation": evaluation
        }

    except Exception as e:
        logging.error(f"에러 발생: {e}")
        raise
    

# 둘다 상, 둘중 하나 하 아닌 경우
def generate_simple_feedback(resume_eval: str, selfintro_eval: str) -> str:
    
    prompt = f"""
        다음 이력서/자기소개서 평가를 바탕으로 간단한 개선 조언 2~3줄을 작성해주세요.

        [이력서 평가]
        {resume_eval}

        [자기소개서 평가]
        {selfintro_eval}
    """
    return llm.invoke(prompt)
