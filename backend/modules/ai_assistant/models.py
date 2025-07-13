"""
AI Assistant models for the MSME SaaS platform
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from utils.helpers import generate_uuid

class QueryType(str, Enum):
    """AI Query type enumeration"""
    BUSINESS_INSIGHTS = "business_insights"
    INVOICE_QUERY = "invoice_query"
    CUSTOMER_QUERY = "customer_query"
    FINANCIAL_ANALYSIS = "financial_analysis"
    PREDICTION = "prediction"
    GENERAL = "general"

class AIQuery(BaseModel):
    """AI Query model"""
    query: str = Field(..., min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    query_type: Optional[QueryType] = Field(default=QueryType.GENERAL)

class AIResponse(BaseModel):
    """AI Response model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)
    query_type: QueryType = Field(default=QueryType.GENERAL)
    context_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    processing_time: Optional[float] = Field(None, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_helpful: Optional[bool] = None
    
    class Config:
        from_attributes = True

class AIInsight(BaseModel):
    """AI Business Insight model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    insight_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    data: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="medium")  # low, medium, high
    action_required: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False)
    
    class Config:
        from_attributes = True

class AIRecommendation(BaseModel):
    """AI Recommendation model"""
    id: str = Field(default_factory=generate_uuid)
    user_id: str = Field(..., min_length=1)
    recommendation_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    impact_score: float = Field(..., ge=0, le=10)
    implementation_difficulty: str = Field(default="medium")  # easy, medium, hard
    expected_outcome: str = Field(..., min_length=1, max_length=500)
    action_items: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_implemented: bool = Field(default=False)
    
    class Config:
        from_attributes = True

class BusinessContext(BaseModel):
    """Business context for AI queries"""
    total_customers: int = 0
    total_invoices: int = 0
    total_revenue: float = 0
    pending_payments: float = 0
    overdue_amount: float = 0
    top_customers: List[Dict] = Field(default_factory=list)
    recent_trends: Dict[str, Any] = Field(default_factory=dict)
    business_metrics: Dict[str, Any] = Field(default_factory=dict)

class AIAnalytics(BaseModel):
    """AI Analytics model"""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    average_response_time: float = 0
    popular_query_types: List[Dict] = Field(default_factory=list)
    user_satisfaction: float = 0
    insights_generated: int = 0
    recommendations_created: int = 0

class QueryFeedback(BaseModel):
    """Query feedback model"""
    response_id: str = Field(..., min_length=1)
    is_helpful: bool = Field(...)
    feedback_text: Optional[str] = Field(None, max_length=500)
    rating: Optional[int] = Field(None, ge=1, le=5)

class AIPromptTemplate(BaseModel):
    """AI Prompt template model"""
    template_name: str = Field(..., min_length=1)
    template_content: str = Field(..., min_length=1)
    variables: List[str] = Field(default_factory=list)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)