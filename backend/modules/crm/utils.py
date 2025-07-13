"""
CRM utilities for the MSME SaaS platform
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from core.database import db_manager
from modules.crm.models import CustomerStatus, CustomerResponse
import logging

logger = logging.getLogger(__name__)

class CRMUtils:
    """Utility functions for CRM operations"""
    
    @staticmethod
    async def calculate_customer_stats(customer_id: str, user_id: str) -> Dict:
        """Calculate statistics for a specific customer"""
        try:
            # Get customer's invoices
            invoices = await db_manager.db.invoices.find({
                "customer_id": customer_id,
                "user_id": user_id
            }).to_list(None)
            
            stats = {
                "total_invoices": len(invoices),
                "total_revenue": 0,
                "outstanding_amount": 0,
                "paid_amount": 0,
                "last_invoice_date": None,
                "average_invoice_value": 0
            }
            
            if invoices:
                # Calculate totals
                total_amount = sum(invoice.get("total_amount", 0) for invoice in invoices)
                paid_amount = sum(
                    invoice.get("total_amount", 0) 
                    for invoice in invoices 
                    if invoice.get("payment_status") == "paid"
                )
                outstanding_amount = total_amount - paid_amount
                
                # Get last invoice date
                last_invoice = max(invoices, key=lambda x: x.get("created_at", datetime.min))
                last_invoice_date = last_invoice.get("created_at")
                
                stats.update({
                    "total_revenue": total_amount,
                    "paid_amount": paid_amount,
                    "outstanding_amount": outstanding_amount,
                    "last_invoice_date": last_invoice_date,
                    "average_invoice_value": total_amount / len(invoices) if invoices else 0
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating customer stats: {e}")
            return {}
    
    @staticmethod
    async def get_customer_summary(user_id: str) -> Dict:
        """Get customer summary for a user"""
        try:
            # Get all customers
            customers = await db_manager.db.customers.find({"user_id": user_id}).to_list(None)
            
            summary = {
                "total_customers": len(customers),
                "active_customers": 0,
                "inactive_customers": 0,
                "potential_customers": 0,
                "total_revenue": 0,
                "average_revenue_per_customer": 0,
                "top_customers": [],
                "customer_growth": []
            }
            
            # Count customers by status
            for customer in customers:
                status = customer.get("status", CustomerStatus.ACTIVE)
                if status == CustomerStatus.ACTIVE:
                    summary["active_customers"] += 1
                elif status == CustomerStatus.INACTIVE:
                    summary["inactive_customers"] += 1
                elif status == CustomerStatus.POTENTIAL:
                    summary["potential_customers"] += 1
            
            # Calculate revenue per customer
            invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "payment_status": "paid"
            }).to_list(None)
            
            if invoices:
                total_revenue = sum(invoice.get("total_amount", 0) for invoice in invoices)
                summary["total_revenue"] = total_revenue
                
                if customers:
                    summary["average_revenue_per_customer"] = total_revenue / len(customers)
                
                # Calculate top customers
                customer_revenue = {}
                for invoice in invoices:
                    customer_id = invoice.get("customer_id")
                    if customer_id:
                        customer_revenue[customer_id] = customer_revenue.get(customer_id, 0) + invoice.get("total_amount", 0)
                
                # Get top 5 customers
                top_customers = sorted(customer_revenue.items(), key=lambda x: x[1], reverse=True)[:5]
                
                # Populate customer names
                for customer_id, revenue in top_customers:
                    customer = next((c for c in customers if c.get("id") == customer_id), None)
                    if customer:
                        summary["top_customers"].append({
                            "id": customer_id,
                            "name": customer.get("name", "Unknown"),
                            "revenue": revenue
                        })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting customer summary: {e}")
            return {}
    
    @staticmethod
    async def populate_customer_stats(customers: List[Dict], user_id: str) -> List[Dict]:
        """Populate customer statistics"""
        try:
            # Get all invoices for efficiency
            invoices = await db_manager.db.invoices.find({"user_id": user_id}).to_list(None)
            
            # Group invoices by customer
            customer_invoices = {}
            for invoice in invoices:
                customer_id = invoice.get("customer_id")
                if customer_id:
                    if customer_id not in customer_invoices:
                        customer_invoices[customer_id] = []
                    customer_invoices[customer_id].append(invoice)
            
            # Calculate stats for each customer
            for customer in customers:
                customer_id = customer.get("id")
                customer_invoice_list = customer_invoices.get(customer_id, [])
                
                if customer_invoice_list:
                    total_amount = sum(invoice.get("total_amount", 0) for invoice in customer_invoice_list)
                    paid_amount = sum(
                        invoice.get("total_amount", 0) 
                        for invoice in customer_invoice_list 
                        if invoice.get("payment_status") == "paid"
                    )
                    outstanding_amount = total_amount - paid_amount
                    
                    customer["total_invoices"] = len(customer_invoice_list)
                    customer["total_revenue"] = total_amount
                    customer["outstanding_amount"] = outstanding_amount
                else:
                    customer["total_invoices"] = 0
                    customer["total_revenue"] = 0
                    customer["outstanding_amount"] = 0
            
            return customers
            
        except Exception as e:
            logger.error(f"Error populating customer stats: {e}")
            return customers
    
    @staticmethod
    async def get_customer_interactions(customer_id: str, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent interactions for a customer"""
        try:
            interactions = await db_manager.db.interactions.find({
                "customer_id": customer_id,
                "user_id": user_id
            }).sort("interaction_date", -1).limit(limit).to_list(None)
            
            return interactions
            
        except Exception as e:
            logger.error(f"Error getting customer interactions: {e}")
            return []
    
    @staticmethod
    async def update_customer_last_interaction(customer_id: str, user_id: str):
        """Update customer's last interaction timestamp"""
        try:
            await db_manager.db.customers.update_one(
                {"id": customer_id, "user_id": user_id},
                {"$set": {"last_interaction": datetime.utcnow()}}
            )
            
        except Exception as e:
            logger.error(f"Error updating customer last interaction: {e}")
    
    @staticmethod
    async def search_customers(user_id: str, query: str, limit: int = 10) -> List[Dict]:
        """Search customers by name, email, or company"""
        try:
            search_criteria = {
                "user_id": user_id,
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}},
                    {"company": {"$regex": query, "$options": "i"}},
                    {"phone": {"$regex": query, "$options": "i"}}
                ]
            }
            
            customers = await db_manager.db.customers.find(search_criteria).limit(limit).to_list(None)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error searching customers: {e}")
            return []
    
    @staticmethod
    async def get_customers_with_pending_follow_ups(user_id: str) -> List[Dict]:
        """Get customers with pending follow-ups"""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Find interactions with follow-up dates that are due
            interactions = await db_manager.db.interactions.find({
                "user_id": user_id,
                "follow_up_date": {"$lte": today},
                "completed": False
            }).to_list(None)
            
            # Get unique customer IDs
            customer_ids = list(set(interaction.get("customer_id") for interaction in interactions))
            
            # Get customer details
            customers = await db_manager.db.customers.find({
                "id": {"$in": customer_ids},
                "user_id": user_id
            }).to_list(None)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error getting customers with pending follow-ups: {e}")
            return []
    
    @staticmethod
    async def get_customer_growth_data(user_id: str, period: str = "month") -> List[Dict]:
        """Get customer growth data for a period"""
        try:
            # Calculate date range
            today = datetime.now()
            
            if period == "month":
                periods = []
                for i in range(12):  # Last 12 months
                    month_start = today.replace(day=1) - timedelta(days=30 * i)
                    month_end = month_start.replace(day=28) + timedelta(days=4)
                    month_end = month_end - timedelta(days=month_end.day)
                    periods.append({
                        "name": month_start.strftime("%Y-%m"),
                        "start": month_start,
                        "end": month_end
                    })
            else:
                # Default to weekly
                periods = []
                for i in range(12):  # Last 12 weeks
                    week_start = today - timedelta(weeks=i, days=today.weekday())
                    week_end = week_start + timedelta(days=6)
                    periods.append({
                        "name": f"Week {week_start.strftime('%Y-%m-%d')}",
                        "start": week_start,
                        "end": week_end
                    })
            
            growth_data = []
            for period_info in periods:
                count = await db_manager.db.customers.count_documents({
                    "user_id": user_id,
                    "created_at": {"$gte": period_info["start"], "$lte": period_info["end"]}
                })
                
                growth_data.append({
                    "period": period_info["name"],
                    "customers_added": count
                })
            
            return growth_data
            
        except Exception as e:
            logger.error(f"Error getting customer growth data: {e}")
            return []

# Global CRM utils instance
crm_utils = CRMUtils()