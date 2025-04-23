<<<<<<< Updated upstream
# from fastapi import APIRouter,  HTTPException
# from pydantic import BaseModel
# from services.agent_service import run_resume_agent
# from exception.base import GptEvaluationNotValidException, AIAnalylizeException
# import logging
=======
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.agent_service import run_resume_agent
from exception.base import GptEvaluationNotValidException, AIAnalylizeException
import logging
>>>>>>> Stashed changes

# router = APIRouter()


# class AgentRequest(BaseModel):
#     gpt_answer: str


<<<<<<< Updated upstream
# @router.post("/analyze")
# async def analyze_with_agent(req: AgentRequest):
#     gpt_answer = req.gpt_answer.strip() 
#     logging.info(f"gpt_answer: {gpt_answer}")
=======
def extract_self_intro(text: str) -> str:
    """
    이력서 OCR 전체 텍스트에서 자기소개서 영역만 추출 (예: '1. 자기소개' 또는 '** 자기소개 **' 기준)
    """
    pattern = re.compile(r"(?:(\d+\.)|(\*\*+))\s*(자기\s?소개|자기소개서)", re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return text[match.start():].strip()
    return ""


@router.post("/analyze")
async def analyze_with_agent(req: AgentRequest):
    gpt_answer = req.gpt_answer.strip()
    logging.info(f"gpt_answer: {gpt_answer}")
>>>>>>> Stashed changes
    
#     if not gpt_answer or len(gpt_answer) < 10:
#         raise GptEvaluationNotValidException()

<<<<<<< Updated upstream
#     try:
#         feedback = await run_resume_agent(gpt_answer)
#         return {
#             "agent_feedback": feedback
#         }
#     except Exception as e:
#         logging.error(f"[Agent 분석 오류]: {e}")
#         raise AIAnalylizeException()
=======
    try:
        feedback = await run_resume_agent(gpt_answer)
        return {
            "agent_feedback": feedback
        }
    except Exception as e:
        logging.error(f"[Agent 분석 오류]: {e}")
        raise AIAnalylizeException()

@router.get("/test/analyze")
async def test_analyze_with_agent(
    eval_resume: str = Query(..., description="이력서 평가 결과"),
    eval_selfintro: str = Query(..., description="자기소개서 평가 결과")
):
    combined_input = f"""[이력서 평가]
{eval_resume.strip()}

[자기소개서 평가]
{eval_selfintro.strip()}"""

    # self_intro_txt는 OCR 전체 텍스트에서 파싱
    raw_ocr_text = f"{eval_resume.strip()}\n\n{eval_selfintro.strip()}"
    self_intro_txt = extract_self_intro(raw_ocr_text)

    try:
        feedback = await run_resume_agent(combined_input, self_intro_txt)
        return {
            "test_input": combined_input,
            "self_intro_txt": self_intro_txt.strip(),
            "agent_feedback": feedback
        }
    except Exception as e:
        logging.error(f"[Agent 테스트 오류]: {e}")
        raise AIAnalylizeException()
>>>>>>> Stashed changes
