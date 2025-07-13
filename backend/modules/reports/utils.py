"""
Reports utilities for the MSME SaaS platform
"""
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any, Tuple
import json
from core.database import db_manager
from modules.reports.models import (
    ReportPeriod, FinancialMetrics, SalesMetrics, CustomerMetrics,
    BusinessOverview, ChartData, KPIMetric
)
from utils.helpers import get_date_range
import logging

logger = logging.getLogger(__name__)

class ReportsUtils:
    """Utility functions for reports and analytics"""
    
    @staticmethod
    async def get_financial_metrics(user_id: str, start_date: date, end_date: date) -> FinancialMetrics:
        """Calculate financial metrics for a period"""
        try:
            # Get invoices for the period
            invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "created_at": {
                    "$gte": datetime.combine(start_date, datetime.min.time()),
                    "$lte": datetime.combine(end_date, datetime.max.time())
                }
            }).to_list(None)
            
            if not invoices:
                return FinancialMetrics()
            
            # Calculate metrics
            total_invoices = len(invoices)
            paid_invoices = len([inv for inv in invoices if inv.get("payment_status") == "paid"])
            pending_invoices = len([inv for inv in invoices if inv.get("payment_status") == "pending"])
            overdue_invoices = len([inv for inv in invoices if inv.get("status") == "overdue"])
            
            total_revenue = sum(inv.get("total_amount", 0) for inv in invoices if inv.get("payment_status") == "paid")
            total_outstanding = sum(inv.get("total_amount", 0) for inv in invoices if inv.get("payment_status") != "paid")
            
            average_invoice_value = total_revenue / paid_invoices if paid_invoices > 0 else 0
            collection_rate = (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
            
            # Calculate growth rate (compared to previous period)
            growth_rate = await ReportsUtils._calculate_growth_rate(user_id, start_date, end_date, "revenue")
            
            return FinancialMetrics(
                total_revenue=total_revenue,
                total_invoices=total_invoices,
                paid_invoices=paid_invoices,
                pending_invoices=pending_invoices,
                overdue_invoices=overdue_invoices,
                average_invoice_value=average_invoice_value,
                total_outstanding=total_outstanding,
                collection_rate=collection_rate,
                growth_rate=growth_rate,
                profit_margin=85.0  # Assuming 85% profit margin for services
            )
            
        except Exception as e:
            logger.error(f"Error calculating financial metrics: {e}")
            return FinancialMetrics()
    
    @staticmethod
    async def get_sales_metrics(user_id: str, start_date: date, end_date: date) -> SalesMetrics:
        """Calculate sales metrics for a period"""
        try:
            # Get paid invoices (sales)
            sales = await db_manager.db.invoices.find({
                "user_id": user_id,
                "payment_status": "paid",
                "created_at": {
                    "$gte": datetime.combine(start_date, datetime.min.time()),
                    "$lte": datetime.combine(end_date, datetime.max.time())
                }
            }).to_list(None)
            
            if not sales:
                return SalesMetrics()
            
            total_sales = sum(sale.get("total_amount", 0) for sale in sales)
            sales_count = len(sales)
            average_sale_value = total_sales / sales_count if sales_count > 0 else 0
            
            # Calculate sales trend
            sales_trend = await ReportsUtils._calculate_sales_trend(user_id, start_date, end_date)
            
            # Calculate top selling periods
            top_selling_periods = await ReportsUtils._calculate_top_selling_periods(sales)
            
            return SalesMetrics(
                total_sales=total_sales,
                sales_count=sales_count,
                average_sale_value=average_sale_value,
                top_selling_periods=top_selling_periods,
                sales_trend=sales_trend,
                conversion_rate=75.0,  # Assuming 75% conversion rate
                recurring_revenue=total_sales * 0.6  # Assuming 60% recurring revenue
            )
            
        except Exception as e:
            logger.error(f"Error calculating sales metrics: {e}")
            return SalesMetrics()
    
    @staticmethod
    async def get_customer_metrics(user_id: str, start_date: date, end_date: date) -> CustomerMetrics:
        """Calculate customer metrics for a period"""
        try:
            # Get all customers
            all_customers = await db_manager.db.customers.find({"user_id": user_id}).to_list(None)
            
            # Get new customers in period
            new_customers = await db_manager.db.customers.find({
                "user_id": user_id,
                "created_at": {
                    "$gte": datetime.combine(start_date, datetime.min.time()),
                    "$lte": datetime.combine(end_date, datetime.max.time())
                }
            }).to_list(None)
            
            total_customers = len(all_customers)
            new_customers_count = len(new_customers)
            
            # Calculate customer values
            invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "payment_status": "paid"
            }).to_list(None)
            
            customer_values = {}
            for invoice in invoices:
                customer_id = invoice.get("customer_id")
                if customer_id:
                    customer_values[customer_id] = customer_values.get(customer_id, 0) + invoice.get("total_amount", 0)
            
            # Calculate top customers
            top_customers = []
            for customer_id, value in sorted(customer_values.items(), key=lambda x: x[1], reverse=True)[:5]:
                customer = next((c for c in all_customers if c.get("id") == customer_id), None)
                if customer:
                    top_customers.append({
                        "id": customer_id,
                        "name": customer.get("name", "Unknown"),
                        "value": value
                    })
            
            total_customer_value = sum(customer_values.values())
            average_customer_value = total_customer_value / total_customers if total_customers > 0 else 0
            
            # Active customers (those with invoices in the period)
            active_customer_ids = set()
            period_invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "created_at": {
                    "$gte": datetime.combine(start_date, datetime.min.time()),
                    "$lte": datetime.combine(end_date, datetime.max.time())
                }
            }).to_list(None)
            
            for invoice in period_invoices:
                customer_id = invoice.get("customer_id")
                if customer_id:
                    active_customer_ids.add(customer_id)
            
            active_customers = len(active_customer_ids)
            
            return CustomerMetrics(
                total_customers=total_customers,
                active_customers=active_customers,
                new_customers=new_customers_count,
                customer_retention_rate=90.0,  # Assuming 90% retention rate
                average_customer_value=average_customer_value,
                top_customers=top_customers,
                customer_segments=[],  # TODO: Implement customer segmentation
                churn_rate=5.0  # Assuming 5% churn rate
            )
            
        except Exception as e:
            logger.error(f"Error calculating customer metrics: {e}")
            return CustomerMetrics()
    
    @staticmethod
    async def generate_business_overview(user_id: str, start_date: date, end_date: date) -> BusinessOverview:
        """Generate comprehensive business overview"""
        try:
            # Get all metrics
            financial_metrics = await ReportsUtils.get_financial_metrics(user_id, start_date, end_date)
            sales_metrics = await ReportsUtils.get_sales_metrics(user_id, start_date, end_date)
            customer_metrics = await ReportsUtils.get_customer_metrics(user_id, start_date, end_date)
            
            # Generate key insights
            key_insights = []
            
            if financial_metrics.growth_rate > 10:
                key_insights.append(f"Revenue grew by {financial_metrics.growth_rate:.1f}% - excellent growth!")
            elif financial_metrics.growth_rate < -5:
                key_insights.append(f"Revenue declined by {abs(financial_metrics.growth_rate):.1f}% - needs attention")
            
            if financial_metrics.collection_rate > 80:
                key_insights.append(f"Collection rate is healthy at {financial_metrics.collection_rate:.1f}%")
            elif financial_metrics.collection_rate < 60:
                key_insights.append(f"Collection rate is low at {financial_metrics.collection_rate:.1f}% - improve payment collection")
            
            if customer_metrics.new_customers > 0:
                key_insights.append(f"Acquired {customer_metrics.new_customers} new customers this period")
            
            # Generate recommendations
            recommendations = []
            
            if financial_metrics.overdue_invoices > 0:
                recommendations.append("Set up automated payment reminders to reduce overdue invoices")
            
            if financial_metrics.average_invoice_value > 0:
                recommendations.append("Consider upselling to increase average invoice value")
            
            if customer_metrics.total_customers > 5:
                recommendations.append("Implement customer loyalty programs to increase retention")
            
            # Performance indicators
            performance_indicators = {
                "revenue_health": "good" if financial_metrics.growth_rate > 0 else "needs_attention",
                "customer_growth": "good" if customer_metrics.new_customers > 0 else "stable",
                "cash_flow": "good" if financial_metrics.collection_rate > 70 else "needs_attention",
                "business_efficiency": "good" if financial_metrics.average_invoice_value > 1000 else "average"
            }
            
            return BusinessOverview(
                financial_metrics=financial_metrics,
                sales_metrics=sales_metrics,
                customer_metrics=customer_metrics,
                key_insights=key_insights,
                recommendations=recommendations,
                performance_indicators=performance_indicators
            )
            
        except Exception as e:
            logger.error(f"Error generating business overview: {e}")
            return BusinessOverview()
    
    @staticmethod
    async def _calculate_growth_rate(user_id: str, start_date: date, end_date: date, metric_type: str) -> float:
        """Calculate growth rate compared to previous period"""
        try:
            # Calculate period length
            period_days = (end_date - start_date).days
            
            # Get previous period
            prev_end_date = start_date - timedelta(days=1)
            prev_start_date = prev_end_date - timedelta(days=period_days)
            
            # Get current period data
            current_invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "payment_status": "paid",
                "created_at": {
                    "$gte": datetime.combine(start_date, datetime.min.time()),
                    "$lte": datetime.combine(end_date, datetime.max.time())
                }
            }).to_list(None)
            
            # Get previous period data
            prev_invoices = await db_manager.db.invoices.find({
                "user_id": user_id,
                "payment_status": "paid",
                "created_at": {
                    "$gte": datetime.combine(prev_start_date, datetime.min.time()),
                    "$lte": datetime.combine(prev_end_date, datetime.max.time())
                }
            }).to_list(None)
            
            current_value = sum(inv.get("total_amount", 0) for inv in current_invoices)
            prev_value = sum(inv.get("total_amount", 0) for inv in prev_invoices)
            
            if prev_value == 0:
                return 100.0 if current_value > 0 else 0.0
            
            return ((current_value - prev_value) / prev_value) * 100
            
        except Exception as e:
            logger.error(f"Error calculating growth rate: {e}")
            return 0.0
    
    @staticmethod
    async def _calculate_sales_trend(user_id: str, start_date: date, end_date: date) -> List[Dict]:
        """Calculate sales trend data"""
        try:
            # Get daily sales data
            sales_trend = []
            current_date = start_date
            
            while current_date <= end_date:
                daily_sales = await db_manager.db.invoices.find({
                    "user_id": user_id,
                    "payment_status": "paid",
                    "created_at": {
                        "$gte": datetime.combine(current_date, datetime.min.time()),
                        "$lte": datetime.combine(current_date, datetime.max.time())
                    }
                }).to_list(None)
                
                daily_total = sum(sale.get("total_amount", 0) for sale in daily_sales)
                
                sales_trend.append({
                    "date": current_date.isoformat(),
                    "sales": daily_total,
                    "count": len(daily_sales)
                })
                
                current_date += timedelta(days=1)
            
            return sales_trend
            
        except Exception as e:
            logger.error(f"Error calculating sales trend: {e}")
            return []
    
    @staticmethod
    async def _calculate_top_selling_periods(sales: List[Dict]) -> List[Dict]:
        """Calculate top selling periods"""
        try:
            # Group by day of week
            day_sales = {}
            for sale in sales:
                created_at = sale.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)
                    day_name = created_at.strftime("%A")
                    day_sales[day_name] = day_sales.get(day_name, 0) + sale.get("total_amount", 0)
            
            # Sort by sales amount
            top_periods = [
                {"period": day, "sales": amount}
                for day, amount in sorted(day_sales.items(), key=lambda x: x[1], reverse=True)
            ]
            
            return top_periods[:3]  # Top 3 days
            
        except Exception as e:
            logger.error(f"Error calculating top selling periods: {e}")
            return []
    
    @staticmethod
    async def generate_chart_data(user_id: str, chart_type: str, start_date: date, end_date: date) -> List[ChartData]:
        """Generate chart data for reports"""
        try:
            charts = []
            
            if chart_type == "revenue_trend":
                # Revenue trend chart
                trend_data = await ReportsUtils._calculate_sales_trend(user_id, start_date, end_date)
                charts.append(ChartData(
                    chart_type="line",
                    title="Revenue Trend",
                    data=trend_data,
                    x_axis="date",
                    y_axis="sales",
                    colors=["#3B82F6"],
                    description="Daily revenue trend over the selected period"
                ))
            
            elif chart_type == "invoice_status":
                # Invoice status pie chart
                invoices = await db_manager.db.invoices.find({
                    "user_id": user_id,
                    "created_at": {
                        "$gte": datetime.combine(start_date, datetime.min.time()),
                        "$lte": datetime.combine(end_date, datetime.max.time())
                    }
                }).to_list(None)
                
                status_counts = {}
                for invoice in invoices:
                    status = invoice.get("payment_status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                chart_data = [
                    {"status": status, "count": count}
                    for status, count in status_counts.items()
                ]
                
                charts.append(ChartData(
                    chart_type="pie",
                    title="Invoice Status Distribution",
                    data=chart_data,
                    x_axis="status",
                    y_axis="count",
                    colors=["#10B981", "#F59E0B", "#EF4444"],
                    description="Distribution of invoice statuses"
                ))
            
            elif chart_type == "top_customers":
                # Top customers bar chart
                customer_metrics = await ReportsUtils.get_customer_metrics(user_id, start_date, end_date)
                
                charts.append(ChartData(
                    chart_type="bar",
                    title="Top Customers by Revenue",
                    data=customer_metrics.top_customers,
                    x_axis="name",
                    y_axis="value",
                    colors=["#8B5CF6"],
                    description="Top customers ranked by total revenue"
                ))
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating chart data: {e}")
            return []
    
    @staticmethod
    async def get_kpi_metrics(user_id: str, start_date: date, end_date: date) -> List[KPIMetric]:
        """Get KPI metrics for dashboard"""
        try:
            financial_metrics = await ReportsUtils.get_financial_metrics(user_id, start_date, end_date)
            customer_metrics = await ReportsUtils.get_customer_metrics(user_id, start_date, end_date)
            
            kpis = [
                KPIMetric(
                    name="Total Revenue",
                    value=financial_metrics.total_revenue,
                    unit="₹",
                    change=financial_metrics.growth_rate,
                    change_type="positive" if financial_metrics.growth_rate > 0 else "negative",
                    description="Total revenue for the period",
                    target=financial_metrics.total_revenue * 1.2,
                    is_good=financial_metrics.growth_rate > 0
                ),
                KPIMetric(
                    name="Collection Rate",
                    value=financial_metrics.collection_rate,
                    unit="%",
                    change=0,  # TODO: Calculate change
                    change_type="neutral",
                    description="Percentage of invoices paid on time",
                    target=85.0,
                    is_good=financial_metrics.collection_rate > 75
                ),
                KPIMetric(
                    name="Average Invoice Value",
                    value=financial_metrics.average_invoice_value,
                    unit="₹",
                    change=0,  # TODO: Calculate change
                    change_type="neutral",
                    description="Average value per invoice",
                    target=financial_metrics.average_invoice_value * 1.15,
                    is_good=financial_metrics.average_invoice_value > 1000
                ),
                KPIMetric(
                    name="New Customers",
                    value=customer_metrics.new_customers,
                    unit="",
                    change=0,  # TODO: Calculate change
                    change_type="neutral",
                    description="New customers acquired this period",
                    target=customer_metrics.new_customers * 1.25,
                    is_good=customer_metrics.new_customers > 0
                )
            ]
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error getting KPI metrics: {e}")
            return []

# Global reports utils instance
reports_utils = ReportsUtils()