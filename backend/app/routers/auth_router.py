"""
Authentication endpoints for user registration and login.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..database import get_db
from ..models.user import User
from ..auth_simple import (
    hash_password,
    verify_password,
    create_session,
    delete_session,
    get_current_user,
    get_current_admin
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_approved: bool
    is_admin: bool
    
    class Config:
        from_attributes = True


class PendingUserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_approved: bool
    is_admin: bool
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    **Parameters:**
    - `username`: Unique username (3-50 characters)
    - `email`: Valid email address
    - `password`: Password (min 8 characters)
    
    **Returns:**
    - User object with ID and details
    """
    # Validate username length
    if len(request.username) < 3 or len(request.username) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be between 3 and 50 characters"
        )
    
    # Validate password length
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Check if username exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    try:
        print(f"[AUTH REGISTER] About to hash password for user: {request.username}", flush=True)
        user = User(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password)
        )
        print(f"[AUTH REGISTER] Password hashed successfully", flush=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create session and set cookie (auto-login after registration)
        session_token = create_session(user.id)
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=60 * 60 * 24 * 7,  # 7 days
            samesite="lax",
            path="/",
            secure=False  # Allow HTTP for development
        )
        
        print(f"[AUTH] New user registered (pending approval): {user.username} ({user.email})", flush=True)
        
        # Return user info with approval status
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_approved=user.is_approved,
            is_admin=user.is_admin
        )
    except Exception as e:
        db.rollback()
        print(f"[AUTH ERROR] Failed to create user: {str(e)}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login")
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Login with username and password.
    
    **Parameters:**
    - `username`: Username
    - `password`: Password
    
    **Returns:**
    - Session token (set as cookie)
    - User details
    """
    # Find user
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if account is approved (admins can always login)
    if not user.is_approved and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval. Please wait for admin approval."
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create session
    session_token = create_session(user.id)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
        path="/",
        secure=False  # Allow HTTP for development
    )
    
    print(f"[AUTH] User logged in: {user.username}", flush=True)
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_approved": user.is_approved,
            "is_admin": user.is_admin
        }
    }


@router.post("/logout")
async def logout(
    response: Response,
    user: User = Depends(get_current_user)
):
    """
    Logout current user.
    
    **Returns:**
    - Success message
    """
    # Get session token from cookie (would need to extract from request)
    # For now, just clear the cookie
    response.delete_cookie("session_token")
    
    print(f"[AUTH] User logged out: {user.username}", flush=True)
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """
    Get current user details.
    
    **Returns:**
    - Current user object
    """
    return user


# Admin endpoints for user management
@router.get("/admin/pending-users")
async def get_pending_users(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of users pending approval (admin only).
    
    **Returns:**
    - List of pending users
    """
    pending_users = db.query(User).filter(
        User.is_approved == False,
        User.is_admin == False
    ).order_by(User.created_at.desc()).all()
    
    return {
        "count": len(pending_users),
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "is_approved": user.is_approved
            }
            for user in pending_users
        ]
    }


@router.post("/admin/approve-user/{user_id}")
async def approve_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Approve a pending user account (admin only).
    
    **Parameters:**
    - `user_id`: ID of user to approve
    
    **Returns:**
    - Success message
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already approved"
        )
    
    user.is_approved = True
    user.approved_at = datetime.utcnow()
    db.commit()
    
    print(f"[AUTH ADMIN] User approved: {user.username} by admin {admin.username}", flush=True)
    
    return {
        "success": True,
        "message": f"User {user.username} approved successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_approved": user.is_approved
        }
    }


@router.post("/admin/reject-user/{user_id}")
async def reject_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Reject and delete a pending user account (admin only).
    
    **Parameters:**
    - `user_id`: ID of user to reject
    
    **Returns:**
    - Success message
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reject admin users"
        )
    
    username = user.username
    db.delete(user)
    db.commit()
    
    print(f"[AUTH ADMIN] User rejected and deleted: {username} by admin {admin.username}", flush=True)
    
    return {
        "success": True,
        "message": f"User {username} rejected and removed"
    }


@router.get("/admin/all-users")
async def get_all_users(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of all users (admin only).
    
    **Returns:**
    - List of all users
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    return {
        "count": len(users),
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_approved": user.is_approved,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "approved_at": user.approved_at.isoformat() if user.approved_at else None
            }
            for user in users
        ]
    }
