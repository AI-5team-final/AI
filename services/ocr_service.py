import os
import httpx
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")

async def extract_text_from_uploadfile(file: UploadFile) -> str:
    """
    업로드된 파일을 비동기로 OCR 처리 후 텍스트 반환
    """
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
    files = {"document": (file.filename, await file.read(), file.content_type)}
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            response = await client.post(
                "https://api.upstage.ai/v1/document-ai/ocr",
                headers=headers,
                files=files
            )
            response.raise_for_status()
            return response.json().get("text", "")
        except Exception as e:
            print(f"OCR 요청 중 오류: {e}")
            return ""

async def extract_text_from_path(filepath: str) -> str:
    """
    파일 경로 기반 비동기 OCR 처리
    """
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
    filename = os.path.basename(filepath)

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            with open(filepath, "rb") as f:
                files = {"document": (filename, f, "application/pdf")}
                response = await client.post(
                    "https://api.upstage.ai/v1/document-ai/ocr",
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                return response.json().get("text", "")
        except Exception as e:
            print(f"OCR 요청 중 오류: {e}")
            return ""
