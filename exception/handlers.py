# exception/handlers.py

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from exception.discord import send_error_to_discord  
import logging


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logging.warning(f"[ValidationError] {exc.errors()}")
        await send_error_to_discord(
            f"⚠️ **유효성 검사 실패**\n📍 Path: `{request.url.path}`\n🔍 오류: `{exc.errors()}`"
        )
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={"message": "유효성 검사 실패", "detail": exc.errors()}
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logging.warning(f"[HTTPException] {exc.detail}")
        await send_error_to_discord(
            f"🚫 **HTTP 예외**\n📍 Path: `{request.url.path}`\n🔍 메시지: `{exc.detail}`\n📦 Status: {exc.status_code}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": f"HTTP 에러: {exc.detail}"}
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logging.error(f"[ValueError] {str(exc)}")
        await send_error_to_discord(
            f"🚨 **값 오류(ValueError)**\n📍 Path: `{request.url.path}`\n🔍 메시지: `{str(exc)}`"
        )
        return JSONResponse(
            status_code=400,
            content={"message": "값 오류 발생", "detail": str(exc)}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logging.critical(f"[Unhandled Exception] {str(exc)}")
        await send_error_to_discord(
            f"💥 **Unhandled Exception**\n📍 Path: `{request.url.path}`\n🧨 예외: `{type(exc).__name__}`\n🔍 메시지: `{str(exc)}`"
        )
        return JSONResponse(
            status_code=500,
            content={"message": "서버 내부 오류가 발생했습니다.", "detail": str(exc)}
        )
