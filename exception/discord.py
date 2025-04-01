import httpx
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1356476142814494831/lQZfL6js9mnIqy4gHF8FR3MqGoKJh-hZzEhn9EIHy4aPYdFumvaZHmIqhJFF2IgSzFQo"

class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            error_message = f"🚨 서버 오류 발생\nURL: {request.url}\nMethod: {request.method}\nError: {str(e)}"
            await send_error_to_discord(error_message)
            return JSONResponse(status_code=500, content={"message": "서버 오류가 발생했습니다."})

async def send_error_to_discord(message: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message}
        )
