from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=6)
    role: str = Field(default="agent", regex="^(owner|admin|manager|agent|viewer)$")

class UserLogin(BaseModel):
    username: str
    password: str

class LeadCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    source: str = "manual"
    notes: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        cleaned = re.sub(r'\D', '', v)
        if len(cleaned) != 11:
            raise ValueError('رقم الهاتف يجب أن يكون 11 رقما')
        if not cleaned.startswith(('010', '011', '012', '015')):
            raise ValueError('رقم هاتف مصري غير صحيح')
        return cleaned

class LeadUpdate(BaseModel):
    status: Optional[str] = Field(None, regex="^(new|contacted|qualified|converted|lost)$")
    notes: Optional[str] = None
    assigned_to: Optional[str] = None

class HuntRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)
    city: str = Field(..., min_length=2, max_length=50)
    max_results: int = Field(default=20, ge=1, le=100)
    
    @validator('query')
    def validate_query(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('بحث قصير جداً')
        return v.strip()

class WhatsAppMessage(BaseModel):
    phone: str
    message: str = Field(..., min_length=1, max_length=1000)
    template: Optional[str] = None

class PermissionRequest(BaseModel):
    user_id: str
    permissions: List[str]
    expires_at: Optional[str] = None
