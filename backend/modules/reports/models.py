"""
Reports models for the MSME SaaS platform
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from utils.helpers import generate_uuid

class ReportType(str, Enum):
    """Report type enumeration"""
    FINANCIAL = "financial"
    SALES = "sales"
    CUSTOMER = "customer"
    INVOICE = "invoice"
    BUSINESS_OVERVIEW = "business_overview"
    CUSTOM = "custom"

class ReportPeriod(str, Enum):
    """Report period enumeration"""
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    """Report format enumeration"""
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"

class ReportRequest(BaseModel):
    """Report request model"""
    report_type: ReportType = Field(...)
    period: ReportPeriod = Field(...)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    format: ReportFormat = Field(default=ReportFormat.JSON)
    include_charts: bool = Field(default=True)
    include_insights: bool = Field(default=True)

class FinancialMetrics(BaseModel):
    """Financial metrics model"""
    total_revenue: float = 0
    total_invoices: int = 0
    paid_invoices: int = 0
    pending_invoices: int = 0
    overdue_invoices: int = 0
    average_invoice_value: float = 0
    total_outstanding: float = 0
    collection_rate: float = 0
    growth_rate: float = 0
    profit_margin: float = 0

class SalesMetrics(BaseModel):
    """Sales metrics model"""
    total_sales: float = 0
    sales_count: int = 0
    average_sale_value: float = 0
    top_selling_periods: List[Dict] = Field(default_factory=list)
    sales_trend: List[Dict] = Field(default_factory=list)
    conversion_rate: float = 0
    recurring_revenue: float = 0

class CustomerMetrics(BaseModel):
    """Customer metrics model"""
    total_customers: int = 0
    active_customers: int = 0
    new_customers: int = 0
    customer_retention_rate: float = 0
    average_customer_value: float = 0
    top_customers: List[Dict] = Field(default_factory=list)
    customer_segments: List[Dict] = Field(default_factory=list)
    churn_rate: float = 0

class BusinessOverview(BaseModel):
    """Business overview model"""
    financial_metrics: FinancialMetrics = Field(default_factory=FinancialMetrics)
    sales_metrics: SalesMetrics = Field(default_factory=SalesMetrics)
    customer_metrics: CustomerMetrics = Field(default_factory=CustomerMetrics)
    key_insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    performance_indicators: Dict[str, Any] = Field(default_factory=dict)

class ReportData(BaseModel):
    """Report data model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    report_type: ReportType = Field(...)
    period: ReportPeriod = Field(...)
    start_date: date = Field(...)
    end_date: date = Field(...)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    charts: Optional[List[Dict]] = Field(default_factory=list)
    insights: Optional[List[str]] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True

class ChartData(BaseModel):
    """Chart data model"""
    chart_type: str = Field(..., min_length=1)  # line, bar, pie, area, etc.
    title: str = Field(..., min_length=1)
    data: List[Dict] = Field(..., min_items=1)
    x_axis: str = Field(..., min_length=1)
    y_axis: str = Field(..., min_length=1)
    colors: Optional[List[str]] = Field(default_factory=list)
    description: Optional[str] = None

class DashboardWidget(BaseModel):
    """Dashboard widget model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    widget_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    data: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, int] = Field(default_factory=dict)  # x, y, width, height
    refresh_interval: int = Field(default=300)  # seconds
    is_visible: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ReportSchedule(BaseModel):
    """Report schedule model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    report_type: ReportType = Field(...)
    period: ReportPeriod = Field(...)
    schedule_type: str = Field(..., min_length=1)  # daily, weekly, monthly
    recipients: List[str] = Field(..., min_items=1)
    format: ReportFormat = Field(default=ReportFormat.PDF)
    is_active: bool = Field(default=True)
    last_sent: Optional[datetime] = None
    next_send: datetime = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReportExport(BaseModel):
    """Report export model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    report_id: str = Field(..., min_length=1)
    format: ReportFormat = Field(...)
    file_path: str = Field(..., min_length=1)
    file_size: int = Field(..., gt=0)
    exported_at: datetime = Field(default_factory=datetime.utcnow)
    download_count: int = Field(default=0)
    expires_at: Optional[datetime] = None

class KPIMetric(BaseModel):
    """KPI metric model"""
    name: str = Field(..., min_length=1)
    value: float = Field(...)
    unit: str = Field(..., min_length=1)
    change: float = Field(default=0)
    change_type: str = Field(default="neutral")  # positive, negative, neutral
    description: str = Field(..., min_length=1)
    target: Optional[float] = None
    is_good: bool = Field(default=True)

class Benchmark(BaseModel):
    """Benchmark model"""
    metric_name: str = Field(..., min_length=1)
    industry_average: float = Field(...)
    user_value: float = Field(...)
    percentile: float = Field(...)
    status: str = Field(..., min_length=1)  # above, below, average
    recommendation: str = Field(..., min_length=1)