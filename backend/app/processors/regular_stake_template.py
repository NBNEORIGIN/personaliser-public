"""
Regular stakes processor using template engine.

This replaces regular_stake_pdf_v1.py with the new template-driven approach.
"""

from pathlib import Path
from typing import List
import io

from ..layout_engine import (
    REGULAR_STAKE_3X3,
    convert_regular_stakes_order,
    renderPlateSVG,
    export_svg_to_pdf
)


def process_regular_stakes_template(
    items: List[dict],
    output_path: Path,
    format: str = "pdf"
) -> Path:
    """
    Process regular stakes using template engine.
    
    Args:
        items: List of order items with line1, line2, line3, graphics_key
        output_path: Destination file path
        format: Output format ("svg" or "pdf")
        
    Returns:
        Path to generated file
    """
    # Use pre-defined 3x3 template
    template = REGULAR_STAKE_3X3
    
    # Convert order data to content format
    content = convert_regular_stakes_order(items)
    
    # Generate SVG
    svg_output = renderPlateSVG(template, content)
    
    if format == "svg":
        # Save SVG directly
        output_path.write_text(svg_output, encoding="utf-8")
        return output_path
    
    elif format == "pdf":
        # Convert to PDF
        pdf_bytes = export_svg_to_pdf(svg_output)
        output_path.write_bytes(pdf_bytes)
        return output_path
    
    else:
        raise ValueError(f"Unsupported format: {format}")


# Backward compatibility wrapper
def process(items: List[dict], output_path: Path) -> Path:
    """
    Backward compatible process function.
    
    This maintains the same interface as regular_stake_pdf_v1.py
    """
    return process_regular_stakes_template(items, output_path, format="pdf")
