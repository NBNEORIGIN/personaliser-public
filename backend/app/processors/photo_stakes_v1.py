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

# Bed and memorial dimensions (same as regular stakes)
BED_W_MM = 480.0
BED_H_MM = 290.0
MEMORIAL_W_MM = 140.0
MEMORIAL_H_MM = 75.0
COLS = 3

# Photo-specific dimensions
PHOTO_BORDER_MM = 2.5  # Black border around photo
PHOTO_INNER_W_MM = 50.5 - (2 * PHOTO_BORDER_MM)  # Photo display area
PHOTO_INNER_H_MM = 68.8 - (2 * PHOTO_BORDER_MM)
PHOTO_FRAME_W_MM = 50.5  # Outer frame including border
PHOTO_FRAME_H_MM = 68.8
PHOTO_CORNER_RADIUS_MM = 6.0
PHOTO_LEFT_MARGIN_MM = 7.7
TEXT_LEFT_MARGIN_MM = 5.0  # Space between photo and text
TEXT_RIGHT_MARGIN_MM = 5.0  # Space from right edge

# Conversion factor
PX_PER_MM = 3.78
PT_TO_MM = 0.3528


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


def _wrap_text(text: str, max_chars_per_line: int = 12) -> List[str]:
    """Wrap text to fit within memorial, breaking at word boundaries"""
    if not text:
        return []
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        # +1 for space
        if current_length + word_length + len(current_line) > max_chars_per_line and current_line:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length
        else:
            current_line.append(word)
            current_length += word_length
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def _add_photo_memorial(dwg: svgwrite.Drawing, x_mm: float, y_mm: float, item: IngestItem, idx: int):
    """Add a single photo memorial to the SVG"""
    # Calculate photo frame position (centered vertically)
    frame_x = x_mm + PHOTO_LEFT_MARGIN_MM
    frame_y = y_mm + (MEMORIAL_H_MM - PHOTO_FRAME_H_MM) / 2
    
    # Calculate inner photo position (with border)
    photo_x = frame_x + PHOTO_BORDER_MM
    photo_y = frame_y + PHOTO_BORDER_MM
    
    # Calculate text area (right side of memorial)
    text_left_x = frame_x + PHOTO_FRAME_W_MM + TEXT_LEFT_MARGIN_MM
    text_right_x = x_mm + MEMORIAL_W_MM - TEXT_RIGHT_MARGIN_MM
    text_width_mm = text_right_x - text_left_x
    text_center_x = (text_left_x + text_right_x) / 2
    
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
    
    # Add black border frame (filled black rounded rectangle)
    dwg.add(dwg.rect(
        insert=(f"{frame_x}mm", f"{frame_y}mm"),
        size=(f"{PHOTO_FRAME_W_MM}mm", f"{PHOTO_FRAME_H_MM}mm"),
        rx=f"{PHOTO_CORNER_RADIUS_MM}mm",
        ry=f"{PHOTO_CORNER_RADIUS_MM}mm",
        fill='black'
    ))
    
    # Create clip path for inner photo area
    clip_id = f'clip_{idx}'
    inner_radius = max(0, PHOTO_CORNER_RADIUS_MM - PHOTO_BORDER_MM)
    clip_path = dwg.defs.add(dwg.clipPath(id=clip_id))
    clip_path.add(dwg.rect(
        insert=(f"{photo_x}mm", f"{photo_y}mm"),
        size=(f"{PHOTO_INNER_W_MM}mm", f"{PHOTO_INNER_H_MM}mm"),
        rx=f"{inner_radius}mm",
        ry=f"{inner_radius}mm"
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
                    insert=(f"{photo_x}mm", f"{photo_y}mm"),
                    size=(f"{PHOTO_INNER_W_MM}mm", f"{PHOTO_INNER_H_MM}mm"),
                    clip_path=f'url(#{clip_id})'
                )
                dwg.add(photo)
            else:
                print(f"[PHOTO] Failed to embed image data for item {idx}", flush=True)
        else:
            print(f"[PHOTO] Photo path not found for item {idx}: {photo_path}", flush=True)
    
    # Add text lines with wrapping
    l1, l2, l3 = _text_lines_map(item)
    
    # Field 1: Top right (small, near top)
    if l1:
        wrapped_l1 = _wrap_text(l1, max_chars_per_line=12)
        start_y = y_mm + 12
        line_height_mm = 3.5
        for i, line in enumerate(wrapped_l1):
            dwg.add(dwg.text(
                line,
                insert=(f"{text_center_x}mm", f"{start_y + i * line_height_mm}mm"),
                text_anchor="middle",
                dominant_baseline="middle",
                font_family="Georgia, serif",
                font_size="9pt",
                font_weight="bold",
                fill="black"
            ))
    
    # Field 2: Center right (larger, centered)
    if l2:
        wrapped_l2 = _wrap_text(l2, max_chars_per_line=10)
        total_height = len(wrapped_l2) * 4.5
        start_y = y_mm + (MEMORIAL_H_MM / 2) - (total_height / 2) + 2
        line_height_mm = 4.5
        for i, line in enumerate(wrapped_l2):
            dwg.add(dwg.text(
                line,
                insert=(f"{text_center_x}mm", f"{start_y + i * line_height_mm}mm"),
                text_anchor="middle",
                dominant_baseline="middle",
                font_family="Georgia, serif",
                font_size="12pt",
                font_weight="bold",
                fill="black"
            ))
    
    # Field 3: Bottom right (small, near bottom)
    if l3:
        wrapped_l3 = _wrap_text(l3, max_chars_per_line=14)
        start_y = y_mm + MEMORIAL_H_MM - 8 - (len(wrapped_l3) - 1) * 3
        line_height_mm = 3
        for i, line in enumerate(wrapped_l3):
            dwg.add(dwg.text(
                line,
                insert=(f"{text_center_x}mm", f"{start_y + i * line_height_mm}mm"),
                text_anchor="middle",
                dominant_baseline="middle",
                font_family="Georgia, serif",
                font_size="7pt",
                fill="black"
            ))


def run(items: List[IngestItem], cfg: dict) -> Tuple[str, str, List[str]]:
    """Process photo stakes batch"""
    job_id = cfg["job_id"]
    out_dir: Path = cfg["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Create SVG document
    dwg = svgwrite.Drawing(
        size=(f"{BED_W_MM}mm", f"{BED_H_MM}mm"),
        profile="full"
    )
    
    rows_csv: List[dict] = []
    
    # Process up to 3 items per bed
    for idx, item in enumerate(items[:3]):
        col = idx % COLS
        row = idx // COLS
        
        x_mm = col * MEMORIAL_W_MM
        y_mm = row * MEMORIAL_H_MM
        
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
    ref_x = BED_W_MM - ref_size_mm
    ref_y = 289.8 - 0.011 - ref_size_mm
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
