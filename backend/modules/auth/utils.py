"""
Authentication utilities for the MSME SaaS platform
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.security import security_manager
from core.database import db_manager
from modules.auth.models import UserResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Security scheme for JWT authentication
security_scheme = HTTPBearer()

class AuthDependencies:
    """Authentication dependencies for FastAPI"""
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
    ) -> UserResponse:
        """Get current authenticated user"""
        token = credentials.credentials
        
        try:
            # Verify the token
            payload = security_manager.verify_token(token)
            user_id = payload.get("sub")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Get user from database
            user = await db_manager.db.users.find_one({"id": user_id})
            
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return UserResponse(**user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def get_current_active_user(
        current_user: UserResponse = Depends(get_current_user)
    ) -> UserResponse:
        """Get current active user"""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user

# Convenience functions for dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> UserResponse:
    """Get current authenticated user - convenience function"""
    return await AuthDependencies.get_current_user(credentials)

async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Get current active user - convenience function"""
    return await AuthDependencies.get_current_active_user(current_user)

class PermissionChecker:
    """Permission checking utilities"""
    
    @staticmethod
    def check_user_access(current_user: UserResponse, target_user_id: str) -> bool:
        """Check if current user has access to target user's data"""
        return current_user.id == target_user_id
    
    @staticmethod
    def check_resource_access(current_user: UserResponse, resource_user_id: str) -> bool:
        """Check if current user has access to a specific resource"""
        return current_user.id == resource_user_id

def require_user_access(current_user: UserResponse, target_user_id: str):
    """Require user to have access to target user's data"""
    if not PermissionChecker.check_user_access(current_user, target_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

def require_resource_access(current_user: UserResponse, resource_user_id: str):
    """Require user to have access to a specific resource"""
    if not PermissionChecker.check_resource_access(current_user, resource_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )