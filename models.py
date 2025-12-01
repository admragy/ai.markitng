from pydantic import BaseModel, validator   # v1 فقط
from typing import Optional
import re

# ---------- Auth ----------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "agent"

    @validator("username")
    def user_length(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("username ≥ 3")
        return v.strip()

    @validator("email")
    def email_valid(cls, v):
        if not re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.\w+$", v):
            raise ValueError("invalid email")
        return v.lower()

class UserLogin(BaseModel):
    username: str
    password: str

# ---------- CRM ----------
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

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None

    @validator("status")
    def valid_status(cls, v):
        if v and v not in {"new", "contacted", "qualified", "converted", "lost"}:
            raise ValueError("invalid status")
        return v

# ---------- Hunting ----------
class HuntRequest(BaseModel):
    query: str
    city: str
    max_results: int = 20

    @validator("query", "city")
    def not_empty(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("too short")
        return v.strip()

# ---------- WhatsApp ----------
class WhatsAppMessage(BaseModel):
    phone: str
    message: str
    template: Optional[str] = None

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
            
