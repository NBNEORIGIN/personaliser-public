from __future__ import annotations
from typing import List, Tuple
from pathlib import Path
from datetime import datetime
import svgwrite
import base64

from ..models import IngestItem
from ..settings import settings
from ..utils import storage
from .registry import register_batch
from .base import write_batch_csv

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

# Photo-specific dimensions (from working example)
PHOTO_W_MM = 50.5  # Photo frame width
PHOTO_H_MM = 68.8  # Photo frame height
PHOTO_CLIP_W_MM = 50.378  # Black background clip width
PHOTO_CLIP_H_MM = 68.901  # Black background clip height
PHOTO_BORDER_STROKE_MM = 3.65  # Border stroke width
PHOTO_CORNER_RADIUS_MM = 6.0
PHOTO_LEFT_MARGIN_MM = 7.7
TEXT_RIGHT_SHIFT_MM = 30.0  # Space between photo and text

# Text sizing (matching regular stakes)
PT_TO_MM = 0.2645833333  # Legacy factor from regular stakes
LINE1_PT = 17
LINE2_PT = 25
LINE3_PT = 13


def _embed_image(path: Path) -> str | None:
    """Embed image as base64 data URI"""
    try:
        with path.open('rb') as f:
            encoded = base64.b64encode(f.read()).decode('ascii')
            return f'data:image/jpeg;base64,{encoded}'
    except Exception as e:
        print(f"Failed to embed image {path}: {e}")
        return None


def _text_lines_map(it: IngestItem) -> Tuple[str, str, str]:
    """Extract text lines from IngestItem"""
    mp = {l.id: l.value for l in it.lines}
    return mp.get("line_1", ""), mp.get("line_2", ""), mp.get("line_3", "")


def _add_photo_memorial(dwg: svgwrite.Drawing, x_mm: float, y_mm: float, item: IngestItem, idx: int):
    """Add a single photo memorial to the SVG"""
    # Calculate positions (matching working example)
    clip_x = x_mm + PHOTO_LEFT_MARGIN_MM
    clip_y = y_mm + (MEMORIAL_H_MM - PHOTO_CLIP_H_MM) / 2
    
    frame_x = x_mm + PHOTO_LEFT_MARGIN_MM
    frame_y = y_mm + (MEMORIAL_H_MM - PHOTO_H_MM) / 2
    
    # Calculate text center position
    text_x = frame_x + PHOTO_W_MM + TEXT_RIGHT_SHIFT_MM
    text_area_width = MEMORIAL_W_MM - (text_x - x_mm) - TEXT_RIGHT_SHIFT_MM
    text_center_x = text_x + text_area_width / 2 - (PHOTO_CLIP_W_MM / 2)
    
    # Add memorial outline (red rounded rectangle)
    dwg.add(dwg.rect(
        insert=(f"{x_mm}mm", f"{y_mm}mm"),
        size=(f"{MEMORIAL_W_MM}mm", f"{MEMORIAL_H_MM}mm"),
        rx=f"{6}mm",
        ry=f"{6}mm",
        fill='none',
        stroke='red',
        stroke_width=f"{0.1}mm"
    ))
    
    # Add black background clip (filled black rounded rectangle)
    dwg.add(dwg.rect(
        insert=(f"{clip_x}mm", f"{clip_y}mm"),
        size=(f"{PHOTO_CLIP_W_MM}mm", f"{PHOTO_CLIP_H_MM}mm"),
        rx=f"{PHOTO_CORNER_RADIUS_MM}mm",
        ry=f"{PHOTO_CORNER_RADIUS_MM}mm",
        fill='black'
    ))
    
    # Create clip path for photo
    clip_id = f'clip_{idx}'
    clip_path = dwg.defs.add(dwg.clipPath(id=clip_id))
    clip_path.add(dwg.rect(
        insert=(f"{clip_x}mm", f"{clip_y}mm"),
        size=(f"{PHOTO_CLIP_W_MM}mm", f"{PHOTO_CLIP_H_MM}mm"),
        rx=f"{PHOTO_CORNER_RADIUS_MM}mm",
        ry=f"{PHOTO_CORNER_RADIUS_MM}mm"
    ))
    
    # Add photo border (black stroke)
    dwg.add(dwg.rect(
        insert=(f"{frame_x}mm", f"{frame_y}mm"),
        size=(f"{PHOTO_W_MM}mm", f"{PHOTO_H_MM}mm"),
        rx=f"{PHOTO_CORNER_RADIUS_MM}mm",
        ry=f"{PHOTO_CORNER_RADIUS_MM}mm",
        fill='none',
        stroke='black',
        stroke_width=f"{PHOTO_BORDER_STROKE_MM}mm"
    ))
    
    # Embed and add photo if available
    photo_url = getattr(item, 'photo_asset_url', None) or getattr(item, 'photo_url', None)
    photo_id = getattr(item, 'photo_asset_id', None)
    
    print(f"[PHOTO] Item {idx}: photo_url={photo_url}, photo_id={photo_id}", flush=True)
    
    if photo_url:
        # Resolve photo path
        photo_path = None
        if photo_url.startswith('/static/photos/'):
            # Local photo from storage
            filename = photo_url.split('/')[-1]
            photo_path = settings.PHOTOS_DIR / filename
            print(f"[PHOTO] Resolved local path: {photo_path}, exists={photo_path.exists()}", flush=True)
        elif photo_id:
            # Try to find by ID
            photo_path = settings.PHOTOS_DIR / f"{photo_id}.jpg"
            print(f"[PHOTO] Trying by ID: {photo_path}, exists={photo_path.exists()}", flush=True)
        
        if photo_path and photo_path.exists():
            photo_data = _embed_image(photo_path)
            if photo_data:
                print(f"[PHOTO] Successfully embedded photo for item {idx}", flush=True)
                photo = dwg.image(
                    href=photo_data,
                    insert=(f"{frame_x}mm", f"{frame_y}mm"),
                    size=(f"{PHOTO_W_MM}mm", f"{PHOTO_H_MM}mm"),
                    clip_path=f'url(#{clip_id})'
                )
                dwg.add(photo)
            else:
                print(f"[PHOTO] Failed to embed image data for item {idx}", flush=True)
        else:
            print(f"[PHOTO] Photo path not found for item {idx}: {photo_path}", flush=True)
    
    # Add text lines (matching working example positions and sizes)
    l1, l2, l3 = _text_lines_map(item)
    
    # Field 1: Top (17pt, 28mm from top)
    if l1:
        dwg.add(dwg.text(
            l1,
            insert=(f"{text_center_x}mm", f"{y_mm + 28}mm"),
            text_anchor="middle",
            font_family="Georgia, serif",
            font_size=f"{LINE1_PT * PT_TO_MM}mm",
            fill="black"
        ))
    
    # Field 2: Center (25pt, 45mm from top)
    if l2:
        dwg.add(dwg.text(
            l2,
            insert=(f"{text_center_x}mm", f"{y_mm + 45}mm"),
            text_anchor="middle",
            font_family="Georgia, serif",
            font_size=f"{LINE2_PT * PT_TO_MM}mm",
            fill="black"
        ))
    
    # Field 3: Bottom (13pt, 62mm from top)
    if l3:
        dwg.add(dwg.text(
            l3,
            insert=(f"{text_center_x}mm", f"{y_mm + 62}mm"),
            text_anchor="middle",
            font_family="Georgia, serif",
            font_size=f"{LINE3_PT * PT_TO_MM}mm",
            fill="black"
        ))


def run(items: List[IngestItem], cfg: dict) -> Tuple[str, str, List[str]]:
    """Process photo stakes batch"""
    job_id = cfg["job_id"]
    out_dir: Path = cfg["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Create SVG document
    dwg = svgwrite.Drawing(
        size=(f"{PAGE_W_MM}mm", f"{PAGE_H_MM}mm"),
        viewBox=f"0 0 {PAGE_W_MM} {PAGE_H_MM}"
    )
    
    rows_csv: List[dict] = []
    
    # Process up to 3 items per bed
    for idx, item in enumerate(items):
        if idx >= BATCH_SIZE:
            break
        col = idx % COLS
        row = idx // COLS
        x_mm = X_OFF_MM + col * MEMORIAL_W_MM
        y_mm = Y_OFF_MM + row * MEMORIAL_H_MM
        _add_photo_memorial(dwg, x_mm, y_mm, item, idx)
        
        l1, l2, l3 = _text_lines_map(item)
        photo_url = getattr(item, 'photo_asset_url', None) or getattr(item, 'photo_url', None) or ""
        rows_csv.append({
            "order_ref": getattr(item, 'order_ref', ''),
            "sku": getattr(item, 'sku', '') or "",
            "graphics_key": getattr(item, 'graphics_key', '') or "",
            "colour": getattr(item, 'colour', '') or "",
            "type": getattr(item, 'product_type', '') or "",
            "decoration": getattr(item, 'decoration_type', '') or "",
            "theme": getattr(item, 'theme', '') or "",
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
    ref_y = PAGE_H_MM - 0.1 - ref_size_mm
    dwg.add(dwg.rect(
        insert=(f"{ref_x}mm", f"{ref_y}mm"),
        size=(f"{ref_size_mm}mm", f"{ref_size_mm}mm"),
        fill='blue'
    ))
    
    # Save with date and processor name
    date_str = datetime.now().strftime("%Y%m%d")
    svg_path = out_dir / f"{date_str}_photo_stakes_v1_bed_1.svg"
    dwg.saveas(svg_path)
    
    csv_path = out_dir / f"{date_str}_photo_stakes_v1_batch.csv"
    write_batch_csv(rows_csv, csv_path)
    
    # Upload to storage
    svg_url = storage.put_artifact(job_id, svg_path)
    csv_url = storage.put_artifact(job_id, csv_path)
    
    return svg_url, csv_url, []


# Register the processor
register_batch("photo_stakes_v1", run)
