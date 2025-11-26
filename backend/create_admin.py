"""
Script to create an admin user account.
Run this after database migration to create your first admin.

Usage:
    python create_admin.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, init_db
from app.models.user import User
from app.auth_simple import hash_password
from datetime import datetime


def create_admin():
    """Create an admin user account."""
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("NBNE Personaliser - Create Admin Account")
        print("="*60 + "\n")
        
        # Get admin details
        username = input("Enter admin username: ").strip()
        if not username:
            print("❌ Username cannot be empty")
            return
        
        # Check if username exists
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"❌ Username '{username}' already exists")
            
            # Ask if they want to make existing user an admin
            make_admin = input(f"Make '{username}' an admin? (y/n): ").strip().lower()
            if make_admin == 'y':
                existing.is_admin = True
                existing.is_approved = True
                existing.approved_at = datetime.utcnow()
                db.commit()
                print(f"✅ User '{username}' is now an admin!")
            return
        
        email = input("Enter admin email: ").strip()
        if not email:
            print("❌ Email cannot be empty")
            return
        
        # Check if email exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            print(f"❌ Email '{email}' already registered")
            return
        
        password = input("Enter admin password (min 8 characters): ").strip()
        if len(password) < 8:
            print("❌ Password must be at least 8 characters")
            return
        
        confirm_password = input("Confirm password: ").strip()
        if password != confirm_password:
            print("❌ Passwords do not match")
            return
        
        # Create admin user
        print("\n⏳ Creating admin account...")
        
        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_approved=True,
            is_admin=True,
            approved_at=datetime.utcnow()
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("\n" + "="*60)
        print("✅ Admin account created successfully!")
        print("="*60)
        print(f"\nUsername: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Admin: {admin.is_admin}")
        print(f"Approved: {admin.is_approved}")
        print(f"Created: {admin.created_at}")
        print("\nYou can now login with these credentials.")
        print("="*60 + "\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating admin: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
