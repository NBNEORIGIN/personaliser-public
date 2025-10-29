"""
Data models for template-driven layout engine.

All measurements are in millimeters (mm).
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# ELEMENT DEFINITIONS
# ============================================================================

class ClipShape(BaseModel):
    """Defines clipping shape for images."""
    kind: Literal["rounded_rect"] = "rounded_rect"
    radius_mm: float = Field(ge=0, description="Corner radius in mm")


class BaseElement(BaseModel):
    """Base class for all layout elements."""
    type: str
    id: str = Field(description="Unique identifier for this element")
    x_mm: float = Field(description="X position in mm (relative to part origin or anchor)")
    y_mm: float = Field(description="Y position in mm (relative to part origin or anchor)")
    w_mm: float = Field(gt=0, description="Width in mm")
    h_mm: float = Field(gt=0, description="Height in mm")
    editable: bool = Field(default=True, description="Whether element can be edited in final output")
    anchor_to: Optional[str] = Field(default=None, description="ID of element to position relative to")
    anchor_point: Literal["top", "bottom", "left", "right", "center"] = Field(default="top", description="Which edge/point to anchor to")


class TextElement(BaseElement):
    """Text element definition."""
    type: Literal["text"] = "text"
    font_family: str = Field(default="Times New Roman")
    font_size_pt: float = Field(gt=0, description="Font size in points")
    text_align: Literal["left", "center", "right"] = Field(default="center")
    multiline: bool = Field(default=False, description="Whether text can wrap to multiple lines")


class ImageElement(BaseElement):
    """Image/photo placeholder element."""
    type: Literal["image"] = "image"
    fit: Literal["cover", "contain"] = Field(default="cover", description="How image fits in box")
    clip_shape: Optional[ClipShape] = Field(default=None, description="Optional clipping shape")
    frame_source: Optional[str] = Field(default=None, description="Optional frame/border SVG to overlay on top")


class GraphicElement(BaseElement):
    """Static graphic/vector element (e.g., borders, frames)."""
    type: Literal["graphic"] = "graphic"
    source: str = Field(description="Path to SVG file or graphic resource")


# Union type for all elements
Element = TextElement | ImageElement | GraphicElement


# ============================================================================
# TEMPLATE DEFINITION
# ============================================================================

class BedMargin(BaseModel):
    """Bed margin definition."""
    left: float = Field(default=0, ge=0, description="Left margin in mm")
    top: float = Field(default=0, ge=0, description="Top margin in mm")


class BedDefinition(BaseModel):
    """Physical bed/plate dimensions."""
    width_mm: float = Field(gt=0, description="Bed width in mm")
    height_mm: float = Field(gt=0, description="Bed height in mm")
    margin_mm: BedMargin = Field(default_factory=BedMargin, description="Bed margins")
    origin_marker: bool = Field(default=True, description="Add 0.1mm origin marker at bottom-left")
    origin_x_mm: float = Field(default=0, description="Origin X position in mm")
    origin_y_mm: float = Field(default=0, description="Origin Y position in mm")


class PartDefinition(BaseModel):
    """Individual part/item definition."""
    width_mm: float = Field(gt=0, description="Part width in mm")
    height_mm: float = Field(gt=0, description="Part height in mm")
    elements: List[Element] = Field(default_factory=list, description="Elements within the part")


class TilingDefinition(BaseModel):
    """Tiling/grid layout definition."""
    cols: int = Field(gt=0, description="Number of columns")
    rows: int = Field(gt=0, description="Number of rows")
    gap_x_mm: float = Field(default=0, ge=0, description="Horizontal gap between parts in mm")
    gap_y_mm: float = Field(default=0, ge=0, description="Vertical gap between parts in mm")
    offset_x_mm: float = Field(default=0, description="Horizontal offset from margin in mm")
    offset_y_mm: float = Field(default=0, description="Vertical offset from margin in mm")


class TemplateJSON(BaseModel):
    """Complete template definition for a product layout."""
    bed: BedDefinition
    part: PartDefinition
    tiling: TilingDefinition


# ============================================================================
# CONTENT PAYLOAD
# ============================================================================

class PhotoContent(BaseModel):
    """Photo content with transform parameters."""
    photo_id: Optional[str] = Field(default=None, description="Photo identifier")
    file_url: str = Field(description="URL or path to photo file")
    scale: float = Field(default=1.0, ge=0.1, le=5.0, description="Scale factor (1.0 = 100%)")
    offset_x_mm: float = Field(default=0, description="Horizontal offset in mm")
    offset_y_mm: float = Field(default=0, description="Vertical offset in mm")


class SlotContent(BaseModel):
    """Content for a single slot/tile on the bed."""
    slot_index: int = Field(ge=0, description="Slot position (row-major order)")
    
    # Dynamic content fields - keys match element IDs from template
    # Using model_extra to allow arbitrary fields
    model_config = {"extra": "allow"}
    
    def get_content(self, element_id: str) -> Optional[str | PhotoContent | Dict[str, Any]]:
        """Get content for a specific element ID."""
        return getattr(self, element_id, None)


class ContentJSON(BaseModel):
    """Content payload for all slots on a bed."""
    slots: List[SlotContent] = Field(default_factory=list, description="Content for each slot")
    
    def get_slot(self, slot_index: int) -> Optional[SlotContent]:
        """Get content for a specific slot index."""
        for slot in self.slots:
            if slot.slot_index == slot_index:
                return slot
        return None
