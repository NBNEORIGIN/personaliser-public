from __future__ import annotations
from typing import Iterable, List, Tuple, Dict, Any
from pathlib import Path
import csv

# Geometry helpers (kept minimal; prefer mm units directly in SVG)
# Only use if conversion is strictly necessary.
_DPI = 96.0
_MM_PER_IN = 25.4


def mm_to_px(mm: float) -> float:
    return (mm / _MM_PER_IN) * _DPI


def px_to_mm(px: float) -> float:
    return (px / _DPI) * _MM_PER_IN


# Deterministic item ordering
# If a legacy pipeline depends on a stable custom order, enable sort=True.
# Otherwise, keep the input order.

def order_items(items: Iterable[Any], *, sort: bool = False) -> List[Any]:
    if not sort:
        return list(items)
    def _key(it: Any) -> Tuple[str, str, str, str]:
        colour = (getattr(it, "colour", None) or "").lower()
        typ = (getattr(it, "product_type", None) or "").lower()
        sku = (getattr(it, "sku", None) or "").lower()
        ref = (getattr(it, "order_ref", None) or "").lower()
        return (colour, typ, sku, ref)
    return sorted(items, key=_key)


# CSV writer helper (deterministic header order from first row)

def write_batch_csv(rows: List[Dict[str, Any]], dest: Path) -> None:
    if not rows:
        dest.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
