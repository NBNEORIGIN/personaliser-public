"""
Template-driven print plate layout engine.

This module replaces hardcoded per-product processors with a flexible
template system that can handle any bed size, part size, and element layout.
"""

from .models import TemplateJSON, ContentJSON
from .renderer import renderPlateSVG
from .pdf_export import export_svg_to_pdf, export_svg_to_pdf_file
from .converters import convert_regular_stakes_order, convert_photo_stakes_order
from .templates import (
    create_regular_stake_template,
    REGULAR_STAKE_3X3,
    REGULAR_STAKE_4X3,
    REGULAR_STAKE_3X4
)

__all__ = [
    "TemplateJSON",
    "ContentJSON",
    "renderPlateSVG",
    "export_svg_to_pdf",
    "export_svg_to_pdf_file",
    "convert_regular_stakes_order",
    "convert_photo_stakes_order",
    "create_regular_stake_template",
    "REGULAR_STAKE_3X3",
    "REGULAR_STAKE_4X3",
    "REGULAR_STAKE_3X4",
]
