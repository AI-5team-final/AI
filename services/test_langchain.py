# import logging
# from langchain.chat_models import ChatOpenAI
# from langchain.prompts import PromptTemplate
# from langchain.chains import SequentialChain, LLMChain
# from dotenv import load_dotenv
# import asyncio

# from exception.base import AIAnalylizeException

# load_dotenv()

# llm = ChatOpenAI(
#     model="gpt-4o-mini",
#     temperature=0.3,
#     max_retries=3,
#     request_timeout=60,
# )

# # 1단계: Gap 분석 체인
# gap_template = PromptTemplate(
#     input_variables=["evaluation_result"],
#     template="""
# 다음은 이력서와 채용공고 간의 매칭 평가 결과입니다.

# {evaluation_result}

# 이 평가 결과를 기반으로, 사용자가 개선해야 할 기술, 자격, 경험 항목을 3~5개로 리스트 형식(한국어)으로 작성해주세요.
# """
# )

# gap_chain = LLMChain(llm=llm, prompt=gap_template, output_key="gap_items")

# # 2단계: 학습 계획 체인
# learning_template = PromptTemplate(
#     input_variables=["gap_items"],
#     template="""
# 아래는 사용자가 보완해야 할 항목 리스트입니다:

# {gap_items}

# 이를 바탕으로 2~4주 분량의 학습 로드맵을 주차별로 제안하고, 초급 → 중급 순으로 추천 리소스를 작성해주세요. 결과는 한국어로 작성해주세요.
# """
# )

# learning_chain = LLMChain(llm=llm, prompt=learning_template, output_key="learning_plan")

# # 전체 체인 구성
# chain = SequentialChain(
#     chains=[gap_chain, learning_chain],
#     input_variables=["evaluation_result"],
#     output_variables=["gap_items", "learning_plan"],
#     verbose=True
# )

# # 실행 함수
# async def run_resume_agent(evaluation_result: str) -> str:
#     try:
#         # LangChain은 비동기 지원 안하므로 쓰레드로 비동기화
#         loop = asyncio.get_event_loop()
#         result = await loop.run_in_executor(None, lambda: chain.invoke({"evaluation_result": evaluation_result}))

#         formatted = f"## 개선 항목\n{result['gap_items']}\n\n## 학습 로드맵\n{result['learning_plan']}"
#         logging.info(f"LangChain 분석 결과:\n{formatted}")
#         return formatted

#     except Exception as e:
#         logging.error(f"[LangChain 분석 실패] {e}")
#         raise AIAnalylizeException()

