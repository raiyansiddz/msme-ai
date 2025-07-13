"""
Invoice models for the MSME SaaS platform
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from typing import Optional, List, Dict
from enum import Enum
from utils.helpers import generate_uuid, generate_invoice_number

class InvoiceStatus(str, Enum):
    """Invoice status enumeration"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    FAILED = "failed"

class InvoiceItem(BaseModel):
    """Invoice item model"""
    id: str = Field(default_factory=generate_uuid)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    total_price: float = Field(..., ge=0)
    tax_rate: float = Field(default=0.18, ge=0, le=1)  # 18% GST default
    tax_amount: float = Field(default=0, ge=0)
    
    @validator('total_price', always=True)
    def calculate_total_price(cls, v, values):
        if 'quantity' in values and 'unit_price' in values:
            return values['quantity'] * values['unit_price']
        return v
    
    @validator('tax_amount', always=True)
    def calculate_tax_amount(cls, v, values):
        if 'total_price' in values and 'tax_rate' in values:
            return values['total_price'] * values['tax_rate']
        return v

class InvoiceBase(BaseModel):
    """Base invoice model"""
    customer_id: str = Field(..., min_length=1)
    invoice_number: str = Field(default_factory=generate_invoice_number)
    issue_date: date = Field(default_factory=date.today)
    due_date: date = Field(...)
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT)
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    items: List[InvoiceItem] = Field(..., min_items=1)
    notes: Optional[str] = Field(None, max_length=1000)
    terms_and_conditions: Optional[str] = Field(None, max_length=2000)
    
    # Calculated fields
    subtotal: float = Field(default=0, ge=0)
    tax_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(default=0, ge=0)
    discount_amount: float = Field(default=0, ge=0)
    discount_percentage: float = Field(default=0, ge=0, le=100)
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        if 'issue_date' in values and v < values['issue_date']:
            raise ValueError('Due date cannot be before issue date')
        return v
    
    @validator('subtotal', always=True)
    def calculate_subtotal(cls, v, values):
        if 'items' in values:
            return sum(item.total_price for item in values['items'])
        return v
    
    @validator('tax_amount', always=True)
    def calculate_tax_amount(cls, v, values):
        if 'items' in values:
            return sum(item.tax_amount for item in values['items'])
        return v
    
    @validator('total_amount', always=True)
    def calculate_total_amount(cls, v, values):
        subtotal = values.get('subtotal', 0)
        tax_amount = values.get('tax_amount', 0)
        discount_amount = values.get('discount_amount', 0)
        return subtotal + tax_amount - discount_amount

class InvoiceCreate(InvoiceBase):
    """Invoice creation model"""
    pass

class InvoiceUpdate(BaseModel):
    """Invoice update model"""
    customer_id: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[InvoiceStatus] = None
    payment_status: Optional[PaymentStatus] = None
    items: Optional[List[InvoiceItem]] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    discount_amount: Optional[float] = Field(None, ge=0)
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)

class InvoiceResponse(InvoiceBase):
    """Invoice response model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    
    # Customer information (populated from join)
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    
    class Config:
        from_attributes = True

class InvoiceFilter(BaseModel):
    """Invoice filter model"""
    customer_id: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    payment_status: Optional[PaymentStatus] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    
    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        if v is not None and 'min_amount' in values and values['min_amount'] is not None:
            if v < values['min_amount']:
                raise ValueError('Max amount cannot be less than min amount')
        return v

class InvoiceSummary(BaseModel):
    """Invoice summary model"""
    total_invoices: int = 0
    total_amount: float = 0
    paid_amount: float = 0
    pending_amount: float = 0
    overdue_amount: float = 0
    draft_count: int = 0
    sent_count: int = 0
    paid_count: int = 0
    overdue_count: int = 0

class PaymentRecord(BaseModel):
    """Payment record model"""
    id: str = Field(default_factory=generate_uuid)
    invoice_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    payment_method: str = Field(..., min_length=1)
    transaction_id: Optional[str] = None
    notes: Optional[str] = None

class InvoiceReminder(BaseModel):
    """Invoice reminder model"""
    id: str = Field(default_factory=generate_uuid)
    invoice_id: str = Field(..., min_length=1)
    reminder_type: str = Field(..., min_length=1)  # email, whatsapp, etc.
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="sent")
    message: Optional[str] = None

class BulkInvoiceAction(BaseModel):
    """Bulk invoice action model"""
    invoice_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., min_length=1)  # mark_paid, send_reminder, etc.
    notes: Optional[str] = None

class InvoiceStats(BaseModel):
    """Invoice statistics model"""
    period: str = Field(..., min_length=1)
    total_invoices: int = 0
    total_revenue: float = 0
    average_invoice_value: float = 0
    payment_rate: float = 0
    top_customers: List[Dict] = []
    monthly_trends: List[Dict] = []