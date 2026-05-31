from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from core.config import config

from api.router import general_router
from utils.middlewere.x_api_key import APIKeyMiddleware



middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=config.cors.allowed_hosts,
        allow_credentials=config.cors.allowed_credentials,
        allow_origin_regex=config.cors.allowed_hosts_regex,
        allow_methods=config.cors.allowed_methods,
        allow_headers=config.cors.allowed_headers,
    ),
    Middleware(APIKeyMiddleware)
]
app = FastAPI(
    docs_url="/swagger/" if config.debug else None,
    redoc_url="/redoc/" if config.debug else None,
    middleware=middleware,
)
app.include_router(general_router)

