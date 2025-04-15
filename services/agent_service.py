import logging
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import List
from dotenv import load_dotenv
from exception.base import AIAnalylizeException
from crewai_tools import SerperDevTool, YoutubeVideoSearchTool
import os

load_dotenv()

search_tool = SerperDevTool()
youtube_tool = YoutubeVideoSearchTool()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    request_timeout=60,
)

# Agent 정의
gap_analyzer = Agent(
    role="이력서 분석가",
    goal="이력서 평가 결과를 분석하여 부족한 기술과 경험을 도출합니다.",
    backstory="당신은 HR 전문가로서 평가 데이터를 기반으로 후보자의 기술/경험 상의 격차를 도출하는 능력을 갖춘 전문가입니다.",
    llm=llm,
    verbose=True
)

resource_searcher = Agent(
    role="학습 리소스 검색 전문가",
    goal="""
    도출된 부족 기술 키워드에 대해 실용적이고 최신 학습 리소스를 제공합니다.
    - YouTube: 한국 유튜브 채널
    - Blog: 실습형 기술 네이버블로그, Velog, 티스토리
    - 각 키워드당 최소 2~3개 추천 (제목, 링크, 추천 이유 포함)
    """,
    backstory="""
    당신은 한국인 개발자 대상의 온라인 학습 큐레이터입니다.
    검색할 때 다음을 기준으로 리소스를 찾으세요:
    1. 실무 적용 가능성 (단순 개념보다 실습 위주)
    2. 콘텐츠의 신뢰도 (유명 유튜브 채널/네이버 블로거)
    3. 한국어 콘텐츠
    """,
    tools=[search_tool, youtube_tool],
    llm=llm,
    verbose=True
)
learning_coach = Agent(
    role="개인화 학습 코치",
    goal="추천된 리소스를 기반으로 단계별 학습 계획을 수립합니다.",
    backstory="당신은 AI 학습 코치로서 사용자가 효율적으로 기술을 익힐 수 있도록 초급부터 중급까지 학습 순서를 정리해주고, 일정에 맞는 로드맵을 제시하는 데 전문화되어 있습니다.",
    llm=llm,
    verbose=True
)

#  매번 다른 평가 결과를 기반으로 Task 생성
def build_tasks(evaluation_result: str) -> List[Task]:
    task1 = Task(
    description=f"아래 이력서 평가 내용을 바탕으로 지원자가 강화해야 할 기술 및 경험 키워드를 3~5개 도출해주세요. - 출력은 반드시 한국어로 작성해주세요.\n\n평가 내용:\n{evaluation_result}",
    expected_output="도출된 부족 기술/경험 키워드 리스트 (3~5개 항목)",
    agent=gap_analyzer
    )
    task2 = Task(
    description="Task1에서 도출한 키워드를 바탕으로 실용적이고 실습 중심의 학습 리소스를 검색해주세요.\n각 키워드별로 2~3개의 YouTube 영상 또는 블로그 글을 추천하고, 제목, 링크, 추천 이유를 포함하여 제시해주세요 - 출력은 반드시 한국어로 작성해주세요..",
    expected_output="키워드별 학습 리소스 추천 리스트 제목 : 링크 (해당 링크 요약))",
    agent=resource_searcher
)
    task3 = Task(
    description="Task2에서 수집한 학습 리소스를 기반으로, 초급 → 중급 수준으로 구성된 4주 분량의 학습 로드맵을 작성해주세요.\n각 주차별 일일학습 목표와 참고 리소스를 정리해주세요. - 출력은 반드시 한국어로 작성해주세요.",
    expected_output="주차별 일일학습 계획표 및 참고 리소스 요약",
    agent=learning_coach
)

    return [task1, task2,task3]

# 여러 채용공고에 대해 반복 호출 가능하도록 수정
async def run_resume_agent(evaluation_result: str) -> str:
    try:
        tasks = build_tasks(evaluation_result)

        crew = Crew(
            agents=[gap_analyzer, resource_searcher, learning_coach],
            tasks=[task1, task2, task3],
            verbose=True,
            process="sequential"
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
