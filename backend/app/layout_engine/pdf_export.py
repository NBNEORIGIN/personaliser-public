"""
PDF export functionality for SVG layouts.

Uses cairosvg to convert SVG to PDF format.
"""

import io
from typing import Union


def export_svg_to_pdf(svg_string: str) -> bytes:
    """
    Convert SVG string to PDF bytes.
    
    Args:
        svg_string: SVG markup as string
        
    Returns:
        PDF file as bytes
        
    Raises:
        ImportError: If cairosvg is not installed
        Exception: If conversion fails
    """
    try:
        import cairosvg
    except ImportError:
        raise ImportError(
            "cairosvg is required for PDF export. "
            "Install it with: pip install cairosvg"
        )
    
    try:
        # Convert SVG to PDF
        pdf_bytes = cairosvg.svg2pdf(
            bytestring=svg_string.encode('utf-8'),
            write_to=None  # Return bytes instead of writing to file
        )
        
        return pdf_bytes
        
    except Exception as e:
        raise Exception(f"Failed to convert SVG to PDF: {str(e)}")


def export_svg_to_pdf_file(svg_string: str, output_path: str) -> str:
    """
    Convert SVG string to PDF file.
    
    Args:
        svg_string: SVG markup as string
        output_path: Destination file path
        
    Returns:
        Path to generated PDF file
        
    Raises:
        ImportError: If cairosvg is not installed
        Exception: If conversion fails
    """
    try:
        import cairosvg
    except ImportError:
        raise ImportError(
            "cairosvg is required for PDF export. "
            "Install it with: pip install cairosvg"
        )
    
    try:
        # Convert SVG to PDF file
        cairosvg.svg2pdf(
            bytestring=svg_string.encode('utf-8'),
            write_to=output_path
        )
        
        return output_path
        
    except Exception as e:
        raise Exception(f"Failed to convert SVG to PDF: {str(e)}")
