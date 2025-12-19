"""
CRM Database Models - نماذج قاعدة البيانات لإدارة علاقات العملاء
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


# ==================== Enums ====================

class LeadStatus(str, Enum):
    """حالة العميل المحتمل"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NEGOTIATING = "negotiating"
    WON = "won"
    LOST = "lost"
    NURTURING = "nurturing"


class LeadSource(str, Enum):
    """مصدر العميل"""
    FACEBOOK_AD = "facebook_ad"
    INSTAGRAM_AD = "instagram_ad"
    GOOGLE_AD = "google_ad"
    TIKTOK_AD = "tiktok_ad"
    LINKEDIN_AD = "linkedin_ad"
    ORGANIC_SEARCH = "organic_search"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    OTHER = "other"


class LeadQuality(str, Enum):
    """جودة العميل"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class InteractionType(str, Enum):
    """نوع التفاعل"""
    CALL = "call"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    MEETING = "meeting"
    NOTE = "note"
    SMS = "sms"


class Lead(BaseModel):
    """نموذج العميل المحتمل"""
    id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=10, max_length=20)
    company: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW
    source: LeadSource = LeadSource.OTHER
    quality: Optional[LeadQuality] = None
    score: float = Field(default=0.0, ge=0, le=5)
    notes: Optional[str] = None
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LeadCreate(BaseModel):
    """نموذج إنشاء عميل"""
    name: str
    phone: str
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    source: LeadSource = LeadSource.OTHER
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    """نموذج تحديث عميل"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[LeadStatus] = None
    quality: Optional[LeadQuality] = None
    score: Optional[float] = None
    notes: Optional[str] = None


class Interaction(BaseModel):
    """نموذج التفاعل"""
    id: Optional[int] = None
    lead_id: int
    type: InteractionType
    direction: str = "outbound"
    description: str
    created_at: datetime = Field(default_factory=datetime.now)


class InteractionCreate(BaseModel):
    """نموذج إنشاء تفاعل"""
    lead_id: int
    type: InteractionType
    direction: str = "outbound"
    description: str


class Task(BaseModel):
    """نموذج المهمة"""
    id: Optional[int] = None
    title: str
    type: str
    priority: str = "medium"
    status: str = "pending"
    lead_id: Optional[int] = None
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class TaskPriority(str, Enum):
    """أولوية المهمة"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Campaign(BaseModel):
    """نموذج الحملة"""
    id: Optional[int] = None
    name: str
    platform: str
    campaign_type: str
    budget: float = Field(ge=0)
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.now)


class Deal(BaseModel):
    """نموذج الصفقة"""
    id: Optional[int] = None
    title: str
    lead_id: int
    amount: float = Field(ge=0)
    stage: str
    status: str = "open"
    created_at: datetime = Field(default_factory=datetime.now)


class DashboardStats(BaseModel):
    """إحصائيات لوحة التحكم"""
    total_leads: int = 0
    new_leads_today: int = 0
    hot_leads: int = 0
    active_campaigns: int = 0
    total_conversions: int = 0
    avg_conversion_rate: float = 0.0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    leads_by_source: Dict[str, int] = {}
    leads_by_status: Dict[str, int] = {}


def calculate_lead_score(lead: Lead, interactions: List[Interaction]) -> float:
    """حساب نقاط العميل"""
    score = 0.0
    if lead.name and lead.phone:
        score += 1.0
    if lead.email:
        score += 0.5
    if lead.company:
        score += 0.3
    if interactions:
        score += min(len(interactions) * 0.2, 1.0)
    return min(round(score, 1), 5.0)


def get_lead_quality(score: float) -> LeadQuality:
    """تحديد جودة العميل"""
    if score >= 4.0:
        return LeadQuality.HOT
    elif score >= 2.5:
        return LeadQuality.WARM
    else:
        return LeadQuality.COLD
