# Layout Engine Features

## ✅ All Requested Features Implemented

### 1. **Bed Origin Marker** ✅
- 0.1mm square marker at bottom-left corner
- Configurable position via `origin_x_mm`, `origin_y_mm`
- Can be enabled/disabled via `origin_marker` flag
- Provides reference point for UV printers and other machines

**Usage:**
```json
{
  "bed": {
    "width_mm": 480,
    "height_mm": 330,
    "origin_marker": true,
    "origin_x_mm": 0,
    "origin_y_mm": 0
  }
}
```

---

### 2. **Relative Positioning** ✅
- Elements can be positioned relative to other elements
- Use `anchor_to` to specify which element to anchor to
- Use `anchor_point` to specify which edge: `"top"`, `"bottom"`, `"left"`, `"right"`, `"center"`
- Supports chained anchoring (element A → element B → element C)

**Usage:**
```json
{
  "elements": [
    {
      "type": "text",
      "id": "title",
      "x_mm": 10,
      "y_mm": 10,
      "w_mm": 120,
      "h_mm": 10
    },
    {
      "type": "text",
      "id": "subtitle",
      "x_mm": 0,
      "y_mm": 5,
      "w_mm": 120,
      "h_mm": 8,
      "anchor_to": "title",
      "anchor_point": "bottom"
    }
  ]
}
```

---

### 3. **Graphics Embedding** ✅
- Embed SVG graphics, borders, frames
- Use `GraphicElement` with `source` path
- Graphics render on top layer (borders overlay content)

**Usage:**
```json
{
  "type": "graphic",
  "id": "border",
  "x_mm": 0,
  "y_mm": 0,
  "w_mm": 140,
  "h_mm": 90,
  "source": "/assets/borders/memorial_frame.svg"
}
```

---

### 4. **Image Embedding** ✅
- Embed photos/images
- Use `ImageElement` with `fit` mode: `"cover"` or `"contain"`
- Images render on bottom layer (behind text)

**Usage:**
```json
{
  "type": "image",
  "id": "photo",
  "x_mm": 10,
  "y_mm": 10,
  "w_mm": 50,
  "h_mm": 60,
  "fit": "cover"
}
```

---

### 5. **Image Clipping with Rounded Corners** ✅
- Clip images with rounded rectangles
- Adjustable corner radius
- Use `clip_shape` with `radius_mm`

**Usage:**
```json
{
  "type": "image",
  "id": "photo",
  "x_mm": 10,
  "y_mm": 10,
  "w_mm": 50,
  "h_mm": 60,
  "fit": "cover",
  "clip_shape": {
    "kind": "rounded_rect",
    "radius_mm": 5
  }
}
```

---

### 6. **CSV/Table Upload & Mapping** ✅
- Upload CSV files with order data
- Auto-detect column mapping or specify manually
- Maps CSV columns to template element IDs
- Supports TSV (tab-separated) format
- Works like existing regular stakes and photo stakes processors

**API Endpoint:**
```
POST /api/layout/upload/csv
```

**Parameters:**
- `file`: CSV file upload
- `template`: JSON template definition
- `column_mapping`: Optional mapping (e.g., `{"Name": "line1", "Date": "line2"}`)
- `has_header`: Whether CSV has header row (default: true)
- `format`: Output format `"svg"` or `"pdf"` (default: "svg")

**Example CSV:**
```csv
Name,Date,Message,Photo
John Smith,1950-2024,Forever in our hearts,/photos/john.jpg
Jane Doe,1955-2023,Loved and missed,/photos/jane.jpg
```

**Example Mapping:**
```json
{
  "Name": "line1",
  "Date": "line2",
  "Message": "line3",
  "Photo": "photo"
}
```

---

### 7. **Adjustable Text Size** ✅
- Set font size via `font_size_pt` (in points)
- Adjustable per element
- Supports any font family

**Usage:**
```json
{
  "type": "text",
  "id": "title",
  "font_size_pt": 16,
  "font_family": "Georgia"
}
```

---

## API Endpoints

### Generate Layout
```
POST /api/layout/generate
```
Generate SVG or PDF from template + content

### Generate SVG
```
POST /api/layout/generate/svg
```
Generate SVG file download

### Generate PDF
```
POST /api/layout/generate/pdf
```
Generate PDF file download

### Upload CSV
```
POST /api/layout/upload/csv
```
Upload CSV and generate layout

### Health Check
```
GET /api/layout/health
```
Service health status

---

## Live Demo

**URL:** https://demo.nbne.uk/demo (once DNS propagates)  
**Fallback:** https://personaliser-api.onrender.com/demo

**Features:**
- Interactive template editor
- Live SVG preview
- Quick templates (Memorial, Business Cards, Labels)
- PDF download
- Configurable bed size, part size, tiling

---

## Migration Status

### ✅ Regular Stakes
- Migrated to template engine
- Template: `REGULAR_STAKE_3X3`
- Processor: `regular_stake_template.py`
- Backward compatible with existing code

### 🔄 Photo Stakes
- Template ready (same structure as regular stakes)
- Just add `ImageElement` with `clip_shape`
- Can use same CSV upload workflow

---

## Technical Stack

- **Backend:** FastAPI + Python 3.11
- **SVG Generation:** Custom renderer with live text
- **PDF Export:** CairoSVG
- **CSV Parsing:** Python csv module
- **Validation:** Pydantic models
- **Deployment:** Render (2GB RAM)
- **Domain:** demo.nbne.uk

---

## Next Steps

1. **Test CSV upload** - Upload sample order CSV
2. **Migrate photo stakes** - Create photo stakes template
3. **Add more templates** - Business cards, labels, etc.
4. **Enhance demo UI** - Add CSV upload to frontend
5. **Production testing** - Test with real orders

---

## Documentation

- **API Docs:** https://demo.nbne.uk/docs
- **Template Guide:** `/backend/app/layout_engine/README.md`
- **Example Usage:** `/backend/app/layout_engine/example.py`
