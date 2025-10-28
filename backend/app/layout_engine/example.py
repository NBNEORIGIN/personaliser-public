"""
Example usage of the template layout engine.

This demonstrates how to create a template and content payload,
then generate an SVG plate.
"""

from .models import (
    TemplateJSON, ContentJSON, SlotContent,
    BedDefinition, BedMargin, PartDefinition, TilingDefinition,
    TextElement, ImageElement, GraphicElement
)
from .renderer import renderPlateSVG


def create_memorial_plaque_template() -> TemplateJSON:
    """
    Create an example template for memorial plaques.
    
    Returns:
        Template definition
    """
    return TemplateJSON(
        bed=BedDefinition(
            width_mm=480,
            height_mm=330,
            margin_mm=BedMargin(left=10, top=10)
        ),
        part=PartDefinition(
            width_mm=140,
            height_mm=90,
            elements=[
                TextElement(
                    type="text",
                    id="nameLine",
                    x_mm=10,
                    y_mm=10,
                    w_mm=120,
                    h_mm=10,
                    font_family="Times New Roman",
                    font_size_pt=14,
                    text_align="center",
                    multiline=False,
                    editable=True
                ),
                TextElement(
                    type="text",
                    id="messageBlock",
                    x_mm=10,
                    y_mm=25,
                    w_mm=120,
                    h_mm=30,
                    font_family="Times New Roman",
                    font_size_pt=10,
                    text_align="center",
                    multiline=True,
                    editable=True
                ),
                ImageElement(
                    type="image",
                    id="photoArea",
                    x_mm=10,
                    y_mm=60,
                    w_mm=40,
                    h_mm=40,
                    fit="cover",
                    clip_shape={"kind": "rounded_rect", "radius_mm": 4},
                    editable=True
                ),
                GraphicElement(
                    type="graphic",
                    id="borderFrame",
                    x_mm=0,
                    y_mm=0,
                    w_mm=140,
                    h_mm=90,
                    source="border.svg",
                    editable=False
                )
            ]
        ),
        tiling=TilingDefinition(
            cols=3,
            rows=3,
            gap_x_mm=5,
            gap_y_mm=5,
            offset_x_mm=0,
            offset_y_mm=0
        )
    )


def create_example_content() -> ContentJSON:
    """
    Create example content for 2 slots.
    
    Returns:
        Content payload
    """
    return ContentJSON(
        slots=[
            SlotContent(
                slot_index=0,
                nameLine="In loving memory",
                messageBlock="John Kendall Newman\n1952 – 2024",
                photoArea="/uploads/jkn-photo-1.jpg"
            ),
            SlotContent(
                slot_index=1,
                nameLine="Forever in our hearts",
                messageBlock="Mary Elizabeth Smith\n1945 – 2024",
                photoArea="/uploads/mes-photo.jpg"
            ),
            # Slot 2 will be empty (no content provided)
        ]
    )


def generate_example_svg() -> str:
    """
    Generate an example SVG using the template engine.
    
    Returns:
        SVG markup string
    """
    template = create_memorial_plaque_template()
    content = create_example_content()
    
    svg = renderPlateSVG(template, content)
    
    return svg


if __name__ == "__main__":
    # Generate and print example SVG
    svg_output = generate_example_svg()
    print(svg_output)
    
    # Optionally save to file
    with open("example_output.svg", "w", encoding="utf-8") as f:
        f.write(svg_output)
    
    print("\n✓ SVG generated successfully!")
    print("✓ Saved to example_output.svg")
