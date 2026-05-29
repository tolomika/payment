from fastapi import APIRouter
from api.v1.payment.controller import router as router_payment

router_v1 = APIRouter()
router_v1.include_router(router_payment, prefix="/api/v1", tags=["payments"])
