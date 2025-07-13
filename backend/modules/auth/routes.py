"""
Authentication routes for the MSME SaaS platform
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from core.database import db_manager
from core.security import security_manager
from modules.auth.models import (
    UserCreate, UserLogin, UserResponse, Token, TokenRefresh,
    PasswordChange, ForgotPassword, ResetPassword, UserUpdate
)
from modules.auth.utils import get_current_user, get_current_active_user
from utils.helpers import ResponseHelper, generate_uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db_manager.db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user document
        user_dict = user_data.dict(exclude={"password", "confirm_password"})
        user_dict.update({
            "id": generate_uuid(),
            "password": security_manager.get_password_hash(user_data.password),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None
        })
        
        # Insert user into database
        result = await db_manager.db.users.insert_one(user_dict)
        
        if result.inserted_id:
            # Create access token
            access_token = security_manager.create_access_token(
                data={"sub": user_dict["id"]}
            )
            refresh_token = security_manager.create_refresh_token(
                data={"sub": user_dict["id"]}
            )
            
            # Return user data and token
            user_response = UserResponse(**user_dict)
            token_data = Token(
                access_token=access_token,
                refresh_token=refresh_token
            )
            
            logger.info(f"User registered successfully: {user_data.email}")
            return ResponseHelper.success(
                data={
                    "user": user_response.dict(),
                    "token": token_data.dict()
                },
                message="User registered successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=dict)
async def login(user_credentials: UserLogin):
    """User login"""
    try:
        # Find user by email
        user = await db_manager.db.users.find_one({"email": user_credentials.email})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not security_manager.verify_password(user_credentials.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Update last login
        await db_manager.db.users.update_one(
            {"id": user["id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create tokens
        access_token = security_manager.create_access_token(
            data={"sub": user["id"]}
        )
        refresh_token = security_manager.create_refresh_token(
            data={"sub": user["id"]}
        )
        
        # Return user data and token
        user_response = UserResponse(**user)
        token_data = Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        logger.info(f"User logged in successfully: {user_credentials.email}")
        return ResponseHelper.success(
            data={
                "user": user_response.dict(),
                "token": token_data.dict()
            },
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=dict)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = security_manager.verify_token(token_data.refresh_token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if user exists and is active
        user = await db_manager.db.users.find_one({"id": user_id})
        if not user or not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = security_manager.create_access_token(
            data={"sub": user_id}
        )
        
        new_token_data = Token(
            access_token=access_token,
            refresh_token=token_data.refresh_token
        )
        
        return ResponseHelper.success(
            data={"token": new_token_data.dict()},
            message="Token refreshed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_active_user)):
    """Get current user information"""
    return ResponseHelper.success(
        data={"user": current_user.dict()},
        message="User information retrieved successfully"
    )

@router.put("/me", response_model=dict)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update current user information"""
    try:
        # Prepare update data
        update_data = user_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update user in database
            await db_manager.db.users.update_one(
                {"id": current_user.id},
                {"$set": update_data}
            )
            
            # Get updated user data
            updated_user = await db_manager.db.users.find_one({"id": current_user.id})
            user_response = UserResponse(**updated_user)
            
            logger.info(f"User updated successfully: {current_user.email}")
            return ResponseHelper.success(
                data={"user": user_response.dict()},
                message="User information updated successfully"
            )
        else:
            return ResponseHelper.success(
                data={"user": current_user.dict()},
                message="No changes to update"
            )
            
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user information"
        )

@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Change user password"""
    try:
        # Get current user data
        user = await db_manager.db.users.find_one({"id": current_user.id})
        
        # Verify current password
        if not security_manager.verify_password(password_data.current_password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        new_password_hash = security_manager.get_password_hash(password_data.new_password)
        await db_manager.db.users.update_one(
            {"id": current_user.id},
            {"$set": {
                "password": new_password_hash,
                "updated_at": datetime.utcnow()
            }}
        )
        
        logger.info(f"Password changed successfully for user: {current_user.email}")
        return ResponseHelper.success(
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.post("/logout", response_model=dict)
async def logout(current_user: UserResponse = Depends(get_current_active_user)):
    """User logout"""
    # In a more advanced implementation, you might want to:
    # 1. Blacklist the current token
    # 2. Clear any session data
    # 3. Log the logout event
    
    logger.info(f"User logged out: {current_user.email}")
    return ResponseHelper.success(
        message="Logout successful"
    )

# Additional endpoints for future implementation
@router.post("/forgot-password", response_model=dict)
async def forgot_password(email_data: ForgotPassword):
    """Forgot password - send reset email"""
    # TODO: Implement email sending for password reset
    logger.info(f"Password reset requested for: {email_data.email}")
    return ResponseHelper.success(
        message="Password reset instructions sent to your email"
    )

@router.post("/reset-password", response_model=dict)
async def reset_password(reset_data: ResetPassword):
    """Reset password with token"""
    # TODO: Implement password reset with token validation
    logger.info("Password reset attempted")
    return ResponseHelper.success(
        message="Password reset successful"
    )