"""
CRM (Customer Relationship Management) models for the MSME SaaS platform
"""
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime, date
from typing import Optional, List, Dict
from enum import Enum
from utils.helpers import generate_uuid, validate_phone

class CustomerStatus(str, Enum):
    """Customer status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    POTENTIAL = "potential"
    BLOCKED = "blocked"

class CustomerType(str, Enum):
    """Customer type enumeration"""
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

class InteractionType(str, Enum):
    """Interaction type enumeration"""
    EMAIL = "email"
    PHONE = "phone"
    MEETING = "meeting"
    WHATSAPP = "whatsapp"
    OTHER = "other"

class CustomerBase(BaseModel):
    """Base customer model"""
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=15)
    company: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=10)
    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    status: CustomerStatus = Field(default=CustomerStatus.ACTIVE)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)
    
    # Business information
    gstin: Optional[str] = Field(None, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    
    # Credit terms
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[int] = Field(None, ge=0)  # days
    
    @validator('phone')
    def validate_phone_number(cls, v):
        if v and not validate_phone(v):
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('gstin')
    def validate_gstin(cls, v):
        if v and len(v) != 15:
            raise ValueError('GSTIN must be 15 characters long')
        return v
    
    @validator('pan')
    def validate_pan(cls, v):
        if v and len(v) != 10:
            raise ValueError('PAN must be 10 characters long')
        return v

class CustomerCreate(CustomerBase):
    """Customer creation model"""
    pass

class CustomerUpdate(BaseModel):
    """Customer update model"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=15)
    company: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=10)
    customer_type: Optional[CustomerType] = None
    status: Optional[CustomerStatus] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=1000)
    gstin: Optional[str] = Field(None, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[int] = Field(None, ge=0)

class CustomerResponse(CustomerBase):
    """Customer response model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_interaction: Optional[datetime] = None
    
    # Calculated fields
    total_invoices: int = 0
    total_revenue: float = 0
    outstanding_amount: float = 0
    
    class Config:
        from_attributes = True

class CustomerFilter(BaseModel):
    """Customer filter model"""
    customer_type: Optional[CustomerType] = None
    status: Optional[CustomerStatus] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    tags: Optional[List[str]] = None
    has_email: Optional[bool] = None
    has_phone: Optional[bool] = None
    created_from: Optional[date] = None
    created_to: Optional[date] = None

class InteractionBase(BaseModel):
    """Base interaction model"""
    customer_id: str = Field(..., min_length=1)
    type: InteractionType = Field(...)
    subject: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    interaction_date: datetime = Field(default_factory=datetime.utcnow)
    follow_up_date: Optional[datetime] = None
    completed: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list)

class InteractionCreate(InteractionBase):
    """Interaction creation model"""
    pass

class InteractionUpdate(BaseModel):
    """Interaction update model"""
    type: Optional[InteractionType] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    interaction_date: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    completed: Optional[bool] = None
    tags: Optional[List[str]] = None

class InteractionResponse(InteractionBase):
    """Interaction response model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Customer information (populated from join)
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    
    class Config:
        from_attributes = True

class CustomerStats(BaseModel):
    """Customer statistics model"""
    total_customers: int = 0
    active_customers: int = 0
    inactive_customers: int = 0
    potential_customers: int = 0
    total_revenue: float = 0
    average_revenue_per_customer: float = 0
    top_customers: List[Dict] = []
    customer_growth: List[Dict] = []
    interaction_summary: Dict = {}

class CustomerSummary(BaseModel):
    """Customer summary model"""
    id: str
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    total_invoices: int = 0
    total_revenue: float = 0
    last_invoice_date: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    status: CustomerStatus

class BulkCustomerAction(BaseModel):
    """Bulk customer action model"""
    customer_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., min_length=1)  # update_status, add_tags, etc.
    data: Dict = Field(default_factory=dict)

class CustomerImport(BaseModel):
    """Customer import model"""
    customers: List[CustomerCreate] = Field(..., min_items=1)
    skip_duplicates: bool = Field(default=True)
    update_existing: bool = Field(default=False)

class CustomerExport(BaseModel):
    """Customer export model"""
    format: str = Field(default="csv")  # csv, xlsx, json
    fields: Optional[List[str]] = None
    filters: Optional[CustomerFilter] = None

class CustomerNote(BaseModel):
    """Customer note model"""
    id: str = Field(default_factory=generate_uuid)
    customer_id: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_important: bool = Field(default=False)

class CustomerDocument(BaseModel):
    """Customer document model"""
    id: str = Field(default_factory=generate_uuid)
    customer_id: str = Field(..., min_length=1)
    document_name: str = Field(..., min_length=1, max_length=200)
    document_type: str = Field(..., min_length=1, max_length=50)
    file_path: str = Field(..., min_length=1)
    file_size: int = Field(..., gt=0)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = Field(None, max_length=500)