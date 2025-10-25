from __future__ import annotations
from typing import List, Tuple, Any
from pathlib import Path
import svgwrite

from ..settings import settings
from ..utils import storage
from .registry import register_batch
from .base import write_batch_csv
from ..utils.svg_embed import embed_image_as_data_uri

# Legacy geometry (mm)
PAGE_W_MM = 439.8
PAGE_H_MM = 289.9
MEM_W_MM = 140.0
MEM_H_MM = 90.0
COLS = 3
ROWS = 3
BATCH_SIZE = COLS * ROWS
# Centered grid (no gutters, legacy layout)
X_OFF_MM = (PAGE_W_MM - (MEM_W_MM * COLS)) / 2.0
Y_OFF_MM = (PAGE_H_MM - (MEM_H_MM * ROWS)) / 2.0

# Legacy text sizing (points scaled by legacy factor ~mm/pt they used)
PT_TO_MM = 0.2645833333  # matches legacy code factor
LINE1_PT = 17 * 1.2      # 20.4 pt
LINE2_PT = 25 * 1.2      # 30 pt
LINE3_PT = 12 * 1.1      # 13.2 pt

# Legacy text baselines within the memorial (mm from top of cell)
L1_Y_MM = 28.0
L2_Y_MM = 45.0
L3_Y_MM = 57.0

ALLOWED_COLOURS = {"copper", "gold", "silver", "stone", "marble"}
COLOUR_PRIORITY = {"copper": 0, "gold": 1, "silver": 2, "stone": 3, "marble": 4}


def _cell_origin(col: int, row: int) -> Tuple[float, float]:
    x = X_OFF_MM + col * MEM_W_MM
    y = Y_OFF_MM + row * MEM_H_MM
    return x, y


def _lines_map(it: Any) -> Tuple[str, str, str]:
    lines = getattr(it, "lines", []) or []
    mp = {}
    for l in lines:
        lid = getattr(l, "id", None) or (l.get("id") if isinstance(l, dict) else None)
        val = getattr(l, "value", None) or (l.get("value") if isinstance(l, dict) else None)
        if lid:
            mp[lid] = val or ""
    return mp.get("line_1", ""), mp.get("line_2", ""), mp.get("line_3", "")


def _wrap_line3(text: str) -> Tuple[List[str], float]:
    # Simple width heuristic based on legacy code: 0.5 * font_mm per char, max ~60% of width
    base_pt = LINE3_PT
    font_mm = base_pt * PT_TO_MM
    char_w_mm = 0.5 * font_mm
    max_line_mm = MEM_W_MM * 0.6
    max_chars = max(1, int(max_line_mm / char_w_mm))
    words = (text or "").split()
    lines: List[str] = []
    cur: List[str] = []
    for w in words:
        test = (" ".join(cur + [w])).strip()
        if len(test) > max_chars and cur:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    if len(lines) == 1 and lines[0]:
        # Secondary split if a single long line
        s = lines[0]
        if len(s) > 30:
            lines = [s[:30].rstrip(), s[30:].lstrip()]
    lines = lines[:5]
    # Legacy-like conditional sizing by total chars
    total_chars = sum(len(x) for x in lines)
    if 10 <= total_chars <= 30:
        pt = LINE1_PT
    elif 31 <= total_chars <= 90:
        pt = LINE1_PT * 0.9
    else:
        pt = LINE3_PT
    return lines, pt


def run(items: List[Any], cfg: dict):
    job_id: str = cfg["job_id"]
    out_dir: Path = cfg["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    warnings: List[str] = []  # Initialize warnings list at the start

    # Filter eligible items by enrichment: TYPE='Regular Stake', DecorationType='Graphic', COLOUR in set
    def _norm(s):
        return (s or "").strip().lower()
    eligible: List[Any] = []
    for it in items:
        colour = _norm(getattr(it, "colour", None) or (getattr(it, "get", lambda k: None)("colour") if hasattr(it, "get") else None))
        typ = _norm(getattr(it, "product_type", None) or (getattr(it, "get", lambda k: None)("product_type") if hasattr(it, "get") else None))
        deco = _norm(getattr(it, "decoration_type", None) or (getattr(it, "get", lambda k: None)("decoration_type") if hasattr(it, "get") else None))
        if (typ == "regular stake") and (deco == "graphic") and (colour in ALLOWED_COLOURS):
            eligible.append(it)

    # Sort by colour priority (copper, gold, silver, stone, marble) then take first bed
    eligible.sort(key=lambda it: COLOUR_PRIORITY.get((getattr(it, "colour", "") or "").strip().lower(), 99))
    # Limit to one bed (legacy single-bed output contract here)
    place = eligible[:BATCH_SIZE]

    # SVG doc in mm units
    dwg = svgwrite.Drawing(size=(f"{PAGE_W_MM}mm", f"{PAGE_H_MM}mm"), profile="full")
    # White background
    dwg.add(dwg.rect(insert=(0, 0), size=(f"{PAGE_W_MM}mm", f"{PAGE_H_MM}mm"), fill="white"))

    batch_rows: List[dict] = []

    for idx, it in enumerate(place):
        col = idx % COLS
        row = idx // COLS
        x_mm, y_mm = _cell_origin(col, row)
        cx_mm = x_mm + (MEM_W_MM / 2.0)

        # Legacy memorial face outline: 140x90mm, 6mm radius corners, red 0.1mm stroke
        dwg.add(
            dwg.rect(
                insert=(f"{x_mm}mm", f"{y_mm}mm"),
                size=(f"{MEM_W_MM}mm", f"{MEM_H_MM}mm"),
                rx=f"6mm",
                ry=f"6mm",
                fill="none",
                stroke="red",
                stroke_width=f"0.1mm",
            )
        )

        # Try embedded graphic by graphics_key or graphic
        gkey = getattr(it, "graphics_key", None) or getattr(it, "graphic", None) or ""
        if gkey:
            key_raw = str(gkey)
            candidates = []
            # If key includes extension, try as-is first
            candidates.append(settings.GRAPHICS_DIR / key_raw)
            # Try with .png/.PNG if no extension
            if "." not in key_raw:
                candidates.append(settings.GRAPHICS_DIR / f"{key_raw}.png")
                candidates.append(settings.GRAPHICS_DIR / f"{key_raw}.PNG")
            # Sanitized variants (lowercase, replace spaces with underscores)
            base = key_raw.rsplit(".", 1)[0]
            base_s = base.strip().replace(" ", "_")
            base_l = base.lower().replace(" ", "_")
            for b in {base, base_s, base_l}:
                candidates.append(settings.GRAPHICS_DIR / f"{b}.png")
                candidates.append(settings.GRAPHICS_DIR / f"{b}.PNG")

            href = None
            for p in candidates:
                href = embed_image_as_data_uri(p)
                if href:
                    break
            if href:
                dwg.add(dwg.image(href=href, insert=(f"{x_mm}mm", f"{y_mm}mm"), size=(f"{MEM_W_MM}mm", f"{MEM_H_MM}mm")))
            else:
                warnings.append("GRAPHIC_FILE_NOT_FOUND")

        # Text lines
        l1, l2, l3 = _lines_map(it)
        # line 1
        if l1:
            dwg.add(dwg.text(
                l1,
                insert=(f"{cx_mm}mm", f"{y_mm + L1_Y_MM}mm"),
                text_anchor="middle",
                dominant_baseline="middle",
                font_family="Georgia",
                font_size=f"{LINE1_PT * PT_TO_MM}mm",
                fill="black",
            ))
        # line 2
        if l2:
            dwg.add(dwg.text(
                l2,
                insert=(f"{cx_mm}mm", f"{y_mm + L2_Y_MM}mm"),
                text_anchor="middle",
                dominant_baseline="middle",
                font_family="Georgia",
                font_size=f"{LINE2_PT * PT_TO_MM}mm",
                fill="black",
            ))
        # line 3 with tspans
        if l3:
            lines3, pt = _wrap_line3(l3)
            if lines3:
                t = dwg.text(
                    "",
                    insert=(f"{cx_mm}mm", f"{y_mm + L3_Y_MM}mm"),
                    text_anchor="middle",
                    dominant_baseline="middle",
                    font_family="Georgia",
                    font_size=f"{pt * PT_TO_MM}mm",
                    fill="black",
                )
                for j, s in enumerate(lines3):
                    dy = "0" if j == 0 else "1.2em"
                    t.add(dwg.tspan(s, x=[f"{cx_mm}mm"], dy=[dy]))
                dwg.add(t)

        batch_rows.append({
            "order_ref": getattr(it, "order_ref", "") or "",
            "sku": (getattr(it, "sku", None) or ""),
            "graphics_key": gkey or "",
            "colour": (getattr(it, "colour", None) or ""),
            "type": (getattr(it, "product_type", None) or ""),
            "decoration": (getattr(it, "decoration_type", None) or ""),
            "theme": (getattr(it, "theme", None) or ""),
            "line_1": l1,
            "line_2": l2,
            "line_3": l3,
            "cell_row": row,
            "cell_col": col,
        })

    # Add printer origin marker: 0.1mm black square at bottom-right of the page
    dwg.add(
        dwg.rect(
            insert=(f"{PAGE_W_MM - 0.1}mm", f"{PAGE_H_MM - 0.1}mm"),
            size=("0.1mm", "0.1mm"),
            fill="black",
            stroke="none",
        )
    )

    # Save deterministically
    svg_path = out_dir / "bed_1.svg"
    dwg.saveas(svg_path)
    csv_path = out_dir / "batch.csv"
    write_batch_csv(batch_rows, csv_path)

    # Publish
    svg_url = storage.put_artifact(job_id, svg_path)
    csv_url = storage.put_artifact(job_id, csv_path)
    # Warn if any eligible item had missing graphics or unresolved files
    for it in place:
        gkey = getattr(it, "graphics_key", None) or getattr(it, "graphic", None) or ""
        if not gkey:
            warnings.append("GRAPHIC_MISSING")
        else:
            # Check at least one variant exists on disk to hint issues
            key_raw = str(gkey)
            exists = False
            for name in [key_raw, f"{key_raw}.png", f"{key_raw}.PNG", key_raw.rsplit(".",1)[0]+".png", key_raw.rsplit(".",1)[0]+".PNG"]:
                if (settings.GRAPHICS_DIR / name).exists():
                    exists = True
                    break
            if not exists:
                warnings.append("GRAPHIC_FILE_NOT_FOUND")
    return svg_url, csv_url, warnings


register_batch("regular_stake_v1", run)
