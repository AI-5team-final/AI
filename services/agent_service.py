import logging
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import List
from dotenv import load_dotenv
from exception.base import AIAnalylizeException

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    max_retries=3,
    request_timeout=60,
)

# Agent 정의
gap_analyzer = Agent(
    role="Gap Analyzer",
    goal="Analyze evaluation results and extract key skills or qualifications the user needs to improve.",
    backstory=(
        "You are an expert evaluator who reads job/resume matching evaluation results and identifies the exact skills, experiences, or qualifications that are missing."
    ),
    verbose=True,
    llm=llm
)

learning_coach = Agent(
    role="Learning Coach",
    goal="Summarize the search results and suggest a personalized learning roadmap.",
    backstory=(
        "You are a helpful AI coach who takes curated learning content and organizes it into a step-by-step plan based on user needs."
    ),
    verbose=True,
    llm=llm
)

#  매번 다른 평가 결과를 기반으로 Task 생성
def build_tasks(evaluation_result: str) -> List[Task]:
    task1 = Task(
        description=f"""
        다음 평가 결과를 분석해 사용자가 개선해야 할 기술, 자격, 경험 항목을 3~5개로 나열하세요.
        평가 결과:
        {evaluation_result}
        결과는 반드시 한국어로 리스트 형식으로 출력해주세요.
        """,
        expected_output="개선이 필요한 항목 리스트 (예: 자격증, 경력, 기술 스택 등)",
        agent=gap_analyzer
    )

    task2 = Task(
        description=""" 
        앞서 분석된 개선 항목을 기반으로 사용자가 어떤 순서로 학습하면 좋을지 제안하세요.
        리소스들을 초급 → 중급 순으로 정리하고, 2~4주 학습 플랜을 제안하세요.
        결과는 반드시 한국어로 작성해주세요.
        """,
        expected_output="주차별 학습 계획 및 추천 리소스",
        agent=learning_coach
    )

    return [task1, task2]

# 여러 채용공고에 대해 반복 호출 가능하도록 수정
async def run_resume_agent(evaluation_result: str) -> str:
    try:
        tasks = build_tasks(evaluation_result)

        crew = Crew(
            agents=[gap_analyzer, learning_coach],
            tasks=tasks,
            verbose=True
        )

        await crew.kickoff_async()

        results = []
        for task in tasks:
            if task.output:
                output_str = str(task.output.raw_output) if hasattr(task.output, "raw_output") else str(task.output)
                results.append(f"## Task by {task.agent.role}\n{output_str.strip()}\n")

        if results:
            final_result = "\n".join(results)
            logging.info(f"AI Agent 분석 결과:\n{final_result}")
            return final_result
        else:
            logging.warning("AI Agent 분석 결과가 비어 있습니다.")
            return "AI Agent 분석 결과가 비어 있습니다."

    except Exception as e:
        logging.error(f"AI Agent 실행 중 오류 발생: {e}")
        raise AIAnalylizeException()