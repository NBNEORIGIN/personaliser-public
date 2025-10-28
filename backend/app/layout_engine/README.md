# Template-Driven Layout Engine

A flexible, template-driven system for generating print plate layouts (SVG and PDF) for signage, engraving, and memorial products.

## Overview

This engine **replaces hardcoded per-product processors** with a data-driven approach where:
- **Templates** define the physical layout (bed size, part size, element positions)
- **Content** provides the actual text, images, and data for each part
- **Renderer** generates editable SVG output that can be opened in Illustrator/Inkscape

## Key Features

✅ **Template-driven** - No code changes needed for new products  
✅ **Editable SVG output** - Text remains live text (not outlined)  
✅ **Flexible tiling** - Configure rows, columns, gaps dynamically  
✅ **Multi-element support** - Text, images, and graphics  
✅ **Rounded image clipping** - Optional clip shapes for photos  
✅ **Millimeter precision** - All coordinates in mm  

## Architecture

```
┌─────────────────┐
│ TemplateJSON    │  ← Defines layout structure
│ (bed/part/tile) │
└────────┬────────┘
         │
         ├─────────────┐
         │             │
┌────────▼────────┐   │
│ ContentJSON     │   │
│ (text/images)   │   │
└────────┬────────┘   │
         │            │
         └────┬───────┘
              │
      ┌───────▼────────┐
      │ renderPlateSVG │
      └───────┬────────┘
              │
      ┌───────▼────────┐
      │  SVG Output    │
      │ (editable!)    │
      └────────────────┘
```

## Data Models

### TemplateJSON

Defines the physical layout:

```python
{
  "bed": {
    "width_mm": 480,
    "height_mm": 330,
    "margin_mm": {"left": 10, "top": 10}
  },
  "part": {
    "width_mm": 140,
    "height_mm": 90,
    "elements": [
      {
        "type": "text",
        "id": "nameLine",
        "x_mm": 10,
        "y_mm": 20,
        "w_mm": 120,
        "h_mm": 10,
        "font_family": "Times New Roman",
        "font_size_pt": 14,
        "text_align": "center",
        "multiline": false
      },
      {
        "type": "image",
        "id": "photoArea",
        "x_mm": 10,
        "y_mm": 70,
        "w_mm": 40,
        "h_mm": 40,
        "fit": "cover",
        "clip_shape": {"kind": "rounded_rect", "radius_mm": 4}
      }
    ]
  },
  "tiling": {
    "cols": 3,
    "rows": 3,
    "gap_x_mm": 5,
    "gap_y_mm": 5
  }
}
```

### ContentJSON

Provides content for each slot:

```python
{
  "slots": [
    {
      "slot_index": 0,
      "nameLine": "In loving memory",
      "messageBlock": "John Kendall Newman\n1952 – 2024",
      "photoArea": "/uploads/photo-1.jpg"
    },
    {
      "slot_index": 1,
      "nameLine": "Forever in our hearts",
      "messageBlock": "Mary Smith\n1945 – 2024",
      "photoArea": "/uploads/photo-2.jpg"
    }
  ]
}
```

## Usage

### Basic Example

```python
from app.layout_engine import TemplateJSON, ContentJSON, renderPlateSVG

# Load or create template
template = TemplateJSON(...)

# Load or create content
content = ContentJSON(...)

# Generate SVG
svg_output = renderPlateSVG(template, content)

# Save to file
with open("output.svg", "w") as f:
    f.write(svg_output)
```

### Running the Example

```bash
cd backend
python -m app.layout_engine.example
```

This generates `example_output.svg` with a 3x3 grid of memorial plaques.

## Element Types

### Text Element

```python
{
  "type": "text",
  "id": "myText",
  "x_mm": 10,
  "y_mm": 20,
  "w_mm": 100,
  "h_mm": 20,
  "font_family": "Arial",
  "font_size_pt": 12,
  "text_align": "center",  # left, center, right
  "multiline": true         # enables line wrapping
}
```

### Image Element

```python
{
  "type": "image",
  "id": "myPhoto",
  "x_mm": 10,
  "y_mm": 50,
  "w_mm": 40,
  "h_mm": 40,
  "fit": "cover",  # or "contain"
  "clip_shape": {
    "kind": "rounded_rect",
    "radius_mm": 4
  }
}
```

### Graphic Element

```python
{
  "type": "graphic",
  "id": "border",
  "x_mm": 0,
  "y_mm": 0,
  "w_mm": 140,
  "h_mm": 90,
  "source": "border.svg"
}
```

## Coordinate System

- **Origin**: Top-left (0, 0)
- **Units**: Millimeters (mm)
- **Element positioning**: Relative to part origin
- **Tiling**: Row-major order (`slot_index = row * cols + col`)

## Tiling Math

For each tile at position `(row, col)`:

```python
tile_x = bed.margin.left + tiling.offset_x + col * (part.width + tiling.gap_x)
tile_y = bed.margin.top + tiling.offset_y + row * (part.height + tiling.gap_y)
```

## SVG Output Features

✅ **Live text** - Text elements remain editable in Illustrator/Inkscape  
✅ **Unique IDs** - Each element has ID like `text-r0-c1-nameLine`  
✅ **Grouped tiles** - Each tile wrapped in `<g transform="translate(...)">`  
✅ **ClipPaths** - Rounded image clipping with unique IDs  
✅ **Layer order** - Images → Text → Graphics (borders on top)  

## PDF Export

PDF export is stubbed for future implementation:

```python
from app.layout_engine import exportPDF

# TODO: Implement using cairosvg, Inkscape CLI, or rsvg-convert
pdf_path = exportPDF(svg_string, "output.pdf")
```

## Future Enhancements

- [ ] Implement PDF export (cairosvg integration)
- [ ] Add proper text wrapping with font metrics
- [ ] Support for more clip shapes (circle, ellipse)
- [ ] Graphic SVG inlining and scaling
- [ ] Image fit mode implementation (cover/contain)
- [ ] Template validation and error handling
- [ ] Database storage for templates
- [ ] REST API endpoints
- [ ] Frontend UI for template editor

## Migration from Old Processors

Old hardcoded processors like `regular_stake_pdf_v1.py` can be replaced by:

1. **Create a template** defining the layout
2. **Store template** in database or JSON file
3. **Generate content** from order data
4. **Call `renderPlateSVG()`** instead of old processor

This eliminates the need for per-product code!

## Files

- `models.py` - Pydantic data models
- `renderer.py` - SVG generation engine
- `utils.py` - Helper functions (pt↔mm, text wrapping, etc.)
- `example.py` - Example usage and test
- `__init__.py` - Public API exports

## Testing

```bash
# Run example
python -m app.layout_engine.example

# Check generated SVG
open example_output.svg  # macOS
start example_output.svg  # Windows
```

## License

Part of the Personaliser project.
