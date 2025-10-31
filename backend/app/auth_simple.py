"""
Simple session-based authentication for graphics management.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
from .database import get_db
from .models.user import User

# Password hashing - configure bcrypt to truncate automatically
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False  # Don't raise error, just truncate
)

# Session storage (in-memory for now, could move to Redis)
sessions = {}  # session_token -> user_id
SESSION_EXPIRE_HOURS = 24 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using SHA256 + bcrypt to avoid length issues."""
    # Pre-hash with SHA256 to get a fixed-length string (always 64 hex chars)
    # This avoids bcrypt's 72-byte limit while maintaining security
    sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    print(f"[AUTH] Hashing password: original_len={len(password)}, sha256_len={len(sha256_hash)}, sha256_bytes={len(sha256_hash.encode('utf-8'))}", flush=True)
    try:
        result = pwd_context.hash(sha256_hash)
        print(f"[AUTH] Hash successful", flush=True)
        return result
    except Exception as e:
        print(f"[AUTH ERROR] Hash failed: {e}", flush=True)
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    # Apply same SHA256 pre-hashing as hash_password
    sha256_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(sha256_hash, hashed_password)


def create_session(user_id: int) -> str:
    """Create a new session token."""
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)
    }
    return token


def get_session_user_id(token: str) -> Optional[int]:
    """Get user ID from session token."""
    session = sessions.get(token)
    if not session:
        return None
    
    # Check if expired
    if datetime.utcnow() > session["expires_at"]:
        del sessions[token]
        return None
    
    return session["user_id"]


def delete_session(token: str):
    """Delete a session."""
    if token in sessions:
        del sessions[token]


def get_current_user(
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user."""
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_id = get_session_user_id(session_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


def get_current_user_optional(
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication - returns None if not authenticated."""
    if not session_token:
        return None
    
    user_id = get_session_user_id(session_token)
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None
    
    return user
