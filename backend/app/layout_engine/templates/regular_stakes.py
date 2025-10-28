"""
Template definition for regular memorial stakes.

This replaces the hardcoded regular_stake_pdf_v1.py processor.
"""

from app.layout_engine.models import (
    TemplateJSON, BedDefinition, BedMargin,
    PartDefinition, TilingDefinition,
    TextElement, ImageElement, GraphicElement
)


def create_regular_stake_template(
    bed_width_mm: float = 480,
    bed_height_mm: float = 330,
    cols: int = 3,
    rows: int = 3
) -> TemplateJSON:
    """
    Create template for regular memorial stakes.
    
    Based on the original regular_stake_pdf_v1.py specifications:
    - Part size: 140mm x 90mm
    - 3 text lines with specific positioning
    - Optional graphic/border
    
    Args:
        bed_width_mm: Bed width in mm
        bed_height_mm: Bed height in mm
        cols: Number of columns
        rows: Number of rows
        
    Returns:
        Template definition
    """
    # Constants from original processor
    PART_WIDTH_MM = 140.0
    PART_HEIGHT_MM = 90.0
    
    # Text positioning (from original)
    LINE1_Y_MM = 20.0  # Top line
    LINE2_Y_MM = 35.0  # Middle line
    LINE3_Y_MM = 50.0  # Bottom line (multiline)
    
    LINE1_PT = 14.0
    LINE2_PT = 12.0
    LINE3_PT = 10.0
    
    # Calculate gaps to center the grid
    total_parts_width = cols * PART_WIDTH_MM
    total_parts_height = rows * PART_HEIGHT_MM
    
    gap_x = (bed_width_mm - total_parts_width) / (cols + 1) if cols > 1 else 10
    gap_y = (bed_height_mm - total_parts_height) / (rows + 1) if rows > 1 else 10
    
    margin_left = gap_x
    margin_top = gap_y
    
    return TemplateJSON(
        bed=BedDefinition(
            width_mm=bed_width_mm,
            height_mm=bed_height_mm,
            margin_mm=BedMargin(left=margin_left, top=margin_top)
        ),
        part=PartDefinition(
            width_mm=PART_WIDTH_MM,
            height_mm=PART_HEIGHT_MM,
            elements=[
                # Line 1 - Top text (e.g., "In loving memory")
                TextElement(
                    type="text",
                    id="line1",
                    x_mm=10,
                    y_mm=LINE1_Y_MM,
                    w_mm=120,
                    h_mm=10,
                    font_family="Georgia",
                    font_size_pt=LINE1_PT,
                    text_align="center",
                    multiline=False,
                    editable=True
                ),
                # Line 2 - Middle text (e.g., name)
                TextElement(
                    type="text",
                    id="line2",
                    x_mm=10,
                    y_mm=LINE2_Y_MM,
                    w_mm=120,
                    h_mm=10,
                    font_family="Georgia",
                    font_size_pt=LINE2_PT,
                    text_align="center",
                    multiline=False,
                    editable=True
                ),
                # Line 3 - Bottom text (multiline, e.g., dates/message)
                TextElement(
                    type="text",
                    id="line3",
                    x_mm=10,
                    y_mm=LINE3_Y_MM,
                    w_mm=120,
                    h_mm=30,
                    font_family="Georgia",
                    font_size_pt=LINE3_PT,
                    text_align="center",
                    multiline=True,
                    editable=True
                ),
                # Optional graphic/border (if provided)
                GraphicElement(
                    type="graphic",
                    id="graphic",
                    x_mm=0,
                    y_mm=0,
                    w_mm=PART_WIDTH_MM,
                    h_mm=PART_HEIGHT_MM,
                    source="",  # Will be set from content
                    editable=False
                )
            ]
        ),
        tiling=TilingDefinition(
            cols=cols,
            rows=rows,
            gap_x_mm=gap_x,
            gap_y_mm=gap_y,
            offset_x_mm=0,
            offset_y_mm=0
        )
    )


# Pre-defined templates for common configurations
REGULAR_STAKE_3X3 = create_regular_stake_template(480, 330, 3, 3)
REGULAR_STAKE_4X3 = create_regular_stake_template(600, 330, 4, 3)
REGULAR_STAKE_3X4 = create_regular_stake_template(480, 440, 3, 4)
