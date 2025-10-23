from __future__ import annotations
from typing import List, Tuple
from dataclasses import dataclass
import random

@dataclass
class Rect:
    id: str
    w: float
    h: float

@dataclass
class PlacedRect(Rect):
    x: float
    y: float


def pack_first_fit(rects: List[Rect], bed_w: float, bed_h: float, margin: float, gutter: float, keepouts: List[Tuple[float, float, float, float]], seed: int = 42) -> Tuple[List[PlacedRect], List[str]]:
    rng = random.Random(seed)
    # sort by (-area, id)
    rects_sorted = sorted(rects, key=lambda r: (-(r.w * r.h), r.id))
    placed: List[PlacedRect] = []
    warnings: List[str] = []

    cursor_y = margin
    row_height = 0.0
    while rects_sorted and cursor_y + row_height <= bed_h - margin:
        cursor_x = margin
        row_height = 0.0
        i = 0
        while i < len(rects_sorted):
            r = rects_sorted[i]
            # check fit horizontally
            if cursor_x + r.w <= bed_w - margin and cursor_y + r.h <= bed_h - margin:
                # check keepouts
                candidate = (cursor_x, cursor_y, r.w, r.h)
                if _overlaps_keepouts(candidate, keepouts):
                    # try move right by gutter until fit or break
                    moved = False
                    while cursor_x + r.w <= bed_w - margin:
                        cursor_x += gutter
                        candidate = (cursor_x, cursor_y, r.w, r.h)
                        if not _overlaps_keepouts(candidate, keepouts):
                            moved = True
                            break
                    if not moved:
                        i += 1
                        continue
                placed.append(PlacedRect(id=r.id, w=r.w, h=r.h, x=cursor_x, y=cursor_y))
                row_height = max(row_height, r.h)
                cursor_x += r.w + gutter
                rects_sorted.pop(i)
            else:
                i += 1
        if row_height == 0.0:
            # no placement possible in this row; move down minimally
            cursor_y += gutter
        else:
            cursor_y += row_height + gutter

        if cursor_y > bed_h - margin:
            break

    if rects_sorted:
        warnings.append("OVERFLOW")
    return placed, warnings


def _overlaps_keepouts(rect: Tuple[float, float, float, float], keepouts: List[Tuple[float, float, float, float]]) -> bool:
    x, y, w, h = rect
    for kx, ky, kw, kh in keepouts:
        if not (x + w <= kx or x >= kx + kw or y + h <= ky or y >= ky + kh):
            return True
    return False


def pack_paginated(
    rects: List[Rect],
    bed_w: float,
    bed_h: float,
    margin: float,
    gutter: float,
    keepouts: List[Tuple[float, float, float, float]],
    seed: int = 42,
) -> List[List[PlacedRect]]:
    """
    Deterministic pagination across multiple beds using first-fit row packing.
    - Sort rects by (-area, id) once for deterministic order.
    - Fill rows left-to-right, top-to-bottom. When no more fit, start a new bed.
    - No rotation.
    Returns: list of beds, each a list of PlacedRect.
    """
    rng = random.Random(seed)
    remaining = list(sorted(rects, key=lambda r: (-(r.w * r.h), r.id)))
    beds: List[List[PlacedRect]] = []

    while remaining:
        placed: List[PlacedRect] = []
        cursor_y = margin
        row_height = 0.0
        # We will attempt to place from remaining list scanning forward each row
        while remaining and cursor_y + row_height <= bed_h - margin:
            cursor_x = margin
            row_height = 0.0
            i = 0
            while i < len(remaining):
                r = remaining[i]
                if cursor_x + r.w <= bed_w - margin and cursor_y + r.h <= bed_h - margin:
                    candidate = (cursor_x, cursor_y, r.w, r.h)
                    if _overlaps_keepouts(candidate, keepouts):
                        moved = False
                        while cursor_x + r.w <= bed_w - margin:
                            cursor_x += gutter
                            candidate = (cursor_x, cursor_y, r.w, r.h)
                            if not _overlaps_keepouts(candidate, keepouts):
                                moved = True
                                break
                        if not moved:
                            i += 1
                            continue
                    placed.append(PlacedRect(id=r.id, w=r.w, h=r.h, x=cursor_x, y=cursor_y))
                    row_height = max(row_height, r.h)
                    cursor_x += r.w + gutter
                    remaining.pop(i)
                else:
                    i += 1
            if row_height == 0.0:
                cursor_y += gutter
            else:
                cursor_y += row_height + gutter
            if cursor_y > bed_h - margin:
                break
        # End of bed
        beds.append(placed)
        # If we couldn't place anything in this bed, break to avoid infinite loop
        if not placed:
            break

    return beds
