"""
Reports routes for the MSME SaaS platform
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime, date, timedelta
from core.database import db_manager
from modules.auth.utils import get_current_active_user
from modules.auth.models import UserResponse
from modules.reports.models import (
    ReportRequest, ReportType, ReportPeriod, ReportData, BusinessOverview
)
from modules.reports.utils import reports_utils
from utils.helpers import ResponseHelper, get_date_range, generate_uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Reports"])

@router.post("/generate", response_model=dict)
async def generate_report(
    report_request: ReportRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Generate a comprehensive report"""
    try:
        # Determine date range
        if report_request.period == ReportPeriod.CUSTOM:
            if not report_request.start_date or not report_request.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date and end date are required for custom period"
                )
            start_date = report_request.start_date
            end_date = report_request.end_date
        else:
            start_date, end_date = get_date_range(report_request.period)
            start_date = start_date.date()
            end_date = end_date.date()
        
        # Generate report data based on type
        report_data = {}
        charts = []
        insights = []
        
        if report_request.report_type == ReportType.FINANCIAL:
            financial_metrics = await reports_utils.get_financial_metrics(current_user.id, start_date, end_date)
            report_data = financial_metrics.dict()
            
            if report_request.include_charts:
                charts = await reports_utils.generate_chart_data(current_user.id, "revenue_trend", start_date, end_date)
            
            if report_request.include_insights:
                insights = [
                    f"Total revenue: ₹{financial_metrics.total_revenue:,.2f}",
                    f"Collection rate: {financial_metrics.collection_rate:.1f}%",
                    f"Growth rate: {financial_metrics.growth_rate:.1f}%"
                ]
        
        elif report_request.report_type == ReportType.SALES:
            sales_metrics = await reports_utils.get_sales_metrics(current_user.id, start_date, end_date)
            report_data = sales_metrics.dict()
            
            if report_request.include_charts:
                charts = await reports_utils.generate_chart_data(current_user.id, "revenue_trend", start_date, end_date)
            
            if report_request.include_insights:
                insights = [
                    f"Total sales: ₹{sales_metrics.total_sales:,.2f}",
                    f"Average sale value: ₹{sales_metrics.average_sale_value:,.2f}",
                    f"Sales count: {sales_metrics.sales_count}"
                ]
        
        elif report_request.report_type == ReportType.CUSTOMER:
            customer_metrics = await reports_utils.get_customer_metrics(current_user.id, start_date, end_date)
            report_data = customer_metrics.dict()
            
            if report_request.include_charts:
                charts = await reports_utils.generate_chart_data(current_user.id, "top_customers", start_date, end_date)
            
            if report_request.include_insights:
                insights = [
                    f"Total customers: {customer_metrics.total_customers}",
                    f"New customers: {customer_metrics.new_customers}",
                    f"Average customer value: ₹{customer_metrics.average_customer_value:,.2f}"
                ]
        
        elif report_request.report_type == ReportType.BUSINESS_OVERVIEW:
            business_overview = await reports_utils.generate_business_overview(current_user.id, start_date, end_date)
            report_data = business_overview.dict()
            
            if report_request.include_charts:
                charts.extend(await reports_utils.generate_chart_data(current_user.id, "revenue_trend", start_date, end_date))
                charts.extend(await reports_utils.generate_chart_data(current_user.id, "invoice_status", start_date, end_date))
                charts.extend(await reports_utils.generate_chart_data(current_user.id, "top_customers", start_date, end_date))
            
            if report_request.include_insights:
                insights = business_overview.key_insights
        
        # Create report record
        report = ReportData(
            user_id=current_user.id,
            report_type=report_request.report_type,
            period=report_request.period,
            start_date=start_date,
            end_date=end_date,
            data=report_data,
            charts=[chart.dict() for chart in charts],
            insights=insights,
            summary={
                "period": f"{start_date} to {end_date}",
                "generated_at": datetime.utcnow().isoformat(),
                "type": report_request.report_type
            }
        )
        
        # Save report to database
        await db_manager.db.reports.insert_one(report.dict())
        
        logger.info(f"Report generated: {report_request.report_type} for user {current_user.id}")
        
        return ResponseHelper.success(
            data={"report": report.dict()},
            message="Report generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report"
        )

@router.get("/dashboard", response_model=dict)
async def get_dashboard_data(
    period: str = Query("month"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get dashboard data with key metrics"""
    try:
        # Get date range
        start_date, end_date = get_date_range(period)
        start_date = start_date.date()
        end_date = end_date.date()
        
        # Get business overview
        business_overview = await reports_utils.generate_business_overview(current_user.id, start_date, end_date)
        
        # Get KPI metrics
        kpi_metrics = await reports_utils.get_kpi_metrics(current_user.id, start_date, end_date)
        
        # Get chart data
        charts = []
        charts.extend(await reports_utils.generate_chart_data(current_user.id, "revenue_trend", start_date, end_date))
        charts.extend(await reports_utils.generate_chart_data(current_user.id, "invoice_status", start_date, end_date))
        
        dashboard_data = {
            "overview": business_overview.dict(),
            "kpi_metrics": [kpi.dict() for kpi in kpi_metrics],
            "charts": [chart.dict() for chart in charts],
            "period": period,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        return ResponseHelper.success(
            data={"dashboard": dashboard_data},
            message="Dashboard data retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get dashboard data error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )

@router.get("/", response_model=dict)
async def get_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    report_type: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get user's reports with pagination"""
    try:
        # Build query
        query = {"user_id": current_user.id}
        if report_type:
            query["report_type"] = report_type
        
        # Get total count
        total_count = await db_manager.db.reports.count_documents(query)
        
        # Get reports
        reports = await db_manager.db.reports.find(query).sort("generated_at", -1).skip((page - 1) * page_size).limit(page_size).to_list(None)
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        pagination = {
            "page": page,
            "page_size": page_size,
            "total_items": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return ResponseHelper.paginated_success(
            data=[ReportData(**report).dict() for report in reports],
            pagination=pagination,
            message="Reports retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get reports error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reports"
        )

@router.get("/{report_id}", response_model=dict)
async def get_report(
    report_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get a specific report"""
    try:
        report = await db_manager.db.reports.find_one({
            "id": report_id,
            "user_id": current_user.id
        })
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        return ResponseHelper.success(
            data={"report": ReportData(**report).dict()},
            message="Report retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report"
        )

@router.delete("/{report_id}", response_model=dict)
async def delete_report(
    report_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Delete a report"""
    try:
        result = await db_manager.db.reports.delete_one({
            "id": report_id,
            "user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        logger.info(f"Report deleted: {report_id} by user {current_user.id}")
        
        return ResponseHelper.success(
            message="Report deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete report"
        )

@router.get("/analytics/overview", response_model=dict)
async def get_analytics_overview(
    period: str = Query("month"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get comprehensive analytics overview"""
    try:
        # Get date range
        start_date, end_date = get_date_range(period)
        start_date = start_date.date()
        end_date = end_date.date()
        
        # Get all metrics
        financial_metrics = await reports_utils.get_financial_metrics(current_user.id, start_date, end_date)
        sales_metrics = await reports_utils.get_sales_metrics(current_user.id, start_date, end_date)
        customer_metrics = await reports_utils.get_customer_metrics(current_user.id, start_date, end_date)
        
        # Get trend data
        charts = []
        charts.extend(await reports_utils.generate_chart_data(current_user.id, "revenue_trend", start_date, end_date))
        charts.extend(await reports_utils.generate_chart_data(current_user.id, "invoice_status", start_date, end_date))
        charts.extend(await reports_utils.generate_chart_data(current_user.id, "top_customers", start_date, end_date))
        
        analytics = {
            "financial": financial_metrics.dict(),
            "sales": sales_metrics.dict(),
            "customers": customer_metrics.dict(),
            "charts": [chart.dict() for chart in charts],
            "period": period,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        return ResponseHelper.success(
            data={"analytics": analytics},
            message="Analytics overview retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get analytics overview error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics overview"
        )

@router.get("/metrics/kpi", response_model=dict)
async def get_kpi_metrics(
    period: str = Query("month"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get KPI metrics for dashboard"""
    try:
        # Get date range
        start_date, end_date = get_date_range(period)
        start_date = start_date.date()
        end_date = end_date.date()
        
        # Get KPI metrics
        kpi_metrics = await reports_utils.get_kpi_metrics(current_user.id, start_date, end_date)
        
        return ResponseHelper.success(
            data={"kpi_metrics": [kpi.dict() for kpi in kpi_metrics]},
            message="KPI metrics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get KPI metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KPI metrics"
        )