"""
AI Assistant utilities for the MSME SaaS platform
"""
import google.generativeai as genai
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import logging
from core.database import db_manager
from core.config import get_settings
from modules.ai_assistant.models import BusinessContext, QueryType

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Gemini AI
genai.configure(api_key=settings.gemini_api_key)

class AIAssistant:
    """Advanced AI Assistant for MSME business intelligence"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.business_context_cache = {}
        self.cache_expiry = 300  # 5 minutes
        
    async def get_business_context(self, user_id: str) -> BusinessContext:
        """Get comprehensive business context for AI queries"""
        try:
            # Check cache first
            cache_key = f"business_context_{user_id}"
            current_time = datetime.utcnow()
            
            if (cache_key in self.business_context_cache and 
                current_time - self.business_context_cache[cache_key]['timestamp'] < timedelta(seconds=self.cache_expiry)):
                return self.business_context_cache[cache_key]['data']
            
            # Get business data
            customers = await db_manager.db.customers.find({"user_id": user_id}).to_list(None)
            invoices = await db_manager.db.invoices.find({"user_id": user_id}).to_list(None)
            
            # Calculate metrics
            total_customers = len(customers)
            total_invoices = len(invoices)
            total_revenue = sum(invoice.get("total_amount", 0) for invoice in invoices if invoice.get("payment_status") == "paid")
            pending_payments = sum(invoice.get("total_amount", 0) for invoice in invoices if invoice.get("payment_status") == "pending")
            overdue_amount = sum(invoice.get("total_amount", 0) for invoice in invoices if invoice.get("status") == "overdue")
            
            # Get top customers
            customer_revenue = {}
            for invoice in invoices:
                if invoice.get("payment_status") == "paid":
                    customer_id = invoice.get("customer_id")
                    if customer_id:
                        customer_revenue[customer_id] = customer_revenue.get(customer_id, 0) + invoice.get("total_amount", 0)
            
            top_customers = []
            for customer_id, revenue in sorted(customer_revenue.items(), key=lambda x: x[1], reverse=True)[:5]:
                customer = next((c for c in customers if c.get("id") == customer_id), None)
                if customer:
                    top_customers.append({
                        "id": customer_id,
                        "name": customer.get("name", "Unknown"),
                        "revenue": revenue
                    })
            
            # Calculate trends
            recent_trends = await self._calculate_trends(user_id)
            
            # Business metrics
            business_metrics = {
                "average_invoice_value": total_revenue / total_invoices if total_invoices > 0 else 0,
                "payment_rate": (len([i for i in invoices if i.get("payment_status") == "paid"]) / total_invoices * 100) if total_invoices > 0 else 0,
                "customer_growth": await self._calculate_customer_growth(user_id),
                "revenue_growth": await self._calculate_revenue_growth(user_id)
            }
            
            context = BusinessContext(
                total_customers=total_customers,
                total_invoices=total_invoices,
                total_revenue=total_revenue,
                pending_payments=pending_payments,
                overdue_amount=overdue_amount,
                top_customers=top_customers,
                recent_trends=recent_trends,
                business_metrics=business_metrics
            )
            
            # Cache the result
            self.business_context_cache[cache_key] = {
                'data': context,
                'timestamp': current_time
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting business context: {e}")
            return BusinessContext()
    
    async def _calculate_trends(self, user_id: str) -> Dict[str, Any]:
        """Calculate business trends"""
        try:
            # Get last 30 days data
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            recent_invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "created_at": {"$gte": thirty_days_ago}
            }).to_list(None)
            
            recent_customers = await db_manager.db.customers.find({
                "user_id": user_id,
                "created_at": {"$gte": thirty_days_ago}
            }).to_list(None)
            
            return {
                "recent_invoices_count": len(recent_invoices),
                "recent_customers_count": len(recent_customers),
                "recent_revenue": sum(invoice.get("total_amount", 0) for invoice in recent_invoices if invoice.get("payment_status") == "paid")
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {}
    
    async def _calculate_customer_growth(self, user_id: str) -> float:
        """Calculate customer growth rate"""
        try:
            # Get current month customers
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_month_customers = await db_manager.db.customers.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": current_month}
            })
            
            # Get previous month customers
            previous_month = current_month - timedelta(days=32)
            previous_month_start = previous_month.replace(day=1)
            previous_month_customers = await db_manager.db.customers.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": previous_month_start, "$lt": current_month}
            })
            
            if previous_month_customers == 0:
                return 100.0 if current_month_customers > 0 else 0.0
            
            return ((current_month_customers - previous_month_customers) / previous_month_customers) * 100
            
        except Exception as e:
            logger.error(f"Error calculating customer growth: {e}")
            return 0.0
    
    async def _calculate_revenue_growth(self, user_id: str) -> float:
        """Calculate revenue growth rate"""
        try:
            # Get current month revenue
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_month_invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "created_at": {"$gte": current_month},
                "payment_status": "paid"
            }).to_list(None)
            
            current_month_revenue = sum(invoice.get("total_amount", 0) for invoice in current_month_invoices)
            
            # Get previous month revenue
            previous_month = current_month - timedelta(days=32)
            previous_month_start = previous_month.replace(day=1)
            previous_month_invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "created_at": {"$gte": previous_month_start, "$lt": current_month},
                "payment_status": "paid"
            }).to_list(None)
            
            previous_month_revenue = sum(invoice.get("total_amount", 0) for invoice in previous_month_invoices)
            
            if previous_month_revenue == 0:
                return 100.0 if current_month_revenue > 0 else 0.0
            
            return ((current_month_revenue - previous_month_revenue) / previous_month_revenue) * 100
            
        except Exception as e:
            logger.error(f"Error calculating revenue growth: {e}")
            return 0.0
    
    async def process_query(self, query: str, user_id: str, query_type: QueryType = QueryType.GENERAL) -> Tuple[str, Dict[str, Any]]:
        """Process AI query with business context"""
        try:
            start_time = datetime.utcnow()
            
            # Get business context
            context = await self.get_business_context(user_id)
            
            # Generate AI prompt based on query type
            prompt = await self._generate_prompt(query, context, query_type)
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract context data used
            context_data = {
                "total_customers": context.total_customers,
                "total_invoices": context.total_invoices,
                "total_revenue": context.total_revenue,
                "query_type": query_type,
                "processing_time": processing_time
            }
            
            return response.text, context_data
            
        except Exception as e:
            logger.error(f"Error processing AI query: {e}")
            return f"I apologize, but I encountered an error processing your query: {str(e)}", {}
    
    async def _generate_prompt(self, query: str, context: BusinessContext, query_type: QueryType) -> str:
        """Generate AI prompt based on query type and context"""
        
        base_context = f"""
        You are an AI business assistant for an MSME (Micro, Small, Medium Enterprise) SaaS platform.
        
        Current Business Context:
        - Total Customers: {context.total_customers}
        - Total Invoices: {context.total_invoices}
        - Total Revenue: ₹{context.total_revenue:,.2f}
        - Pending Payments: ₹{context.pending_payments:,.2f}
        - Overdue Amount: ₹{context.overdue_amount:,.2f}
        - Customer Growth: {context.business_metrics.get('customer_growth', 0):.1f}%
        - Revenue Growth: {context.business_metrics.get('revenue_growth', 0):.1f}%
        - Payment Rate: {context.business_metrics.get('payment_rate', 0):.1f}%
        
        Top Customers by Revenue:
        {json.dumps(context.top_customers, indent=2)}
        
        Recent Trends:
        {json.dumps(context.recent_trends, indent=2)}
        """
        
        if query_type == QueryType.BUSINESS_INSIGHTS:
            return f"""
            {base_context}
            
            You are providing business insights. Focus on:
            1. Key business metrics and what they mean
            2. Trends and patterns in the data
            3. Areas of concern or opportunity
            4. Actionable recommendations
            
            User Query: {query}
            
            Provide a comprehensive, insightful response in a professional yet friendly tone.
            """
            
        elif query_type == QueryType.FINANCIAL_ANALYSIS:
            return f"""
            {base_context}
            
            You are providing financial analysis. Focus on:
            1. Revenue analysis and cash flow
            2. Payment patterns and collection efficiency
            3. Profitability indicators
            4. Financial health assessment
            
            User Query: {query}
            
            Provide detailed financial insights with specific numbers and recommendations.
            """
            
        elif query_type == QueryType.CUSTOMER_QUERY:
            return f"""
            {base_context}
            
            You are answering customer-related questions. Focus on:
            1. Customer behavior and patterns
            2. Customer segmentation insights
            3. Relationship management recommendations
            4. Customer retention strategies
            
            User Query: {query}
            
            Provide customer-focused insights and actionable recommendations.
            """
            
        elif query_type == QueryType.INVOICE_QUERY:
            return f"""
            {base_context}
            
            You are answering invoice-related questions. Focus on:
            1. Invoice patterns and trends
            2. Payment collection insights
            3. Overdue invoice management
            4. Invoicing process optimization
            
            User Query: {query}
            
            Provide invoice-specific insights and recommendations.
            """
            
        else:
            return f"""
            {base_context}
            
            You are a helpful business assistant. Answer the user's question using the business context provided.
            Be specific, actionable, and professional in your response.
            
            User Query: {query}
            
            Provide a helpful and informative response.
            """
    
    async def generate_business_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate automated business insights"""
        try:
            context = await self.get_business_context(user_id)
            insights = []
            
            # Revenue insights
            if context.total_revenue > 0:
                if context.business_metrics.get('revenue_growth', 0) > 20:
                    insights.append({
                        "type": "revenue_growth",
                        "title": "Strong Revenue Growth",
                        "description": f"Your revenue has grown by {context.business_metrics.get('revenue_growth', 0):.1f}% this month!",
                        "priority": "high",
                        "action_required": False
                    })
                elif context.business_metrics.get('revenue_growth', 0) < -10:
                    insights.append({
                        "type": "revenue_decline",
                        "title": "Revenue Decline Alert",
                        "description": f"Your revenue has declined by {abs(context.business_metrics.get('revenue_growth', 0)):.1f}% this month. Consider reviewing your sales strategy.",
                        "priority": "high",
                        "action_required": True
                    })
            
            # Payment insights
            if context.overdue_amount > 0:
                overdue_percentage = (context.overdue_amount / context.total_revenue) * 100 if context.total_revenue > 0 else 0
                if overdue_percentage > 10:
                    insights.append({
                        "type": "overdue_payments",
                        "title": "High Overdue Payments",
                        "description": f"You have ₹{context.overdue_amount:,.2f} in overdue payments ({overdue_percentage:.1f}% of total revenue). Consider sending payment reminders.",
                        "priority": "high",
                        "action_required": True
                    })
            
            # Customer insights
            if context.business_metrics.get('customer_growth', 0) > 15:
                insights.append({
                    "type": "customer_growth",
                    "title": "Excellent Customer Growth",
                    "description": f"You've acquired {context.business_metrics.get('customer_growth', 0):.1f}% more customers this month!",
                    "priority": "medium",
                    "action_required": False
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating business insights: {e}")
            return []
    
    async def generate_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate AI-powered business recommendations"""
        try:
            context = await self.get_business_context(user_id)
            recommendations = []
            
            # Payment collection recommendations
            if context.overdue_amount > 0:
                recommendations.append({
                    "type": "payment_collection",
                    "title": "Improve Payment Collection",
                    "description": "Set up automated payment reminders to reduce overdue amounts and improve cash flow.",
                    "impact_score": 8.5,
                    "implementation_difficulty": "easy",
                    "expected_outcome": f"Could recover up to ₹{context.overdue_amount * 0.7:,.2f} in overdue payments",
                    "action_items": [
                        "Enable automated email reminders",
                        "Send WhatsApp payment notifications",
                        "Offer early payment discounts"
                    ]
                })
            
            # Customer retention recommendations
            if context.total_customers > 5:
                recommendations.append({
                    "type": "customer_retention",
                    "title": "Enhance Customer Relationships",
                    "description": "Focus on your top customers to increase repeat business and referrals.",
                    "impact_score": 7.5,
                    "implementation_difficulty": "medium",
                    "expected_outcome": "Increase customer lifetime value by 25-30%",
                    "action_items": [
                        "Create loyalty programs for top customers",
                        "Schedule regular check-ins",
                        "Offer personalized discounts"
                    ]
                })
            
            # Invoice optimization recommendations
            if context.total_invoices > 10:
                avg_invoice_value = context.business_metrics.get('average_invoice_value', 0)
                if avg_invoice_value > 0:
                    recommendations.append({
                        "type": "invoice_optimization",
                        "title": "Optimize Invoice Values",
                        "description": f"Your average invoice value is ₹{avg_invoice_value:,.2f}. Consider upselling to increase this.",
                        "impact_score": 6.5,
                        "implementation_difficulty": "medium",
                        "expected_outcome": f"Increase average invoice value by 15-20%",
                        "action_items": [
                            "Bundle complementary services",
                            "Offer premium service tiers",
                            "Implement minimum order values"
                        ]
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

# Global AI assistant instance
ai_assistant = AIAssistant()