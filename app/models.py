from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: Optional[int]
    username: str
    email: str
    password: str

class FinanceEntry(BaseModel):
    id: Optional[int]
    user_id: int
    description: str
    amount: float
    currency: str
    created_at: Optional[str]
