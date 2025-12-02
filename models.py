from pydantic import BaseModel, validator
from typing import Optional
import re

class UserLogin(BaseModel):
    username: str
    password: str

class LeadCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    source: str = "manual"
    notes: Optional[str] = None

    @validator("phone")
    def clean_phone(cls, v):
        digits = re.sub(r"\D", "", v)
        if len(digits) != 11 or not digits.startswith(("010", "011", "012", "015")):
            raise ValueError("egyptian mobile only")
        return digits

class HuntRequest(BaseModel):
    query: str
    city: str
    max_results: int = 20

    @validator("query", "city")
    def not_empty(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("too short")
        return v.strip()

class WhatsAppMessage(BaseModel):
    phone: str
    message: str

    @validator("phone")
    def clean_phone(cls, v):
        digits = re.sub(r"\D", "", v)
        if len(digits) != 11 or not digits.startswith(("010", "011", "012", "015")):
            raise ValueError("egyptian mobile only")
        return digits

    @validator("message")
    def msg_length(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError("message required")
        return v.strip()
        
