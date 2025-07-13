"""
Advanced Invoice routes for the MSME SaaS platform
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date
from core.database import db_manager
from modules.auth.utils import get_current_active_user
from modules.auth.models import UserResponse
from modules.invoices.models import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceFilter,
    InvoiceStats, PaymentRecord, InvoiceReminder, BulkInvoiceAction
)
from modules.invoices.utils import invoice_utils
from utils.helpers import ResponseHelper, paginate_results, generate_uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Invoices"])

@router.post("/", response_model=dict)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Create a new invoice with advanced features"""
    try:
        # Validate customer exists
        customer = await db_manager.db.customers.find_one({
            "id": invoice_data.customer_id,
            "user_id": current_user.id
        })
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found"
            )
        
        # Create invoice document
        invoice_dict = invoice_data.dict()
        invoice_dict.update({
            "id": generate_uuid(),
            "user_id": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Insert invoice
        result = await db_manager.db.invoices.insert_one(invoice_dict)
        
        if result.inserted_id:
            # Get created invoice with customer info
            invoice = await db_manager.db.invoices.find_one({"id": invoice_dict["id"]})
            invoices_with_customer = await invoice_utils.populate_customer_info([invoice])
            
            logger.info(f"Invoice created: {invoice_dict['invoice_number']} by user {current_user.id}")
            return ResponseHelper.success(
                data={"invoice": InvoiceResponse(**invoices_with_customer[0]).dict()},
                message="Invoice created successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create invoice"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invoice creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invoice creation failed"
        )

@router.get("/", response_model=dict)
async def get_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get invoices with advanced filtering and pagination"""
    try:
        # Build query
        query = {"user_id": current_user.id}
        
        if status:
            query["status"] = status
        if customer_id:
            query["customer_id"] = customer_id
        if from_date:
            query["created_at"] = query.get("created_at", {})
            query["created_at"]["$gte"] = from_date
        if to_date:
            query["created_at"] = query.get("created_at", {})
            query["created_at"]["$lte"] = to_date
        
        # Get invoices
        invoices = await db_manager.db.invoices.find(query).sort("created_at", -1).to_list(None)
        
        # Populate customer information
        invoices_with_customer = await invoice_utils.populate_customer_info(invoices)
        
        # Paginate results
        paginated_data = paginate_results(invoices_with_customer, page, page_size)
        
        return ResponseHelper.paginated_success(
            data=[InvoiceResponse(**invoice).dict() for invoice in paginated_data["items"]],
            pagination=paginated_data["pagination"],
            message="Invoices retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get invoices error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoices"
        )

@router.get("/{invoice_id}", response_model=dict)
async def get_invoice(
    invoice_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get a specific invoice with full details"""
    try:
        invoice = await db_manager.db.invoices.find_one({
            "id": invoice_id,
            "user_id": current_user.id
        })
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        # Populate customer information
        invoices_with_customer = await invoice_utils.populate_customer_info([invoice])
        
        return ResponseHelper.success(
            data={"invoice": InvoiceResponse(**invoices_with_customer[0]).dict()},
            message="Invoice retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get invoice error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice"
        )

@router.put("/{invoice_id}", response_model=dict)
async def update_invoice(
    invoice_id: str,
    invoice_update: InvoiceUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update an invoice"""
    try:
        # Check if invoice exists
        existing_invoice = await db_manager.db.invoices.find_one({
            "id": invoice_id,
            "user_id": current_user.id
        })
        
        if not existing_invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        # Prepare update data
        update_data = invoice_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update invoice
            await db_manager.db.invoices.update_one(
                {"id": invoice_id, "user_id": current_user.id},
                {"$set": update_data}
            )
            
            # Update invoice status
            await invoice_utils.update_invoice_status(invoice_id, current_user.id)
            
            # Get updated invoice
            updated_invoice = await db_manager.db.invoices.find_one({
                "id": invoice_id,
                "user_id": current_user.id
            })
            
            invoices_with_customer = await invoice_utils.populate_customer_info([updated_invoice])
            
            logger.info(f"Invoice updated: {invoice_id} by user {current_user.id}")
            return ResponseHelper.success(
                data={"invoice": InvoiceResponse(**invoices_with_customer[0]).dict()},
                message="Invoice updated successfully"
            )
        else:
            return ResponseHelper.success(
                data={"invoice": InvoiceResponse(**existing_invoice).dict()},
                message="No changes to update"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update invoice error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update invoice"
        )

@router.delete("/{invoice_id}", response_model=dict)
async def delete_invoice(
    invoice_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Delete an invoice"""
    try:
        result = await db_manager.db.invoices.delete_one({
            "id": invoice_id,
            "user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        logger.info(f"Invoice deleted: {invoice_id} by user {current_user.id}")
        return ResponseHelper.success(
            message="Invoice deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete invoice error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete invoice"
        )

@router.get("/stats/summary", response_model=dict)
async def get_invoice_summary(
    period: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get invoice summary statistics"""
    try:
        summary = await invoice_utils.calculate_invoice_summary(current_user.id, period)
        
        return ResponseHelper.success(
            data={"summary": summary},
            message="Invoice summary retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get invoice summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice summary"
        )

@router.get("/stats/analytics", response_model=dict)
async def get_invoice_analytics(
    period: str = Query("month"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get advanced invoice analytics"""
    try:
        stats = await invoice_utils.get_invoice_stats(current_user.id, period)
        
        return ResponseHelper.success(
            data={"analytics": stats},
            message="Invoice analytics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get invoice analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice analytics"
        )

@router.get("/overdue", response_model=dict)
async def get_overdue_invoices(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get all overdue invoices"""
    try:
        overdue_invoices = await invoice_utils.get_overdue_invoices(current_user.id)
        invoices_with_customer = await invoice_utils.populate_customer_info(overdue_invoices)
        
        return ResponseHelper.success(
            data={"invoices": [InvoiceResponse(**invoice).dict() for invoice in invoices_with_customer]},
            message="Overdue invoices retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get overdue invoices error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve overdue invoices"
        )

@router.post("/bulk-actions", response_model=dict)
async def bulk_invoice_actions(
    bulk_action: BulkInvoiceAction,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Perform bulk actions on invoices"""
    try:
        affected_count = 0
        
        if bulk_action.action == "mark_paid":
            result = await db_manager.db.invoices.update_many(
                {
                    "id": {"$in": bulk_action.invoice_ids},
                    "user_id": current_user.id
                },
                {"$set": {
                    "payment_status": "paid",
                    "status": "paid",
                    "paid_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            affected_count = result.modified_count
            
        elif bulk_action.action == "mark_sent":
            result = await db_manager.db.invoices.update_many(
                {
                    "id": {"$in": bulk_action.invoice_ids},
                    "user_id": current_user.id
                },
                {"$set": {
                    "status": "sent",
                    "sent_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }}
            )
            affected_count = result.modified_count
            
        elif bulk_action.action == "delete":
            result = await db_manager.db.invoices.delete_many({
                "id": {"$in": bulk_action.invoice_ids},
                "user_id": current_user.id
            })
            affected_count = result.deleted_count
        
        logger.info(f"Bulk action {bulk_action.action} performed on {affected_count} invoices by user {current_user.id}")
        return ResponseHelper.success(
            data={"affected_count": affected_count},
            message=f"Bulk action {bulk_action.action} completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Bulk invoice actions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk actions"
        )

@router.post("/{invoice_id}/send-reminder", response_model=dict)
async def send_invoice_reminder(
    invoice_id: str,
    reminder_type: str = Query("email"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Send invoice reminder to customer"""
    try:
        # Check if invoice exists
        invoice = await db_manager.db.invoices.find_one({
            "id": invoice_id,
            "user_id": current_user.id
        })
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        # TODO: Implement actual reminder sending logic
        # For now, just log the reminder
        reminder_data = {
            "id": generate_uuid(),
            "invoice_id": invoice_id,
            "reminder_type": reminder_type,
            "sent_at": datetime.utcnow(),
            "status": "sent",
            "user_id": current_user.id
        }
        
        await db_manager.db.invoice_reminders.insert_one(reminder_data)
        
        logger.info(f"Invoice reminder sent: {invoice_id} via {reminder_type} by user {current_user.id}")
        return ResponseHelper.success(
            data={"reminder": reminder_data},
            message=f"Invoice reminder sent via {reminder_type}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send invoice reminder error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invoice reminder"
        )