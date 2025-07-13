"""
Advanced CRM routes for the MSME SaaS platform
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from core.database import db_manager
from modules.auth.utils import get_current_active_user
from modules.auth.models import UserResponse
from modules.crm.models import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerFilter,
    InteractionCreate, InteractionUpdate, InteractionResponse,
    CustomerStats, BulkCustomerAction
)
from modules.crm.utils import crm_utils
from utils.helpers import ResponseHelper, paginate_results, generate_uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["CRM"])

@router.post("/customers", response_model=dict)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Create a new customer"""
    try:
        # Check if customer with same email already exists
        if customer_data.email:
            existing_customer = await db_manager.db.customers.find_one({
                "email": customer_data.email,
                "user_id": current_user.id
            })
            if existing_customer:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer with this email already exists"
                )
        
        # Create customer document
        customer_dict = customer_data.dict()
        customer_dict.update({
            "id": generate_uuid(),
            "user_id": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Insert customer
        result = await db_manager.db.customers.insert_one(customer_dict)
        
        if result.inserted_id:
            # Get created customer with stats
            customers_with_stats = await crm_utils.populate_customer_stats([customer_dict], current_user.id)
            
            logger.info(f"Customer created: {customer_data.name} by user {current_user.id}")
            return ResponseHelper.success(
                data={"customer": CustomerResponse(**customers_with_stats[0]).dict()},
                message="Customer created successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create customer"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Customer creation failed"
        )

@router.get("/customers", response_model=dict)
async def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    customer_type: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get customers with advanced filtering and search"""
    try:
        # Build query
        query = {"user_id": current_user.id}
        
        if status:
            query["status"] = status
        if customer_type:
            query["customer_type"] = customer_type
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"company": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}}
            ]
        
        # Get customers
        customers = await db_manager.db.customers.find(query).sort("created_at", -1).to_list(None)
        
        # Populate customer statistics
        customers_with_stats = await crm_utils.populate_customer_stats(customers, current_user.id)
        
        # Paginate results
        paginated_data = paginate_results(customers_with_stats, page, page_size)
        
        return ResponseHelper.paginated_success(
            data=[CustomerResponse(**customer).dict() for customer in paginated_data["items"]],
            pagination=paginated_data["pagination"],
            message="Customers retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get customers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customers"
        )

@router.get("/customers/{customer_id}", response_model=dict)
async def get_customer(
    customer_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get a specific customer with detailed information"""
    try:
        customer = await db_manager.db.customers.find_one({
            "id": customer_id,
            "user_id": current_user.id
        })
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Populate customer statistics
        customers_with_stats = await crm_utils.populate_customer_stats([customer], current_user.id)
        
        # Get customer interactions
        interactions = await crm_utils.get_customer_interactions(customer_id, current_user.id)
        
        customer_data = customers_with_stats[0]
        customer_data["recent_interactions"] = interactions
        
        return ResponseHelper.success(
            data={"customer": CustomerResponse(**customer_data).dict()},
            message="Customer retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get customer error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer"
        )

@router.put("/customers/{customer_id}", response_model=dict)
async def update_customer(
    customer_id: str,
    customer_update: CustomerUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update a customer"""
    try:
        # Check if customer exists
        existing_customer = await db_manager.db.customers.find_one({
            "id": customer_id,
            "user_id": current_user.id
        })
        
        if not existing_customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Prepare update data
        update_data = customer_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update customer
            await db_manager.db.customers.update_one(
                {"id": customer_id, "user_id": current_user.id},
                {"$set": update_data}
            )
            
            # Get updated customer
            updated_customer = await db_manager.db.customers.find_one({
                "id": customer_id,
                "user_id": current_user.id
            })
            
            customers_with_stats = await crm_utils.populate_customer_stats([updated_customer], current_user.id)
            
            logger.info(f"Customer updated: {customer_id} by user {current_user.id}")
            return ResponseHelper.success(
                data={"customer": CustomerResponse(**customers_with_stats[0]).dict()},
                message="Customer updated successfully"
            )
        else:
            customers_with_stats = await crm_utils.populate_customer_stats([existing_customer], current_user.id)
            return ResponseHelper.success(
                data={"customer": CustomerResponse(**customers_with_stats[0]).dict()},
                message="No changes to update"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update customer error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer"
        )

@router.delete("/customers/{customer_id}", response_model=dict)
async def delete_customer(
    customer_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Delete a customer"""
    try:
        # Check if customer has any invoices
        invoice_count = await db_manager.db.invoices.count_documents({
            "customer_id": customer_id,
            "user_id": current_user.id
        })
        
        if invoice_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete customer with existing invoices"
            )
        
        result = await db_manager.db.customers.delete_one({
            "id": customer_id,
            "user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Also delete customer interactions
        await db_manager.db.interactions.delete_many({
            "customer_id": customer_id,
            "user_id": current_user.id
        })
        
        logger.info(f"Customer deleted: {customer_id} by user {current_user.id}")
        return ResponseHelper.success(
            message="Customer deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete customer error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete customer"
        )

@router.get("/customers/stats/summary", response_model=dict)
async def get_customer_summary(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get customer summary statistics"""
    try:
        summary = await crm_utils.get_customer_summary(current_user.id)
        
        return ResponseHelper.success(
            data={"summary": summary},
            message="Customer summary retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get customer summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer summary"
        )

@router.post("/interactions", response_model=dict)
async def create_interaction(
    interaction_data: InteractionCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Create a new customer interaction"""
    try:
        # Validate customer exists
        customer = await db_manager.db.customers.find_one({
            "id": interaction_data.customer_id,
            "user_id": current_user.id
        })
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found"
            )
        
        # Create interaction document
        interaction_dict = interaction_data.dict()
        interaction_dict.update({
            "id": generate_uuid(),
            "user_id": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Insert interaction
        result = await db_manager.db.interactions.insert_one(interaction_dict)
        
        if result.inserted_id:
            # Update customer's last interaction
            await crm_utils.update_customer_last_interaction(interaction_data.customer_id, current_user.id)
            
            # Add customer information
            interaction_dict["customer_name"] = customer.get("name")
            interaction_dict["customer_email"] = customer.get("email")
            interaction_dict["customer_phone"] = customer.get("phone")
            
            logger.info(f"Interaction created for customer: {interaction_data.customer_id} by user {current_user.id}")
            return ResponseHelper.success(
                data={"interaction": InteractionResponse(**interaction_dict).dict()},
                message="Interaction created successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create interaction"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interaction creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interaction creation failed"
        )

@router.get("/interactions", response_model=dict)
async def get_interactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    customer_id: Optional[str] = Query(None),
    interaction_type: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get interactions with filtering"""
    try:
        # Build query
        query = {"user_id": current_user.id}
        
        if customer_id:
            query["customer_id"] = customer_id
        if interaction_type:
            query["type"] = interaction_type
        
        # Get interactions
        interactions = await db_manager.db.interactions.find(query).sort("interaction_date", -1).to_list(None)
        
        # Populate customer information
        customer_ids = list(set(interaction.get("customer_id") for interaction in interactions))
        customers = await db_manager.db.customers.find({
            "id": {"$in": customer_ids}
        }).to_list(None)
        
        customer_lookup = {customer["id"]: customer for customer in customers}
        
        for interaction in interactions:
            customer_id = interaction.get("customer_id")
            if customer_id and customer_id in customer_lookup:
                customer = customer_lookup[customer_id]
                interaction["customer_name"] = customer.get("name", "")
                interaction["customer_email"] = customer.get("email", "")
                interaction["customer_phone"] = customer.get("phone", "")
        
        # Paginate results
        paginated_data = paginate_results(interactions, page, page_size)
        
        return ResponseHelper.paginated_success(
            data=[InteractionResponse(**interaction).dict() for interaction in paginated_data["items"]],
            pagination=paginated_data["pagination"],
            message="Interactions retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get interactions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interactions"
        )

@router.get("/follow-ups", response_model=dict)
async def get_pending_follow_ups(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get customers with pending follow-ups"""
    try:
        customers = await crm_utils.get_customers_with_pending_follow_ups(current_user.id)
        
        return ResponseHelper.success(
            data={"customers": [CustomerResponse(**customer).dict() for customer in customers]},
            message="Pending follow-ups retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get pending follow-ups error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending follow-ups"
        )