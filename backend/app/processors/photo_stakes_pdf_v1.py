"""
Photo Stakes Processor - PDF Version
Uses ReportLab to generate PDFs with editable text and images.
"""
from __future__ import annotations
from typing import List, Tuple
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
    print(f"[PHOTO PDF] Registered Georgia font from {georgia_path}", flush=True)
else:
    print(f"[PHOTO PDF] WARNING: Georgia font not found at {georgia_path}", flush=True)

# Page and memorial dimensions (matching regular stakes)
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

# Photo-specific dimensions
PHOTO_W_MM = 50.5
PHOTO_H_MM = 68.8
PHOTO_BORDER_MM = 3.65
PHOTO_CORNER_RADIUS_MM = 6.0
PHOTO_LEFT_MARGIN_MM = 7.7

# Text positioning (from memorial top)
TEXT_X_OFFSET_MM = 95.0  # Center of text area
LINE1_Y_MM = 62.0
LINE2_Y_MM = 45.0
LINE3_Y_MM = 28.0

# Text sizing
LINE1_PT = 17
LINE2_PT = 25
LINE3_PT = 13

# Font setup
FONT_NAME = "Georgia"
FONT_NAME_BOLD = "Georgia"  # Using same font for bold (can add Georgia Bold TTF later)


def _text_lines_map(it: IngestItem) -> Tuple[str, str, str]:
    """Extract text lines from IngestItem"""
    mp = {l.id: l.value for l in it.lines}
    return mp.get("line_1", ""), mp.get("line_2", ""), mp.get("line_3", "")


def _add_photo_memorial(c: canvas.Canvas, x_mm: float, y_mm: float, item: IngestItem, idx: int):
    """Add a single photo memorial to the PDF"""
    
    # Draw memorial outline (red rounded rectangle)
    c.setStrokeColorRGB(1, 0, 0)
    c.setLineWidth(0.1 * mm)
    c.roundRect(
        x_mm * mm, y_mm * mm,
        MEMORIAL_W_MM * mm, MEMORIAL_H_MM * mm,
        6 * mm,
        stroke=1, fill=0
    )
    
    # Calculate photo position
    photo_x_mm = x_mm + PHOTO_LEFT_MARGIN_MM
    photo_y_mm = y_mm + (MEMORIAL_H_MM - PHOTO_H_MM) / 2
    
    # Draw black background for photo
    c.setFillColorRGB(0, 0, 0)
    c.roundRect(
        photo_x_mm * mm, photo_y_mm * mm,
        PHOTO_W_MM * mm, PHOTO_H_MM * mm,
        PHOTO_CORNER_RADIUS_MM * mm,
        stroke=0, fill=1
    )
    
    # Embed and add photo if available
    photo_url = getattr(item, 'photo_asset_url', None) or getattr(item, 'photo_url', None)
    photo_id = getattr(item, 'photo_asset_id', None)
    
    print(f"[PHOTO PDF] Item {idx}: photo_url={photo_url}, photo_id={photo_id}", flush=True)
    
    if photo_url:
        # Resolve photo path
        photo_path = None
        if photo_url.startswith('/static/photos/'):
            filename = photo_url.split('/')[-1]
            photo_path = settings.PHOTOS_DIR / filename
            print(f"[PHOTO PDF] Resolved local path: {photo_path}, exists={photo_path.exists()}", flush=True)
        elif photo_id:
            photo_path = settings.PHOTOS_DIR / f"{photo_id}.jpg"
            print(f"[PHOTO PDF] Trying by ID: {photo_path}, exists={photo_path.exists()}", flush=True)
        
        if photo_path and photo_path.exists():
            try:
                # Draw image (ReportLab handles clipping automatically with roundRect mask)
                c.drawImage(
                    str(photo_path),
                    photo_x_mm * mm, photo_y_mm * mm,
                    width=PHOTO_W_MM * mm,
                    height=PHOTO_H_MM * mm,
                    preserveAspectRatio=True,
                    mask='auto'
                )
                print(f"[PHOTO PDF] Successfully embedded photo for item {idx}", flush=True)
            except Exception as e:
                print(f"[PHOTO PDF] Failed to embed photo: {e}", flush=True)
        else:
            print(f"[PHOTO PDF] Photo path not found for item {idx}: {photo_path}", flush=True)
    
    # Draw photo border (black stroke)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(PHOTO_BORDER_MM * mm)
    c.roundRect(
        photo_x_mm * mm, photo_y_mm * mm,
        PHOTO_W_MM * mm, PHOTO_H_MM * mm,
        PHOTO_CORNER_RADIUS_MM * mm,
        stroke=1, fill=0
    )
    
    # Add text lines
    l1, l2, l3 = _text_lines_map(item)
    text_x_mm = x_mm + TEXT_X_OFFSET_MM
    
    c.setFillColorRGB(0, 0, 0)
    
    # Field 1: Top (17pt)
    if l1:
        c.setFont(FONT_NAME, LINE1_PT)
        c.drawCentredString(text_x_mm * mm, (y_mm + LINE1_Y_MM) * mm, l1)
    
    # Field 2: Center (25pt, bold)
    if l2:
        c.setFont(FONT_NAME_BOLD, LINE2_PT)
        c.drawCentredString(text_x_mm * mm, (y_mm + LINE2_Y_MM) * mm, l2)
    
    # Field 3: Bottom (13pt)
    if l3:
        c.setFont(FONT_NAME, LINE3_PT)
        c.drawCentredString(text_x_mm * mm, (y_mm + LINE3_Y_MM) * mm, l3)


def run(items: List[IngestItem], cfg: dict) -> Tuple[str, str, List[str]]:
    """Process photo stakes batch and generate PDF"""
    job_id = cfg["job_id"]
    out_dir: Path = cfg["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Create PDF
    date_str = datetime.now().strftime("%Y%m%d")
    pdf_path = out_dir / f"{date_str}_photo_stakes_pdf_v1_bed_1.pdf"
    
    c = canvas.Canvas(str(pdf_path), pagesize=(PAGE_W_MM * mm, PAGE_H_MM * mm))
    
    # White background
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, PAGE_W_MM * mm, PAGE_H_MM * mm, fill=1, stroke=0)
    
    rows_csv: List[dict] = []
    
    # Layout memorials in centered grid
    for idx, item in enumerate(items):
        if idx >= BATCH_SIZE:
            break
        col = idx % COLS
        row = idx // COLS
        x_mm = X_OFF_MM + col * MEMORIAL_W_MM
        # PDF coordinates are bottom-up, so flip Y
        y_mm = PAGE_H_MM - (Y_OFF_MM + (row + 1) * MEMORIAL_H_MM)
        
        _add_photo_memorial(c, x_mm, y_mm, item, idx)
        
        l1, l2, l3 = _text_lines_map(item)
        photo_url = getattr(item, 'photo_asset_url', None) or getattr(item, 'photo_url', None) or ""
        rows_csv.append({
            "order_ref": getattr(item, 'order_ref', ''),
            "sku": getattr(item, 'sku', '') or "",
            "graphics_key": getattr(item, 'graphics_key', '') or "",
            "colour": getattr(item, 'colour', '') or "",
            "type": getattr(item, 'product_type', '') or "",
            "photo_url": photo_url,
            "line_1": l1,
            "line_2": l2,
            "line_3": l3,
            "cell_row": row,
            "cell_col": col,
        })
    
    # Add reference marker (blue square at bottom-right)
    ref_size_mm = 0.1
    ref_x = PAGE_W_MM - ref_size_mm
    ref_y = 0.1  # Bottom in PDF coordinates
    c.setFillColorRGB(0, 0, 1)
    c.rect(ref_x * mm, ref_y * mm, ref_size_mm * mm, ref_size_mm * mm, fill=1, stroke=0)
    
    c.save()
    
    # Write CSV
    csv_path = out_dir / f"{date_str}_photo_stakes_pdf_v1_batch.csv"
    write_batch_csv(rows_csv, csv_path)
    
    # Force garbage collection to free memory
    gc.collect()
    
    # Return URLs
    pdf_url = f"/static/jobs/{job_id}/{pdf_path.name}"
    csv_url = f"/static/jobs/{job_id}/{csv_path.name}"
    
    return pdf_url, csv_url, []


# Register this processor
register_batch("photo_stakes_pdf_v1", run)
