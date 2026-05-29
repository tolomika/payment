from fastapi import APIRouter
from api.v1.router import router_v1

general_router = APIRouter()
general_router.include_router(router_v1)
