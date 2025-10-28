"""
Template-driven print plate layout engine.

This module replaces hardcoded per-product processors with a flexible
template system that can handle any bed size, part size, and element layout.
"""

from .models import TemplateJSON, ContentJSON
from .renderer import renderPlateSVG, exportPDF

__all__ = [
    "TemplateJSON",
    "ContentJSON",
    "renderPlateSVG",
    "exportPDF",
]
