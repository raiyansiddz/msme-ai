"""
AI Assistant routes for the MSME SaaS platform
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from core.database import db_manager
from modules.auth.utils import get_current_active_user
from modules.auth.models import UserResponse
from modules.ai_assistant.models import (
    AIQuery, AIResponse, QueryFeedback, QueryType
)
from modules.ai_assistant.utils import ai_assistant
from utils.helpers import ResponseHelper, generate_uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Assistant"])

@router.post("/query", response_model=dict)
async def process_ai_query(
    query_data: AIQuery,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Process AI query with business intelligence"""
    try:
        start_time = datetime.utcnow()
        
        # Process query with AI
        response_text, context_data = await ai_assistant.process_query(
            query_data.query, 
            current_user.id, 
            query_data.query_type
        )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Create AI response record
        ai_response = AIResponse(
            user_id=current_user.id,
            query=query_data.query,
            response=response_text,
            query_type=query_data.query_type,
            context_data=context_data,
            processing_time=processing_time
        )
        
        # Save to database
        await db_manager.db.ai_responses.insert_one(ai_response.dict())
        
        logger.info(f"AI query processed for user {current_user.id}: {query_data.query[:50]}...")
        
        return ResponseHelper.success(
            data={"response": ai_response.dict()},
            message="Query processed successfully"
        )
        
    except Exception as e:
        logger.error(f"AI query processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process AI query"
        )

@router.get("/insights", response_model=dict)
async def get_business_insights(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get AI-generated business insights"""
    try:
        insights = await ai_assistant.generate_business_insights(current_user.id)
        
        # Save insights to database
        for insight in insights:
            insight_doc = {
                "id": generate_uuid(),
                "user_id": current_user.id,
                "insight_type": insight["type"],
                "title": insight["title"],
                "description": insight["description"],
                "priority": insight["priority"],
                "action_required": insight["action_required"],
                "created_at": datetime.utcnow(),
                "is_read": False
            }
            await db_manager.db.ai_insights.insert_one(insight_doc)
        
        return ResponseHelper.success(
            data={"insights": insights},
            message="Business insights generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Get business insights error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate business insights"
        )

@router.get("/recommendations", response_model=dict)
async def get_business_recommendations(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get AI-generated business recommendations"""
    try:
        recommendations = await ai_assistant.generate_recommendations(current_user.id)
        
        # Save recommendations to database
        for rec in recommendations:
            rec_doc = {
                "id": generate_uuid(),
                "user_id": current_user.id,
                "recommendation_type": rec["type"],
                "title": rec["title"],
                "description": rec["description"],
                "impact_score": rec["impact_score"],
                "implementation_difficulty": rec["implementation_difficulty"],
                "expected_outcome": rec["expected_outcome"],
                "action_items": rec["action_items"],
                "created_at": datetime.utcnow(),
                "is_implemented": False
            }
            await db_manager.db.ai_recommendations.insert_one(rec_doc)
        
        return ResponseHelper.success(
            data={"recommendations": recommendations},
            message="Business recommendations generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Get business recommendations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate business recommendations"
        )

@router.get("/context", response_model=dict)
async def get_business_context(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get current business context for AI"""
    try:
        context = await ai_assistant.get_business_context(current_user.id)
        
        return ResponseHelper.success(
            data={"context": context.dict()},
            message="Business context retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get business context error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business context"
        )

@router.post("/feedback", response_model=dict)
async def submit_query_feedback(
    feedback: QueryFeedback,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Submit feedback for AI query response"""
    try:
        # Update the AI response with feedback
        result = await db_manager.db.ai_responses.update_one(
            {"id": feedback.response_id, "user_id": current_user.id},
            {"$set": {"is_helpful": feedback.is_helpful}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI response not found"
            )
        
        # Save detailed feedback
        feedback_doc = {
            "id": generate_uuid(),
            "user_id": current_user.id,
            "response_id": feedback.response_id,
            "is_helpful": feedback.is_helpful,
            "feedback_text": feedback.feedback_text,
            "rating": feedback.rating,
            "created_at": datetime.utcnow()
        }
        await db_manager.db.ai_feedback.insert_one(feedback_doc)
        
        logger.info(f"AI feedback submitted by user {current_user.id}: {feedback.is_helpful}")
        
        return ResponseHelper.success(
            message="Feedback submitted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit feedback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )

@router.get("/history", response_model=dict)
async def get_query_history(
    limit: int = 10,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get AI query history for user"""
    try:
        history = await db_manager.db.ai_responses.find(
            {"user_id": current_user.id}
        ).sort("created_at", -1).limit(limit).to_list(None)
        
        return ResponseHelper.success(
            data={"history": [AIResponse(**response).dict() for response in history]},
            message="Query history retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get query history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query history"
        )

@router.get("/analytics", response_model=dict)
async def get_ai_analytics(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get AI usage analytics"""
    try:
        # Get query statistics
        total_queries = await db_manager.db.ai_responses.count_documents({"user_id": current_user.id})
        
        # Get helpful queries
        helpful_queries = await db_manager.db.ai_responses.count_documents({
            "user_id": current_user.id,
            "is_helpful": True
        })
        
        # Get query types distribution
        pipeline = [
            {"$match": {"user_id": current_user.id}},
            {"$group": {"_id": "$query_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        query_types = await db_manager.db.ai_responses.aggregate(pipeline).to_list(None)
        
        # Calculate average response time
        avg_response_time = 0
        if total_queries > 0:
            pipeline = [
                {"$match": {"user_id": current_user.id}},
                {"$group": {"_id": None, "avg_time": {"$avg": "$processing_time"}}}
            ]
            result = await db_manager.db.ai_responses.aggregate(pipeline).to_list(None)
            if result:
                avg_response_time = result[0]["avg_time"]
        
        analytics = {
            "total_queries": total_queries,
            "helpful_queries": helpful_queries,
            "satisfaction_rate": (helpful_queries / total_queries * 100) if total_queries > 0 else 0,
            "average_response_time": avg_response_time,
            "query_types_distribution": query_types
        }
        
        return ResponseHelper.success(
            data={"analytics": analytics},
            message="AI analytics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get AI analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI analytics"
        )

@router.post("/smart-insights", response_model=dict)
async def get_smart_insights(
    query: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get smart business insights based on specific query"""
    try:
        # Common business insight queries
        insight_queries = {
            "top customers": QueryType.CUSTOMER_QUERY,
            "revenue analysis": QueryType.FINANCIAL_ANALYSIS,
            "payment status": QueryType.INVOICE_QUERY,
            "business growth": QueryType.BUSINESS_INSIGHTS,
            "overdue invoices": QueryType.INVOICE_QUERY,
            "customer trends": QueryType.CUSTOMER_QUERY,
            "profit analysis": QueryType.FINANCIAL_ANALYSIS
        }
        
        # Determine query type
        query_type = QueryType.BUSINESS_INSIGHTS
        query_lower = query.lower()
        for key, qtype in insight_queries.items():
            if key in query_lower:
                query_type = qtype
                break
        
        # Process the query
        response_text, context_data = await ai_assistant.process_query(query, current_user.id, query_type)
        
        return ResponseHelper.success(
            data={
                "insight": response_text,
                "query_type": query_type,
                "context": context_data
            },
            message="Smart insights generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Get smart insights error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate smart insights"
        )