import logging
import time
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
def verify_crew_output(gap_text: str, plan_text: str) -> str:
    prompt = f"""
            다음은 AI가 생성한 이력서 개선 분석 결과와 학습 로드맵입니다. 이 결과가 실제 평가 결과와 비교했을 때 타당하고 설득력 있는지 검토해주세요.

            [Gap 분석 결과]
            {gap_text}

            [학습 로드맵]
            {plan_text}

            응답은 아래 형식으로 JSON으로 주세요:
            {{
            "verdict": "YES" 또는 "NO",
            "reason": "간단한 사유"
            }}
            """
    return llm.invoke(prompt)

# 메인 실행 함수
async def analyze_resume_with_agent(resume_eval: str, selfintro_eval: str) -> str:
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
        task1_output = str(task1.output.raw_output if hasattr(task1.output, "raw_output") else task1.output)
        task2_output = str(task2.output.raw_output if hasattr(task2.output, "raw_output") else task2.output)

        # 4. 검증
        t5 = time.time()
        evaluation = verify_crew_output(task1_output, task2_output)
        t6 = time.time()
        print(f"[결과 검증] {t6 - t5:.2f}초")

        overall_end = time.time()
        print(f"[전체 소요 시간] {overall_end - overall_start:.2f}초")

        if "NO" in evaluation:
            return f"CrewAI 결과가 타당하지 않다고 판단됨:\n{evaluation}"

        return f"CrewAI 결과가 타당하다고 판단됨:\n\n## 개선 포인트\n{task1_output}\n\n## 학습 로드맵\n{task2_output}"

    except Exception as e:
        logging.error(f"에러 발생: {e}")
        return "에이전트 실행 중 오류가 발생했습니다."
