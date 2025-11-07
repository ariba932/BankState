

from fastapi import FastAPI

from api.routes import router as statement_router
from api.webhook import router as webhook_router



@app.get("/")
def read_root():
    return {"message": "Bank Statement Reconciliation API"}

app.include_router(statement_router)
app.include_router(webhook_router)
