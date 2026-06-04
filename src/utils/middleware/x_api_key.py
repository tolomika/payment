from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import config



class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/docs/", "/openapi.json", "/redoc/", "/swagger/"]:
            return await call_next(request)

        client_key = request.headers.get("X-API-Key")

        if not client_key or client_key != config.api_key.get_secret_value():
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API Key"},
            )

        return await call_next(request)
