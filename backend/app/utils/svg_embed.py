from __future__ import annotations
import base64
import mimetypes
from pathlib import Path
from typing import Optional


def embed_image_as_data_uri(path: Path) -> Optional[str]:
    """Return a data: URI for the given image path, or None if missing.

    Uses mimetypes to guess the Content-Type; defaults to image/png.
    Encodes bytes as base64 ASCII string.
    """
    try:
        if not path.exists():
            return None
        mime, _ = mimetypes.guess_type(str(path))
        if not mime:
            mime = "image/png"
        data = path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None
