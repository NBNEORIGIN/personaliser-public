from __future__ import annotations
from pathlib import Path
import csv
import re
import threading
import time
from typing import Dict, Optional, TypedDict

from ..settings import settings


class SkuMeta(TypedDict, total=False):
    template_id: Optional[str]
    requires_photo: bool
    default_type: Optional[str]
    COLOUR: Optional[str]
    TYPE: Optional[str]
    DecorationType: Optional[str]
    Theme: Optional[str]


_SKU_CACHE: Optional[Dict[str, Dict[str, str]]] = None
_SKU_MTIME: Optional[float] = None
_RELOAD_THREAD: Optional[threading.Thread] = None
_RELOAD_STOP = threading.Event()


def _norm(s: str) -> str:
    """Lowercase and trim, preserve punctuation (spaces/dashes/underscores)."""
    return (s or "").strip().lower()


def _norm_no_space(s: str) -> str:
    """Lowercase and trim and remove all whitespace for tolerant lookups."""
    return re.sub(r"\s+", "", (s or "").strip().lower())


def _load_if_needed() -> Dict[str, Dict[str, str]]:
    global _SKU_CACHE, _SKU_MTIME
    # Preferred: explicit settings.SKULIST_PATH; then DATA_DIR; then repo assets
    candidates = [
        getattr(settings, "SKULIST_PATH", None),
        settings.DATA_DIR / "SKULIST.csv",
        Path(__file__).resolve().parents[3] / "assets" / "SKULIST.csv",
    ]
    candidates = [p for p in candidates if isinstance(p, Path)]
    csv_path = next((p for p in candidates if p.exists()), candidates[0])
    m: Dict[str, Dict[str, str]] = _SKU_CACHE or {}
    try:
        if not csv_path.exists():
            _SKU_CACHE, _SKU_MTIME = {}, None
            return _SKU_CACHE
        stat = csv_path.stat()
        if _SKU_CACHE is None or _SKU_MTIME is None or stat.st_mtime != _SKU_MTIME:
            m = {}
            with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # detect SKU header case-insensitively
                    raw = ""
                    for rk in row.keys():
                        if (rk or "").strip().lower() == "sku":
                            raw = row.get(rk) or ""
                            break
                    if not (raw or "").strip():
                        continue
                    info = {k: (v or "").strip() for k, v in row.items()}
                    # store both punctuation-preserved and no-space keys
                    m[_norm(raw)] = info
                    m[_norm_no_space(raw)] = info
            _SKU_CACHE = m
            _SKU_MTIME = stat.st_mtime
        return _SKU_CACHE or {}
    except Exception:
        return _SKU_CACHE or {}


def get_meta_for_sku(sku: str) -> SkuMeta:
    data = _load_if_needed()
    # try both preserved and no-space variants
    info = data.get(_norm(sku)) or data.get(_norm_no_space(sku)) or {}
    meta: SkuMeta = {
        "template_id": (info.get("template_id") or None),
        "requires_photo": (str(info.get("requires_photo") or "").lower() in {"1","true","yes","y"}),
        "default_type": (info.get("default_type") or None),
    }
    for k in ("COLOUR","TYPE","DecorationType","Theme"):
        v = info.get(k)
        meta[k] = v if v else None
    return meta


def _reload_loop(interval: int) -> None:
    while not _RELOAD_STOP.is_set():
        try:
            _load_if_needed()
        except Exception:
            pass
        # basic debounce interval
        _RELOAD_STOP.wait(timeout=max(1, int(interval)))


def init() -> None:
    """Load SKU map once and start background reload if configured."""
    global _RELOAD_THREAD
    _load_if_needed()
    interval = int(getattr(settings, "SKU_MAP_RELOAD_SEC", 0) or 0)
    if interval > 0 and (_RELOAD_THREAD is None or not _RELOAD_THREAD.is_alive()):
        _RELOAD_STOP.clear()
        t = threading.Thread(target=_reload_loop, args=(interval,), name="sku_map_reloader", daemon=True)
        _RELOAD_THREAD = t
        t.start()
