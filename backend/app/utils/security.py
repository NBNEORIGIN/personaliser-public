"""Security utilities for file validation and sanitization."""
import re
from pathlib import Path
from fastapi import HTTPException, UploadFile

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'.txt', '.tsv', '.csv', '.zip'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


def sanitize_filename(filename: str) -> str:
    """
    Remove dangerous characters from filename.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Get just the filename (no path traversal)
    filename = Path(filename).name
    
    # Remove special characters except . - _
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length to prevent filesystem issues
    if len(filename) > 255:
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            filename = name[:250] + '.' + ext
        else:
            filename = filename[:255]
    
    return filename


async def validate_upload(file: UploadFile) -> bool:
    """
    Validate uploaded file for security.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            detail={
                "message": "Invalid file type",
                "hint": f"Allowed file types: {', '.join(ALLOWED_EXTENSIONS)}",
                "code": "INVALID_FILE_TYPE",
                "support": "Contact support@nbne.uk if you need help"
            }
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        raise HTTPException(
            400,
            detail={
                "message": "File too large",
                "hint": f"Maximum file size is {max_mb}MB",
                "code": "FILE_TOO_LARGE",
                "support": "Contact support@nbne.uk if you need help"
            }
        )
    
    # Check for empty files
    if size == 0:
        raise HTTPException(
            400,
            detail={
                "message": "Empty file",
                "hint": "The uploaded file appears to be empty",
                "code": "EMPTY_FILE",
                "support": "Contact support@nbne.uk if you need help"
            }
        )
    
    return True


def validate_path(file_path: Path, base_dir: Path) -> bool:
    """
    Validate that a file path is within the allowed base directory.
    Prevents path traversal attacks.
    
    Args:
        file_path: Path to validate
        base_dir: Base directory that file must be within
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If path is invalid or outside base directory
    """
    try:
        # Resolve both paths to absolute
        resolved_path = file_path.resolve()
        resolved_base = base_dir.resolve()
        
        # Check if file_path is within base_dir
        if not str(resolved_path).startswith(str(resolved_base)):
            raise HTTPException(
                403,
                detail={
                    "message": "Access denied",
                    "hint": "Invalid file path",
                    "code": "PATH_TRAVERSAL_ATTEMPT"
                }
            )
        
        return True
    except Exception as e:
        raise HTTPException(
            400,
            detail={
                "message": "Invalid path",
                "hint": "The file path is invalid",
                "code": "INVALID_PATH"
            }
        )
