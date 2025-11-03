"""
SVG renderer for template-driven layout engine.

Generates editable SVG output with live text, images, and graphics.
"""

import re
from pathlib import Path
from typing import Optional
from .models import (
    TemplateJSON, ContentJSON, SlotContent, PhotoContent,
    TextElement, ImageElement, GraphicElement, Element
)
from .utils import (
    pt_to_mm, wrap_text, calculate_line_height,
    escape_xml, generate_unique_id
)


def generate_inline_frame(frame_type: str, width_mm: float, height_mm: float, radius_mm: float = 0, border_width_mm: float = None) -> str:
    """
    Generate inline SVG frame/border based on frame type.
    
    Args:
        frame_type: Type of frame ('simple-gold', 'simple-silver', 'simple-black', 'ornate-gold')
        width_mm: Width in mm
        height_mm: Height in mm
        radius_mm: Corner radius in mm
        border_width_mm: Border width in mm (overrides default)
        
    Returns:
        SVG markup string for the frame
    """
    # Color and style mapping
    frame_styles = {
        'simple-gold': {'stroke': '#FFD700', 'stroke-width': '1.5', 'fill': 'none'},
        'simple-silver': {'stroke': '#C0C0C0', 'stroke-width': '1.5', 'fill': 'none'},
        'simple-black': {'stroke': '#000000', 'stroke-width': '1', 'fill': 'none'},
        'ornate-gold': {'stroke': '#FFD700', 'stroke-width': '2', 'fill': 'none', 'ornate': True}
    }
    
    # Override stroke-width if border_width_mm provided
    if border_width_mm is not None:
        for style in frame_styles.values():
            style['stroke-width'] = str(border_width_mm)
    
    style = frame_styles.get(frame_type, frame_styles['simple-gold'])
    
    if style.get('ornate'):
        # Ornate frame with double border
        return (
            f'<g id="frame">'
            f'<rect x="0" y="0" width="{width_mm}" height="{height_mm}" '
            f'rx="{radius_mm}" ry="{radius_mm}" '
            f'fill="none" stroke="{style["stroke"]}" stroke-width="{style["stroke-width"]}" />'
            f'<rect x="2" y="2" width="{width_mm-4}" height="{height_mm-4}" '
            f'rx="{max(0, radius_mm-2)}" ry="{max(0, radius_mm-2)}" '
            f'fill="none" stroke="{style["stroke"]}" stroke-width="0.5" opacity="0.6" />'
            f'</g>'
        )
    else:
        # Simple border
        return (
            f'<rect id="frame" x="0" y="0" width="{width_mm}" height="{height_mm}" '
            f'rx="{radius_mm}" ry="{radius_mm}" '
            f'fill="{style["fill"]}" stroke="{style["stroke"]}" stroke-width="{style["stroke-width"]}" />'
        )


def render_text_element(
    element: TextElement,
    content: str,
    row: int,
    col: int
) -> str:
    """
    Render a text element as SVG <text> with live editable text.
    
    Args:
        element: Text element definition
        content: Text content to render
        row: Row index for ID generation
        col: Column index for ID generation
        
    Returns:
        SVG markup string
    """
    if not content:
        content = ""
    
    # Determine text anchor based on alignment
    text_anchor_map = {
        "left": "start",
        "center": "middle",
        "right": "end"
    }
    text_anchor = text_anchor_map.get(element.text_align, "middle")
    
    # Calculate x position based on alignment
    if element.text_align == "center":
        text_x = element.x_mm + element.w_mm / 2
    elif element.text_align == "right":
        text_x = element.x_mm + element.w_mm
    else:  # left
        text_x = element.x_mm
    
    # Calculate baseline y position (top of box + font size)
    font_size_mm = pt_to_mm(element.font_size_pt)
    baseline_y = element.y_mm + font_size_mm
    
    # Generate unique ID
    element_id = generate_unique_id("text", row, col, element.id)
    
    # Build SVG
    svg_parts = []
    svg_parts.append(
        f'<text id="{element_id}" '
        f'x="{text_x}" y="{baseline_y}" '
        f'font-family="{escape_xml(element.font_family)}" '
        f'font-size="{element.font_size_pt}pt" '
        f'text-anchor="{text_anchor}" '
        f'fill="black">'
    )
    
    if element.multiline:
        # Split text into lines
        lines = wrap_text(content, element.w_mm, element.font_size_pt, element.font_family)
        line_height = calculate_line_height(element.font_size_pt)
        
        for i, line in enumerate(lines):
            dy = 0 if i == 0 else line_height
            svg_parts.append(
                f'<tspan x="{text_x}" dy="{dy}">{escape_xml(line)}</tspan>'
            )
    else:
        # Single line
        svg_parts.append(f'{escape_xml(content)}')
    
    svg_parts.append('</text>')
    
    return '\n'.join(svg_parts)


def render_image_element(
    element: ImageElement,
    content: Optional[str | PhotoContent | dict],
    row: int,
    col: int
) -> str:
    """
    Render an image element as SVG <image> with optional clipping, transforms, and frame overlay.
    
    Args:
        element: Image element definition
        content: Image path string, PhotoContent object, or dict with photo data
        row: Row index for ID generation
        col: Column index for ID generation
        
    Returns:
        SVG markup string
    """
    # Parse content to extract image path and transform
    image_path = None
    scale = 1.0
    offset_x_mm = 0.0
    offset_y_mm = 0.0
    
    if isinstance(content, PhotoContent):
        image_path = content.file_url
        scale = content.scale
        offset_x_mm = content.offset_x_mm
        offset_y_mm = content.offset_y_mm
    elif isinstance(content, dict):
        image_path = content.get('file_url') or content.get('photo_url')
        scale = content.get('scale', 1.0)
        offset_x_mm = content.get('offset_x_mm', 0.0)
        offset_y_mm = content.get('offset_y_mm', 0.0)
        print(f"[IMAGE] Dict content: {content}", flush=True)
        print(f"[IMAGE] Extracted path: {image_path}, scale: {scale}, offset: ({offset_x_mm}, {offset_y_mm})", flush=True)
    elif isinstance(content, str):
        image_path = content
        print(f"[IMAGE] String content: {image_path}", flush=True)
    
    # Always create image element (even if no photo) for drag & drop
    svg_parts = []
    element_id = generate_unique_id("image", row, col, element.id)
    group_id = generate_unique_id("image-group", row, col, element.id)
    
    # Use placeholder image if no path provided
    if not image_path:
        # Use data URI for placeholder (light gray square)
        image_path = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='100%25' height='100%25' fill='%23f0f0f0'/%3E%3C/svg%3E"
    
    # Start group for image + frame
    svg_parts.append(f'<g id="{group_id}">')
    
    # Handle clipping if defined
    clip_path_id = None
    if element.clip_shape:
        clip_path_id = generate_unique_id("clip", row, col, element.id)
        
        # Create clipPath definition
        svg_parts.append(f'<clipPath id="{clip_path_id}">')
        
        if element.clip_shape.kind == "rounded_rect":
            svg_parts.append(
                f'<rect x="{element.x_mm}" y="{element.y_mm}" '
                f'width="{element.w_mm}" height="{element.h_mm}" '
                f'rx="{element.clip_shape.radius_mm}" ry="{element.clip_shape.radius_mm}" />'
            )
        
        svg_parts.append('</clipPath>')
    
    # Build transform string if scale or offset is applied
    transform_parts = []
    if scale != 1.0 or offset_x_mm != 0 or offset_y_mm != 0:
        # Calculate center point for scaling
        center_x = element.x_mm + element.w_mm / 2
        center_y = element.y_mm + element.h_mm / 2
        
        # Apply transforms: translate to center, scale, translate back, then apply offset
        if offset_x_mm != 0 or offset_y_mm != 0:
            transform_parts.append(f'translate({offset_x_mm}, {offset_y_mm})')
        if scale != 1.0:
            transform_parts.append(f'translate({center_x}, {center_y}) scale({scale}) translate({-center_x}, {-center_y})')
    
    # If we have transforms, wrap image in a group with clip-path applied to the group
    if transform_parts:
        transform_attr = f' transform="{" ".join(transform_parts)}"'
        
        # Start a clipped group
        if clip_path_id:
            svg_parts.append(f'<g clip-path="url(#{clip_path_id})">')
        
        # Render image with transform but no clip-path (clip is on parent group)
        image_attrs = [
            f'id="{element_id}"',
            f'x="{element.x_mm}"',
            f'y="{element.y_mm}"',
            f'width="{element.w_mm}"',
            f'height="{element.h_mm}"',
            f'href="{escape_xml(image_path)}"',
            'preserveAspectRatio="xMidYMid slice"' if element.fit == "cover" else 'preserveAspectRatio="xMidYMid meet"'
        ]
        
        svg_parts.append(f'<image {" ".join(image_attrs)}{transform_attr} />')
        
        # Close clipped group
        if clip_path_id:
            svg_parts.append('</g>')
    else:
        # No transforms, render normally with clip-path on image
        image_attrs = [
            f'id="{element_id}"',
            f'x="{element.x_mm}"',
            f'y="{element.y_mm}"',
            f'width="{element.w_mm}"',
            f'height="{element.h_mm}"',
            f'href="{escape_xml(image_path)}"',
            'preserveAspectRatio="xMidYMid slice"' if element.fit == "cover" else 'preserveAspectRatio="xMidYMid meet"'
        ]
        
        if clip_path_id:
            image_attrs.append(f'clip-path="url(#{clip_path_id})"')
        
        svg_parts.append(f'<image {" ".join(image_attrs)} />')
    
    # Render frame overlay if specified
    if element.frame_source:
        frame_id = generate_unique_id("frame", row, col, element.id)
        radius = element.clip_shape.radius_mm if element.clip_shape else 0
        
        try:
            # Check if it's a built-in frame type
            if element.frame_source in ['simple-gold', 'simple-silver', 'simple-black', 'ornate-gold']:
                # Generate inline frame based on type
                border_width = element.border_width_mm if hasattr(element, 'border_width_mm') else 1.5
                frame_svg = generate_inline_frame(element.frame_source, element.w_mm, element.h_mm, radius, border_width)
                # Wrap in group with transform to position correctly
                positioned_frame = (
                    f'<g transform="translate({element.x_mm}, {element.y_mm})">'
                    f'{frame_svg.replace("id=\"frame\"", f"id=\"{frame_id}\"")}'
                    f'</g>'
                )
                svg_parts.append(positioned_frame)
            else:
                # Try to load from file
                frame_path = Path(element.frame_source.lstrip('/'))
                if not frame_path.is_absolute():
                    from ..settings import settings
                    assets_dir = Path(settings.ASSETS_DIR) if hasattr(settings, 'ASSETS_DIR') else Path('assets')
                    frame_path = assets_dir / element.frame_source
                
                if frame_path.exists():
                    frame_svg = frame_path.read_text()
                    # Embed frame as nested SVG with proper positioning and sizing
                    svg_parts.append(
                        f'<svg id="{frame_id}" '
                        f'x="{element.x_mm}" y="{element.y_mm}" '
                        f'width="{element.w_mm}" height="{element.h_mm}" '
                        f'viewBox="0 0 100 100" preserveAspectRatio="none">'
                        f'{frame_svg}'
                        f'</svg>'
                    )
                else:
                    # Fallback to simple border
                    svg_parts.append(
                        f'<rect id="{frame_id}" '
                        f'x="{element.x_mm}" y="{element.y_mm}" '
                        f'width="{element.w_mm}" height="{element.h_mm}" '
                        f'fill="none" stroke="gold" stroke-width="1" rx="{radius}" />'
                    )
        except Exception as e:
            # Fallback on error
            svg_parts.append(
                f'<!-- Frame load error: {str(e)} -->'
                f'<rect id="{frame_id}" '
                f'x="{element.x_mm}" y="{element.y_mm}" '
                f'width="{element.w_mm}" height="{element.h_mm}" '
                f'fill="none" stroke="gold" stroke-width="1" rx="{radius}" />'
            )
    
    svg_parts.append('</g>')
    
    return '\n'.join(svg_parts)


def render_graphic_element(
    element: GraphicElement,
    row: int,
    col: int,
    dynamic_source: Optional[str] = None
) -> str:
    """
    Render a graphic element by loading and inlining SVG or embedding an image.
    
    Args:
        element: Graphic element definition
        row: Row index for ID generation
        col: Column index for ID generation
        dynamic_source: Optional dynamic source path from CSV content (overrides element.source)
        
    Returns:
        SVG markup string
    """
    element_id = generate_unique_id("graphic", row, col, element.id)
    
    # Use dynamic source if provided, otherwise use element's static source
    source = dynamic_source if dynamic_source else element.source
    
    # If source is a PNG/JPG/JPEG, render as image instead of SVG
    if source and source.lower().endswith(('.png', '.jpg', '.jpeg')):
        # Render as embedded image
        return (
            f'<image id="{element_id}" '
            f'x="{element.x_mm}mm" y="{element.y_mm}mm" '
            f'width="{element.width_mm}mm" height="{element.height_mm}mm" '
            f'href="{source}" '
            f'preserveAspectRatio="xMidYMid meet" />'
        )
    
    # Try to load SVG from source
    svg_content = None
    try:
        # Handle different source formats
        if source.startswith('<svg'):
            # Inline SVG markup
            svg_content = source
        elif source.startswith('http://') or source.startswith('https://'):
            # URL - would need requests library, skip for now
            svg_content = None
        else:
            # File path
            source_path = Path(source)
            if not source_path.is_absolute():
                # Try relative to assets directory
                from ..settings import settings
                assets_dir = Path(settings.ASSETS_DIR) if hasattr(settings, 'ASSETS_DIR') else Path('assets')
                source_path = assets_dir / source
            
            if source_path.exists():
                svg_content = source_path.read_text(encoding='utf-8')
    except Exception as e:
        # Log error but continue with placeholder
        svg_content = None
    
    if svg_content:
        # Extract viewBox from source SVG if present
        viewbox_match = re.search(r'viewBox="([^"]+)"', svg_content)
        viewbox = viewbox_match.group(1) if viewbox_match else "0 0 100 100"
        
        # Strip outer <svg> tags if present and extract inner content
        inner_content = svg_content
        if '<svg' in svg_content:
            # Extract content between <svg...> and </svg>
            svg_start = svg_content.find('>')
            svg_end = svg_content.rfind('</svg>')
            if svg_start != -1 and svg_end != -1:
                inner_content = svg_content[svg_start + 1:svg_end].strip()
        
        # Wrap in positioned SVG with proper scaling
        return (
            f'<svg id="{element_id}" '
            f'x="{element.x_mm}" y="{element.y_mm}" '
            f'width="{element.w_mm}" height="{element.h_mm}" '
            f'viewBox="{viewbox}" preserveAspectRatio="xMidYMid meet">'
            f'{inner_content}'
            f'</svg>'
        )
    else:
        # Fallback to placeholder rectangle
        return (
            f'<!-- Graphic not found: {escape_xml(element.source)} -->\n'
            f'<rect id="{element_id}" '
            f'x="{element.x_mm}" y="{element.y_mm}" '
            f'width="{element.w_mm}" height="{element.h_mm}" '
            f'fill="none" stroke="#000000" stroke-width="0.5" />'
        )


def calculate_element_position(element: Element, elements: list) -> tuple[float, float]:
    """
    Calculate absolute position of element, accounting for anchor_to.
    
    Args:
        element: Element to position
        elements: All elements in the part (for anchor lookup)
        
    Returns:
        Tuple of (absolute_x_mm, absolute_y_mm)
    """
    if not element.anchor_to:
        # No anchor, use position as-is
        return (element.x_mm, element.y_mm)
    
    # Find anchor element
    anchor_element = None
    for e in elements:
        if e.id == element.anchor_to:
            anchor_element = e
            break
    
    if not anchor_element:
        # Anchor not found, fallback to absolute position
        return (element.x_mm, element.y_mm)
    
    # Calculate anchor point position
    anchor_x, anchor_y = calculate_element_position(anchor_element, elements)
    
    if element.anchor_point == "bottom":
        anchor_y += anchor_element.h_mm
    elif element.anchor_point == "right":
        anchor_x += anchor_element.w_mm
    elif element.anchor_point == "center":
        anchor_x += anchor_element.w_mm / 2
        anchor_y += anchor_element.h_mm / 2
    # "top" and "left" use anchor position as-is
    
    return (anchor_x + element.x_mm, anchor_y + element.y_mm)


def render_part(
    template: TemplateJSON,
    slot_content: Optional[SlotContent],
    row: int,
    col: int
) -> str:
    """
    Render a single part/tile with all its elements.
    
    Args:
        template: Template definition
        slot_content: Content for this slot (or None for empty)
        row: Row index
        col: Column index
        
    Returns:
        SVG markup string for this part
    """
    svg_parts = []
    
    # Calculate absolute positions for all elements (handling anchors)
    elements_with_positions = []
    for element in template.part.elements:
        abs_x, abs_y = calculate_element_position(element, template.part.elements)
        elements_with_positions.append((element, abs_x, abs_y))
    
    # Render elements in order: images first, then text, then graphics (so borders are on top)
    images = [(e, x, y) for e, x, y in elements_with_positions if isinstance(e, ImageElement)]
    texts = [(e, x, y) for e, x, y in elements_with_positions if isinstance(e, TextElement)]
    graphics = [(e, x, y) for e, x, y in elements_with_positions if isinstance(e, GraphicElement)]
    
    # Render images
    for element, abs_x, abs_y in images:
        # Create temporary element with absolute position
        positioned_element = element.model_copy(update={"x_mm": abs_x, "y_mm": abs_y, "anchor_to": None})
        image_path = slot_content.get_content(element.id) if slot_content else None
        svg_parts.append(render_image_element(positioned_element, image_path, row, col))
    
    # Render text
    for element, abs_x, abs_y in texts:
        positioned_element = element.model_copy(update={"x_mm": abs_x, "y_mm": abs_y, "anchor_to": None})
        content = slot_content.get_content(element.id) if slot_content else ""
        svg_parts.append(render_text_element(positioned_element, content or "", row, col))
    
    # Render graphics
    for element, abs_x, abs_y in graphics:
        positioned_element = element.model_copy(update={"x_mm": abs_x, "y_mm": abs_y, "anchor_to": None})
        # Get dynamic graphic path from slot content if available
        graphic_path = slot_content.get_content(element.id) if slot_content else None
        svg_parts.append(render_graphic_element(positioned_element, row, col, graphic_path))
    
    return '\n'.join(svg_parts)


def renderPlateSVG(template: TemplateJSON, content: ContentJSON) -> str:
    """
    Render complete bed/plate SVG with all tiled parts.
    
    This is the main entry point for SVG generation.
    
    Args:
        template: Template definition (bed, part, tiling)
        content: Content payload for all slots
        
    Returns:
        Complete SVG markup string
    """
    bed = template.bed
    tiling = template.tiling
    part = template.part
    
    # Build SVG header
    svg_parts = []
    svg_parts.append(
        f'<svg width="{bed.width_mm}mm" height="{bed.height_mm}mm" '
        f'viewBox="0 0 {bed.width_mm} {bed.height_mm}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )
    
    # Add metadata
    svg_parts.append('<!-- Generated by Template Layout Engine -->')
    svg_parts.append(f'<!-- Bed: {bed.width_mm}mm x {bed.height_mm}mm -->')
    svg_parts.append(f'<!-- Part: {part.width_mm}mm x {part.height_mm}mm -->')
    svg_parts.append(f'<!-- Tiling: {tiling.rows} rows x {tiling.cols} cols -->')
    
    # Add origin marker if enabled (0.1mm square at bottom-left)
    if bed.origin_marker:
        marker_size = 0.1
        # SVG origin is top-left, so bottom-left is at y = height
        marker_y = bed.height_mm - marker_size
        svg_parts.append(
            f'<rect id="origin-marker" '
            f'x="{bed.origin_x_mm}" y="{marker_y}" '
            f'width="{marker_size}" height="{marker_size}" '
            f'fill="black" />'
        )
        svg_parts.append(f'<!-- Origin marker at ({bed.origin_x_mm}, {bed.origin_y_mm}) -->')
    
    # Render each tile
    for row in range(tiling.rows):
        for col in range(tiling.cols):
            # Calculate tile position on bed
            tile_x = (
                bed.margin_mm.left +
                tiling.offset_x_mm +
                col * (part.width_mm + tiling.gap_x_mm)
            )
            tile_y = (
                bed.margin_mm.top +
                tiling.offset_y_mm +
                row * (part.height_mm + tiling.gap_y_mm)
            )
            
            # Get content for this slot
            slot_index = row * tiling.cols + col
            slot_content = content.get_slot(slot_index)
            
            # Create tile group with transform
            tile_id = generate_unique_id("tile", row, col)
            svg_parts.append(f'<g id="{tile_id}" transform="translate({tile_x}, {tile_y})">')
            
            # Render part content
            svg_parts.append(render_part(template, slot_content, row, col))
            
            svg_parts.append('</g>')
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


def exportPDF(svg_string: str, output_path: str = "output.pdf") -> str:
    """
    Export SVG to PDF format using cairosvg.
    
    Args:
        svg_string: SVG markup to convert
        output_path: Destination PDF file path
        
    Returns:
        Path to generated PDF file
        
    Raises:
        ImportError: If cairosvg is not installed
        Exception: If conversion fails
    """
    from .pdf_export import export_svg_to_pdf_file
    return export_svg_to_pdf_file(svg_string, output_path)
