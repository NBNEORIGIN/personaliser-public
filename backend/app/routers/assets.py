from __future__ import annotations
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Optional, Dict, Any
from uuid import uuid4
from ..utils.storage import get_storage, make_upload_key
from ..settings import settings
from ..auth import get_current_user

router = APIRouter()


@router.post("/assets/presign-upload")
def presign_upload(payload: Optional[Dict[str, Any]] = Body(None), user=Depends(get_current_user)):
    if not payload or not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail={"error": "invalid_payload"})
    content_type = payload.get("content_type") or "application/octet-stream"
    key = make_upload_key("uploads")
    storage = get_storage()
    sig = storage.presign_upload(key, content_type)
    # Provide a GET url too
    get_url = storage.presign_get(key, settings.PRESIGN_EXPIRES_S)
    return {
        "asset_id": uuid4().hex[:8],
        "upload_url": sig.url,
        "fields": sig.fields,
        "get_url": get_url,
        "storage_key": key,
    }
