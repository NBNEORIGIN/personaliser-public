"""
Regular Stakes Processor - PDF Version
Uses ReportLab to generate PDFs with editable text and graphics.
"""
from __future__ import annotations
from typing import List, Tuple, Any
from pathlib import Path
from datetime import datetime
import gc

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ..models import IngestItem
from ..settings import settings
from .item_router import register_batch
from .base import write_batch_csv

# Register Georgia font
FONTS_DIR = Path(__file__).resolve().parents[3] / "fonts"
georgia_path = FONTS_DIR / "georgia.ttf"
if georgia_path.exists():
    pdfmetrics.registerFont(TTFont('Georgia', str(georgia_path)))
    print(f"[REGULAR PDF] Registered Georgia font from {georgia_path}", flush=True)
else:
    print(f"[REGULAR PDF] WARNING: Georgia font not found at {georgia_path}", flush=True)

# Page and memorial dimensions
PAGE_W_MM = 439.8
PAGE_H_MM = 289.9
MEMORIAL_W_MM = 140.0
MEMORIAL_H_MM = 90.0
COLS = 3
ROWS = 3
BATCH_SIZE = COLS * ROWS

# Centered grid layout
X_OFF_MM = (PAGE_W_MM - (MEMORIAL_W_MM * COLS)) / 2.0
Y_OFF_MM = (PAGE_H_MM - (MEMORIAL_H_MM * ROWS)) / 2.0

# Text positioning (from memorial top)
LINE1_Y_MM = 28.0
LINE2_Y_MM = 45.0
LINE3_Y_MM = 57.0

# Text sizing
LINE1_PT = 17 * 1.2  # 20.4pt
LINE2_PT = 25 * 1.2  # 30pt
LINE3_PT = 12 * 1.1  # 13.2pt

# Font setup
FONT_NAME = "Georgia"

# Allowed colours
ALLOWED_COLOURS = {"copper", "gold", "silver", "stone", "marble", "black"}
COLOUR_PRIORITY = {"copper": 0, "gold": 1, "silver": 2, "stone": 3, "marble": 4, "black": 5}


def _text_lines_map(it: Any) -> Tuple[str, str, str]:
    """Extract text lines from IngestItem"""
    lines = getattr(it, "lines", []) or []
    mp = {}
    for l in lines:
        lid = getattr(l, "id", None) or (l.get("id") if isinstance(l, dict) else None)
        val = getattr(l, "value", None) or (l.get("value") if isinstance(l, dict) else None)
        if lid:
            mp[lid] = val or ""
    return mp.get("line_1", ""), mp.get("line_2", ""), mp.get("line_3", "")


def _wrap_line3(text: str) -> Tuple[List[str], float]:
    """Wrap line 3 text and determine font size"""
    PT_TO_MM = 0.2645833333
    base_pt = LINE3_PT
    font_mm = base_pt * PT_TO_MM
    char_w_mm = 0.5 * font_mm
    max_line_mm = MEMORIAL_W_MM * 0.6
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
        s = lines[0]
        if len(s) > 30:
            lines = [s[:30].rstrip(), s[30:].lstrip()]
    
    lines = lines[:5]
    
    # Adjust font size based on total characters
    total_chars = sum(len(x) for x in lines)
    if 10 <= total_chars <= 30:
        pt = LINE1_PT
    elif 31 <= total_chars <= 90:
        pt = LINE1_PT * 0.9
    else:
        pt = LINE3_PT
    
    return lines, pt


def _add_regular_memorial(c: canvas.Canvas, x_mm: float, y_mm: float, item: Any, idx: int, warnings: List[str]):
    """Add a single regular memorial to the PDF"""
    
    # Draw memorial outline (red, 0.1mm stroke, 6mm corner radius)
    c.setStrokeColorRGB(1, 0, 0)
    c.setLineWidth(0.1 * mm)
    c.roundRect(
        x_mm * mm, y_mm * mm,
        MEMORIAL_W_MM * mm, MEMORIAL_H_MM * mm,
        6 * mm,
        stroke=1, fill=0
    )
    
    # Try to embed graphic
    gkey = getattr(item, "graphics_key", None) or getattr(item, "graphic", None) or ""
    if gkey:
        try:
            key_raw = str(gkey)
            candidates = []
            
            # If key includes extension, try as-is first
            candidates.append(settings.GRAPHICS_DIR / key_raw)
            
            # Try with .png/.PNG if no extension
            if "." not in key_raw:
                candidates.append(settings.GRAPHICS_DIR / f"{key_raw}.png")
                candidates.append(settings.GRAPHICS_DIR / f"{key_raw}.PNG")
            
            # Sanitized variants
            base = key_raw.rsplit(".", 1)[0]
            base_s = base.strip().replace(" ", "_")
            base_l = base.lower().replace(" ", "_")
            for b in {base, base_s, base_l}:
                candidates.append(settings.GRAPHICS_DIR / f"{b}.png")
                candidates.append(settings.GRAPHICS_DIR / f"{b}.PNG")
            
            graphic_path = None
            for p in candidates:
                if p.exists():
                    graphic_path = p
                    break
            
            if graphic_path:
                try:
                    # Draw graphic - fill entire memorial area
                    c.drawImage(
                        str(graphic_path),
                        x_mm * mm, y_mm * mm,
                        width=MEMORIAL_W_MM * mm,
                        height=MEMORIAL_H_MM * mm,
                        preserveAspectRatio=False,  # Stretch to fill
                        lazy=2  # Memory optimization: load image on-demand
                    )
                    print(f"[REGULAR PDF] Successfully embedded graphic for item {idx}: {graphic_path.name}", flush=True)
                except Exception as e:
                    print(f"[REGULAR PDF] Failed to embed graphic: {e}", flush=True)
                    warnings.append(f"GRAPHIC_ERROR: {str(e)}")
            else:
                print(f"[REGULAR PDF] Graphic not found for item {idx}: {gkey}", flush=True)
                warnings.append("GRAPHIC_FILE_NOT_FOUND")
        except Exception as e:
            warnings.append(f"GRAPHIC_ERROR: {str(e)}")
    
    # Add text lines
    l1, l2, l3 = _text_lines_map(item)
    cx_mm = x_mm + (MEMORIAL_W_MM / 2.0)
    
    c.setFillColorRGB(0, 0, 0)
    
    # Line 1 (PDF coords: flip Y from top to bottom)
    if l1:
        c.setFont(FONT_NAME, LINE1_PT)
        y1 = y_mm + (MEMORIAL_H_MM - LINE1_Y_MM)  # Flip: bottom-up coords
        c.drawCentredString(cx_mm * mm, y1 * mm, l1)
    
    # Line 2
    if l2:
        c.setFont(FONT_NAME, LINE2_PT)
        y2 = y_mm + (MEMORIAL_H_MM - LINE2_Y_MM)  # Flip: bottom-up coords
        c.drawCentredString(cx_mm * mm, y2 * mm, l2)
    
    # Line 3 (with wrapping)
    if l3:
        lines3, pt = _wrap_line3(l3)
        c.setFont(FONT_NAME, pt)
        
        # Calculate vertical spacing
        line_spacing_mm = 4.0
        total_height = len(lines3) * line_spacing_mm
        y3_base = y_mm + (MEMORIAL_H_MM - LINE3_Y_MM)  # Flip: bottom-up coords
        start_y = y3_base - (total_height / 2.0)
        
        for i, line in enumerate(lines3):
            y_pos = start_y + (i * line_spacing_mm)
            c.drawCentredString(cx_mm * mm, y_pos * mm, line)


def run(items: List[Any], cfg: dict) -> Tuple[str, str, List[str]]:
    """Process regular stakes batch and generate PDF"""
    job_id = cfg["job_id"]
    out_dir: Path = cfg["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    warnings: List[str] = []
    
    # Filter eligible items
    def _norm(s):
        return (s or "").strip().lower()
    
    eligible: List[Any] = []
    for it in items:
        colour = _norm(getattr(it, "colour", None) or "")
        typ = _norm(getattr(it, "product_type", None) or "")
        deco = _norm(getattr(it, "decoration_type", None) or "")
        if (typ == "regular stake") and (deco == "graphic") and (colour in ALLOWED_COLOURS):
            eligible.append(it)
    
    # Sort by colour priority
    eligible.sort(key=lambda it: COLOUR_PRIORITY.get(_norm(getattr(it, "colour", "")), 99))
    
    # Limit to one bed
    place = eligible[:BATCH_SIZE]
    
    # Create PDF
    date_str = datetime.now().strftime("%Y%m%d")
    pdf_path = out_dir / f"{date_str}_regular_stake_pdf_v1_bed_1.pdf"
    
    c = canvas.Canvas(str(pdf_path), pagesize=(PAGE_W_MM * mm, PAGE_H_MM * mm))
    
    # White background
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, PAGE_W_MM * mm, PAGE_H_MM * mm, fill=1, stroke=0)
    
    # Add memorials
    rows_csv = []
    for idx, item in enumerate(place):
        col = idx % COLS
        row = idx // COLS
        x_mm = X_OFF_MM + col * MEMORIAL_W_MM
        y_mm = Y_OFF_MM + row * MEMORIAL_H_MM
        
        _add_regular_memorial(c, x_mm, y_mm, item, idx, warnings)
        
        # CSV row
        order_ref = getattr(item, "order_ref", "") or ""
        l1, l2, l3 = _text_lines_map(item)
        rows_csv.append({
            "bed": 1,
            "position": idx + 1,
            "order_ref": order_ref,
            "line_1": l1,
            "line_2": l2,
            "line_3": l3,
        })
    
    # Add blue reference marker (bottom-right corner)
    ref_size_mm = 0.1
    ref_x = PAGE_W_MM - ref_size_mm
    ref_y = 0.1
    c.setFillColorRGB(0, 0, 1)
    c.rect(ref_x * mm, ref_y * mm, ref_size_mm * mm, ref_size_mm * mm, fill=1, stroke=0)
    
    c.save()
    
    # Write CSV
    csv_path = out_dir / f"{date_str}_regular_stake_pdf_v1_batch.csv"
    write_batch_csv(rows_csv, csv_path)
    
    # Force garbage collection to free memory
    gc.collect()
    
    # Return URLs
    pdf_url = f"/static/jobs/{job_id}/{pdf_path.name}"
    csv_url = f"/static/jobs/{job_id}/{csv_path.name}"
    
    return pdf_url, csv_url, warnings


# Register this processor
register_batch("regular_stake_pdf_v1", run)
