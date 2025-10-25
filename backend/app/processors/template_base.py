"""
Template-based processor system.

This module provides a base class for processors that use pre-designed templates
with placeholders for text and images. This approach separates design from code,
making it easier to maintain and update layouts.
"""
from __future__ import annotations
from typing import List, Tuple, Dict, Any
from pathlib import Path
import json

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from PIL import Image

from ..models import IngestItem


class TemplateProcessor:
    """Base class for template-based processors"""
    
    def __init__(self, template_config: Dict[str, Any]):
        """
        Initialize with template configuration.
        
        Args:
            template_config: Dict containing:
                - page_width_mm: Page width in mm
                - page_height_mm: Page height in mm
                - memorial_width_mm: Memorial width in mm
                - memorial_height_mm: Memorial height in mm
                - cols: Number of columns
                - rows: Number of rows
                - x_offset_mm: X offset for grid
                - y_offset_mm: Y offset for grid
                - text_fields: List of text field configs
                - image_fields: List of image field configs
        """
        self.config = template_config
        
    def create_pdf(self, items: List[IngestItem], output_path: Path) -> None:
        """Create PDF from items using template configuration"""
        c = canvas.Canvas(str(output_path), pagesize=(
            self.config['page_width_mm'] * mm,
            self.config['page_height_mm'] * mm
        ))
        
        # Set white background
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, 
               self.config['page_width_mm'] * mm, 
               self.config['page_height_mm'] * mm, 
               fill=1, stroke=0)
        
        # Process items in grid
        batch_size = self.config['cols'] * self.config['rows']
        for idx, item in enumerate(items[:batch_size]):
            col = idx % self.config['cols']
            row = idx // self.config['cols']
            
            x_mm = self.config['x_offset_mm'] + col * self.config['memorial_width_mm']
            # PDF coordinates are bottom-up, so we need to flip Y
            y_mm = self.config['page_height_mm'] - (
                self.config['y_offset_mm'] + 
                (row + 1) * self.config['memorial_height_mm']
            )
            
            self._render_memorial(c, item, x_mm, y_mm)
        
        c.save()
    
    def _render_memorial(self, c: canvas.Canvas, item: IngestItem, x_mm: float, y_mm: float) -> None:
        """Render a single memorial at the given position"""
        # Draw memorial outline (red rounded rectangle)
        c.setStrokeColorRGB(1, 0, 0)
        c.setLineWidth(0.1 * mm)
        c.roundRect(
            x_mm * mm, y_mm * mm,
            self.config['memorial_width_mm'] * mm,
            self.config['memorial_height_mm'] * mm,
            6 * mm,
            stroke=1, fill=0
        )
        
        # Render image fields
        for img_field in self.config.get('image_fields', []):
            self._render_image(c, item, x_mm, y_mm, img_field)
        
        # Render text fields
        for text_field in self.config.get('text_fields', []):
            self._render_text(c, item, x_mm, y_mm, text_field)
    
    def _render_image(self, c: canvas.Canvas, item: IngestItem, 
                      x_mm: float, y_mm: float, field_config: Dict) -> None:
        """Render an image field"""
        # Get image path from item
        photo_url = getattr(item, 'photo_asset_url', None) or getattr(item, 'photo_url', None)
        if not photo_url:
            return
        
        # Resolve path
        from ..settings import settings
        if photo_url.startswith('/static/photos/'):
            filename = photo_url.split('/')[-1]
            photo_path = settings.PHOTOS_DIR / filename
            
            if photo_path.exists():
                # Calculate position
                img_x = (x_mm + field_config['x_offset_mm']) * mm
                img_y = (y_mm + field_config['y_offset_mm']) * mm
                img_w = field_config['width_mm'] * mm
                img_h = field_config['height_mm'] * mm
                
                # Draw black background
                c.setFillColorRGB(0, 0, 0)
                c.roundRect(img_x, img_y, img_w, img_h, 
                           field_config.get('corner_radius_mm', 6) * mm,
                           stroke=0, fill=1)
                
                # Draw image
                try:
                    c.drawImage(str(photo_path), img_x, img_y, 
                               width=img_w, height=img_h, 
                               mask='auto', preserveAspectRatio=True)
                except Exception as e:
                    print(f"Failed to draw image: {e}")
                
                # Draw border
                c.setStrokeColorRGB(0, 0, 0)
                c.setLineWidth(field_config.get('border_width_mm', 3.65) * mm)
                c.roundRect(img_x, img_y, img_w, img_h,
                           field_config.get('corner_radius_mm', 6) * mm,
                           stroke=1, fill=0)
    
    def _render_text(self, c: canvas.Canvas, item: IngestItem,
                     x_mm: float, y_mm: float, field_config: Dict) -> None:
        """Render a text field"""
        # Get text from item
        lines_map = {l.id: l.value for l in item.lines}
        text = lines_map.get(field_config['line_id'], '')
        
        if not text:
            return
        
        # Calculate position
        text_x = (x_mm + field_config['x_offset_mm']) * mm
        text_y = (y_mm + field_config['y_offset_mm']) * mm
        
        # Set font
        c.setFont(field_config.get('font', 'Helvetica'), 
                 field_config['font_size_pt'])
        c.setFillColorRGB(0, 0, 0)
        
        # Draw text
        if field_config.get('align', 'center') == 'center':
            c.drawCentredString(text_x, text_y, text)
        elif field_config['align'] == 'right':
            c.drawRightString(text_x, text_y, text)
        else:
            c.drawString(text_x, text_y, text)


def load_template(template_path: Path) -> Dict[str, Any]:
    """Load template configuration from JSON file"""
    with open(template_path, 'r') as f:
        return json.load(f)
