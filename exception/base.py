# exception/base.py
from fastapi import HTTPException

class ResumeNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="해당 이력서를 찾을 수 없음")

class InvalidObjectIdException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="유효하지 않은 ObjectId 형식")

class ResumeTextMissingException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="이력서 텍스트가 유효하지 않음")

class JobPostingTextMissingException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="채용공고 텍스트가 유효하지 않음")

class GptEvaluationNotValidException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="GPT 평과 결과가 유효하지 않음")

class GptEvaluationFailedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=500, detail="GPT 평가 실패")

class GptProcessingException(HTTPException):
    def __init__(self):
        super().__init__(status_code=500, detail="GPT 평가 중 오류 발생")

class MongoSaveException(HTTPException):
    def __init__(self):
        super().__init__(status_code=500, detail="MongoDB 저장 실패")

class JobSearchException(HTTPException):
    def __init__(self):
        super().__init__(status_code=500, detail="공고 검색 중 오류 발생")

class BothNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="해당 이력서 또는 채용공고 없음")

class SimilarFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=500, detail="유사 이력서 검색 중 오류 발생")

class AIAnalylizeException(HTTPException):
    def __init__(self):
        super().__init__(status_code=500, detail="AI 분석 중 서버 오류 발생")

        