from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/webhook/erp-notification")
async def erp_webhook(request: Request):
    payload = await request.json()
    # TODO: Process ERP notification payload
    # For now, just echo back
    return JSONResponse({"received": payload})
