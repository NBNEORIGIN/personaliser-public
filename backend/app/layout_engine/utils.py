"""
Utility functions for layout engine.
"""

from typing import List
import math


def pt_to_mm(pt: float) -> float:
    """
    Convert points to millimeters.
    
    1 pt = 1/72 inch
    1 inch = 25.4 mm
    Therefore: 1 pt = 25.4/72 mm ≈ 0.3528 mm
    
    Args:
        pt: Size in points
        
    Returns:
        Size in millimeters
    """
    return pt * 25.4 / 72.0


def mm_to_pt(mm: float) -> float:
    """
    Convert millimeters to points.
    
    Args:
        mm: Size in millimeters
        
    Returns:
        Size in points
    """
    return mm * 72.0 / 25.4


def wrap_text(text: str, max_width_mm: float, font_size_pt: float, font_family: str = "Times New Roman") -> List[str]:
    """
    Wrap text to fit within a maximum width.
    
    This is a simplified version that splits on newlines and estimates character width.
    For production, you might want to use a proper text measurement library.
    
    Args:
        text: Text to wrap
        max_width_mm: Maximum width in mm
        font_size_pt: Font size in points
        font_family: Font family name
        
    Returns:
        List of text lines
    """
    # First split on explicit newlines
    lines = text.split('\n')
    
    # For now, return as-is (simple newline splitting)
    # TODO: Implement proper word wrapping based on font metrics
    # This would require measuring actual text width, which is complex without a font library
    
    return lines


def calculate_line_height(font_size_pt: float, line_spacing: float = 1.2) -> float:
    """
    Calculate line height in mm for multiline text.
    
    Args:
        font_size_pt: Font size in points
        line_spacing: Line spacing multiplier (default 1.2 = 120%)
        
    Returns:
        Line height in mm
    """
    return pt_to_mm(font_size_pt) * line_spacing


def escape_xml(text: str) -> str:
    """
    Escape special XML characters in text.
    
    Args:
        text: Text to escape
        
    Returns:
        XML-safe text
    """
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def generate_unique_id(prefix: str, row: int, col: int, element_id: str = "") -> str:
    """
    Generate a unique ID for SVG elements.
    
    Args:
        prefix: ID prefix (e.g., "tile", "clip")
        row: Row index
        col: Column index
        element_id: Optional element identifier
        
    Returns:
        Unique ID string
    """
    if element_id:
        return f"{prefix}-r{row}-c{col}-{element_id}"
    return f"{prefix}-r{row}-c{col}"
