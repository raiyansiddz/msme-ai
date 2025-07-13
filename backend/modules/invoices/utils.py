"""
Invoice utilities for the MSME SaaS platform
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from core.database import db_manager
from modules.invoices.models import InvoiceStatus, PaymentStatus, InvoiceResponse
import logging

logger = logging.getLogger(__name__)

class InvoiceUtils:
    """Utility functions for invoice operations"""
    
    @staticmethod
    async def update_invoice_status(invoice_id: str, user_id: str) -> bool:
        """Update invoice status based on current date and payment status"""
        try:
            invoice = await db_manager.db.invoices.find_one({
                "id": invoice_id,
                "user_id": user_id
            })
            
            if not invoice:
                return False
            
            current_date = date.today()
            due_date = invoice.get("due_date")
            payment_status = invoice.get("payment_status")
            current_status = invoice.get("status")
            
            # Convert due_date string to date object if necessary
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
            
            new_status = current_status
            
            # Update status based on payment and due date
            if payment_status == PaymentStatus.PAID:
                new_status = InvoiceStatus.PAID
            elif current_date > due_date and payment_status != PaymentStatus.PAID:
                new_status = InvoiceStatus.OVERDUE
            elif current_status == InvoiceStatus.DRAFT and payment_status == PaymentStatus.PENDING:
                new_status = InvoiceStatus.SENT
            
            if new_status != current_status:
                await db_manager.db.invoices.update_one(
                    {"id": invoice_id, "user_id": user_id},
                    {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
                )
                logger.info(f"Invoice {invoice_id} status updated to {new_status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating invoice status: {e}")
            return False
    
    @staticmethod
    async def get_overdue_invoices(user_id: str) -> List[Dict]:
        """Get all overdue invoices for a user"""
        try:
            current_date = date.today()
            
            # Find invoices that are overdue
            overdue_invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "due_date": {"$lt": current_date.isoformat()},
                "payment_status": {"$ne": PaymentStatus.PAID}
            }).to_list(None)
            
            return overdue_invoices
            
        except Exception as e:
            logger.error(f"Error getting overdue invoices: {e}")
            return []
    
    @staticmethod
    async def calculate_invoice_summary(user_id: str, period: Optional[str] = None) -> Dict:
        """Calculate invoice summary for a user"""
        try:
            # Base query
            query = {"user_id": user_id}
            
            # Add date filter if period is specified
            if period:
                start_date, end_date = InvoiceUtils._get_period_dates(period)
                query["created_at"] = {
                    "$gte": start_date,
                    "$lte": end_date
                }
            
            # Get all invoices
            invoices = await db_manager.db.invoices.find(query).to_list(None)
            
            summary = {
                "total_invoices": len(invoices),
                "total_amount": 0,
                "paid_amount": 0,
                "pending_amount": 0,
                "overdue_amount": 0,
                "draft_count": 0,
                "sent_count": 0,
                "paid_count": 0,
                "overdue_count": 0
            }
            
            for invoice in invoices:
                total_amount = invoice.get("total_amount", 0)
                status = invoice.get("status")
                payment_status = invoice.get("payment_status")
                
                summary["total_amount"] += total_amount
                
                if payment_status == PaymentStatus.PAID:
                    summary["paid_amount"] += total_amount
                    summary["paid_count"] += 1
                elif status == InvoiceStatus.OVERDUE:
                    summary["overdue_amount"] += total_amount
                    summary["overdue_count"] += 1
                else:
                    summary["pending_amount"] += total_amount
                
                # Status counts
                if status == InvoiceStatus.DRAFT:
                    summary["draft_count"] += 1
                elif status == InvoiceStatus.SENT:
                    summary["sent_count"] += 1
            
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating invoice summary: {e}")
            return {}
    
    @staticmethod
    def _get_period_dates(period: str) -> tuple:
        """Get start and end dates for a period"""
        today = datetime.now()
        
        if period == "today":
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == "week":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == "month":
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        elif period == "quarter":
            quarter = (today.month - 1) // 3 + 1
            start_date = today.replace(month=3 * quarter - 2, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = today.replace(month=3 * quarter, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(day=28) + timedelta(days=4)
            end_date = end_date - timedelta(days=end_date.day)
        elif period == "year":
            start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            # Default to last 30 days
            start_date = today - timedelta(days=30)
            end_date = today
        
        return start_date, end_date
    
    @staticmethod
    async def populate_customer_info(invoices: List[Dict]) -> List[Dict]:
        """Populate customer information in invoices"""
        try:
            # Get unique customer IDs
            customer_ids = list(set(invoice.get("customer_id") for invoice in invoices if invoice.get("customer_id")))
            
            # Get customer data
            customers = await db_manager.db.customers.find({
                "id": {"$in": customer_ids}
            }).to_list(None)
            
            # Create customer lookup
            customer_lookup = {customer["id"]: customer for customer in customers}
            
            # Populate customer info in invoices
            for invoice in invoices:
                customer_id = invoice.get("customer_id")
                if customer_id and customer_id in customer_lookup:
                    customer = customer_lookup[customer_id]
                    invoice["customer_name"] = customer.get("name", "")
                    invoice["customer_email"] = customer.get("email", "")
                    invoice["customer_phone"] = customer.get("phone", "")
                    invoice["customer_address"] = customer.get("address", "")
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error populating customer info: {e}")
            return invoices
    
    @staticmethod
    async def get_invoice_stats(user_id: str, period: str = "month") -> Dict:
        """Get invoice statistics for a period"""
        try:
            start_date, end_date = InvoiceUtils._get_period_dates(period)
            
            # Get invoices for the period
            invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }).to_list(None)
            
            if not invoices:
                return {
                    "period": period,
                    "total_invoices": 0,
                    "total_revenue": 0,
                    "average_invoice_value": 0,
                    "payment_rate": 0,
                    "top_customers": [],
                    "monthly_trends": []
                }
            
            # Calculate stats
            total_invoices = len(invoices)
            total_revenue = sum(invoice.get("total_amount", 0) for invoice in invoices if invoice.get("payment_status") == PaymentStatus.PAID)
            paid_invoices = [invoice for invoice in invoices if invoice.get("payment_status") == PaymentStatus.PAID]
            payment_rate = (len(paid_invoices) / total_invoices) * 100 if total_invoices > 0 else 0
            
            # Average invoice value
            total_amount = sum(invoice.get("total_amount", 0) for invoice in invoices)
            average_invoice_value = total_amount / total_invoices if total_invoices > 0 else 0
            
            # Top customers (by total invoice value)
            customer_totals = {}
            for invoice in invoices:
                customer_id = invoice.get("customer_id")
                if customer_id:
                    customer_totals[customer_id] = customer_totals.get(customer_id, 0) + invoice.get("total_amount", 0)
            
            top_customers = sorted(customer_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "period": period,
                "total_invoices": total_invoices,
                "total_revenue": total_revenue,
                "average_invoice_value": average_invoice_value,
                "payment_rate": payment_rate,
                "top_customers": top_customers,
                "monthly_trends": []  # TODO: Implement monthly trends
            }
            
        except Exception as e:
            logger.error(f"Error getting invoice stats: {e}")
            return {}

# Global invoice utils instance
invoice_utils = InvoiceUtils()