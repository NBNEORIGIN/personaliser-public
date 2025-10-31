"""
Graphics management endpoints with user authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from ..database import get_db
from ..models.user import User, Graphic
from ..auth_simple import get_current_user, get_current_user_optional
from ..settings import settings

router = APIRouter(prefix="/api/graphics", tags=["graphics"])

# File size limits
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FILES_PER_USER = 100


class GraphicResponse(BaseModel):
    id: int
    filename: str
    url: str
    file_size: int
    uploaded_at: str
    
    class Config:
        from_attributes = True


@router.post("/upload", response_model=GraphicResponse)
async def upload_graphic(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a graphic to user's library.
    
    **Parameters:**
    - `file`: PNG/JPG/SVG file (max 5MB)
    
    **Returns:**
    - Graphic object with URL
    """
    # Check file extension
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.svg']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Check user's graphic count
    user_graphics_count = db.query(Graphic).filter(Graphic.user_id == user.id).count()
    if user_graphics_count >= MAX_FILES_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_FILES_PER_USER} graphics per user"
        )
    
    # Read file
    content = await file.read()
    file_size = len(content)
    
    # Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Create user graphics directory
    user_graphics_dir = settings.DATA_DIR / "graphics" / f"user_{user.id}"
    user_graphics_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in ".-_ ").strip()
    
    # Check if filename already exists for this user
    existing = db.query(Graphic).filter(
        Graphic.user_id == user.id,
        Graphic.filename == safe_filename
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graphic '{safe_filename}' already exists. Please rename or delete the existing one."
        )
    
    # Save file
    file_path = user_graphics_dir / safe_filename
    file_path.write_bytes(content)
    
    # Create database record
    graphic = Graphic(
        user_id=user.id,
        filename=safe_filename,
        file_path=str(file_path),
        file_size=file_size
    )
    db.add(graphic)
    db.commit()
    db.refresh(graphic)
    
    print(f"[GRAPHICS] User {user.username} uploaded: {safe_filename} ({file_size} bytes)", flush=True)
    
    return GraphicResponse(
        id=graphic.id,
        filename=graphic.filename,
        url=f"/static/graphics/user_{user.id}/{graphic.filename}",
        file_size=graphic.file_size,
        uploaded_at=graphic.uploaded_at.isoformat()
    )


@router.get("/list", response_model=List[GraphicResponse])
async def list_graphics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all graphics in user's library.
    
    **Returns:**
    - List of graphic objects
    """
    graphics = db.query(Graphic).filter(Graphic.user_id == user.id).all()
    
    return [
        GraphicResponse(
            id=g.id,
            filename=g.filename,
            url=f"/static/graphics/user_{user.id}/{g.filename}",
            file_size=g.file_size,
            uploaded_at=g.uploaded_at.isoformat()
        )
        for g in graphics
    ]


@router.delete("/{graphic_id}")
async def delete_graphic(
    graphic_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a graphic from user's library.
    
    **Parameters:**
    - `graphic_id`: ID of graphic to delete
    
    **Returns:**
    - Success message
    """
    # Find graphic
    graphic = db.query(Graphic).filter(
        Graphic.id == graphic_id,
        Graphic.user_id == user.id
    ).first()
    
    if not graphic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Graphic not found"
        )
    
    # Delete file
    file_path = Path(graphic.file_path)
    if file_path.exists():
        file_path.unlink()
    
    # Delete database record
    db.delete(graphic)
    db.commit()
    
    print(f"[GRAPHICS] User {user.username} deleted: {graphic.filename}", flush=True)
    
    return {"success": True, "message": "Graphic deleted"}


@router.get("/public", response_model=List[GraphicResponse])
async def list_public_graphics():
    """
    List public graphics library (available to all users).
    
    **Returns:**
    - List of public graphic objects
    """
    public_dir = settings.DATA_DIR / "graphics" / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    
    graphics = []
    for file_path in public_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg']:
            graphics.append(GraphicResponse(
                id=0,  # Public graphics don't have IDs
                filename=file_path.name,
                url=f"/static/graphics/public/{file_path.name}",
                file_size=file_path.stat().st_size,
                uploaded_at=""
            ))
    
    return graphics
