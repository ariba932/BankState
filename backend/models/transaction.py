from pydantic import BaseModel
from typing import Optional

class Transaction(BaseModel):
    date: str
    amount: float
    currency: str = "NGN"
    description: Optional[str] = None
    type: str  # debit/credit
    reference: Optional[str] = None
    balance: Optional[float] = None
