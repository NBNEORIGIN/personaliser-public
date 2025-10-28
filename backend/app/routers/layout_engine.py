"""
REST API endpoints for template-driven layout engine.

Provides HTTP interface for generating SVG and PDF outputs.
"""

from fastapi import APIRouter, HTTPException, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict
import io
import json

from ..layout_engine import TemplateJSON, ContentJSON, renderPlateSVG
from ..layout_engine.pdf_export import export_svg_to_pdf
from ..layout_engine.csv_parser import parse_csv_to_content, parse_tsv_to_content, auto_detect_mapping


router = APIRouter(prefix="/api/layout", tags=["Layout Engine"])


class GenerateRequest(BaseModel):
    """Request body for generating layouts."""
    template: TemplateJSON
    content: ContentJSON
    format: str = "svg"  # "svg" or "pdf"


class GenerateResponse(BaseModel):
    """Response for successful generation."""
    success: bool
    message: str
    svg: Optional[str] = None


@router.post("/generate", response_model=GenerateResponse)
async def generate_layout(request: GenerateRequest):
    """
    Generate a print plate layout from template and content.
    
    **Parameters:**
    - `template`: Layout template definition (bed, part, tiling, elements)
    - `content`: Content payload for each slot
    - `format`: Output format ("svg" or "pdf")
    
    **Returns:**
    - For SVG: JSON response with SVG string
    - For PDF: Binary PDF file download
    
    **Example:**
    ```json
    {
      "template": {
        "bed": {"width_mm": 480, "height_mm": 330, "margin_mm": {"left": 10, "top": 10}},
        "part": {"width_mm": 140, "height_mm": 90, "elements": [...]},
        "tiling": {"cols": 3, "rows": 3, "gap_x_mm": 5, "gap_y_mm": 5}
      },
      "content": {
        "slots": [
          {"slot_index": 0, "nameLine": "John Doe", "messageBlock": "1950-2024"}
        ]
      },
      "format": "svg"
    }
    ```
    """
    try:
        # Generate SVG
        svg_output = renderPlateSVG(request.template, request.content)
        
        if request.format == "pdf":
            # Convert to PDF and return as download
            pdf_bytes = export_svg_to_pdf(svg_output)
            
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "attachment; filename=layout.pdf"
                }
            )
        
        # Return SVG as JSON
        return GenerateResponse(
            success=True,
            message="SVG generated successfully",
            svg=svg_output
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate layout: {str(e)}"
        )


@router.post("/generate/svg")
async def generate_svg(request: GenerateRequest):
    """
    Generate SVG layout and return as downloadable file.
    
    **Parameters:**
    - `template`: Layout template definition
    - `content`: Content payload
    
    **Returns:**
    - SVG file download
    """
    try:
        svg_output = renderPlateSVG(request.template, request.content)
        
        return Response(
            content=svg_output,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": "attachment; filename=layout.svg"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate SVG: {str(e)}"
        )


@router.post("/generate/pdf")
async def generate_pdf(request: GenerateRequest):
    """
    Generate PDF layout and return as downloadable file.
    
    **Parameters:**
    - `template`: Layout template definition
    - `content`: Content payload
    
    **Returns:**
    - PDF file download
    """
    try:
        # Generate SVG
        svg_output = renderPlateSVG(request.template, request.content)
        
        # Convert to PDF
        pdf_bytes = export_svg_to_pdf(svg_output)
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=layout.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.post("/upload/csv")
async def upload_csv(
    file: UploadFile = File(...),
    template: str = Form(...),
    column_mapping: Optional[str] = Form(None),
    has_header: bool = Form(True),
    format: str = Form("svg"),
    page: Optional[int] = Form(None),
    items_per_page: Optional[int] = Form(None)
):
    """
    Upload CSV file and generate layout with pagination support.
    
    **Parameters:**
    - `file`: CSV file upload
    - `template`: JSON string of template definition
    - `column_mapping`: Optional JSON string mapping CSV columns to element IDs
                       e.g., {"Name": "line1", "Date": "line2"}
    - `has_header`: Whether CSV has header row
    - `format`: Output format ("svg" or "pdf")
    - `page`: Optional page number (0-indexed) for pagination
    - `items_per_page`: Optional items per page for pagination
    
    **Returns:**
    - SVG or PDF file download
    """
    try:
        # Read CSV data
        csv_data = (await file.read()).decode('utf-8')
        
        # Parse template
        template_obj = TemplateJSON.model_validate_json(template)
        
        # Parse or auto-detect column mapping
        if column_mapping:
            mapping = json.loads(column_mapping)
        else:
            # Auto-detect mapping
            element_ids = [e.id for e in template_obj.part.elements]
            mapping = auto_detect_mapping(csv_data, element_ids, has_header)
        
        # Parse CSV to content
        content = parse_csv_to_content(csv_data, mapping, has_header)
        
        # Handle pagination if requested
        if page is not None and items_per_page is not None:
            start_idx = page * items_per_page
            end_idx = start_idx + items_per_page
            content.slots = content.slots[start_idx:end_idx]
        
        # Debug logging
        print(f"[CSV DEBUG] Column mapping: {mapping}")
        print(f"[CSV DEBUG] Number of slots: {len(content.slots)}")
        if content.slots:
            print(f"[CSV DEBUG] First slot data: {content.slots[0].model_dump()}")
        
        # Generate SVG
        svg_output = renderPlateSVG(template_obj, content)
        
        if format == "pdf":
            # Convert to PDF
            pdf_bytes = export_svg_to_pdf(svg_output)
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=layout.pdf"}
            )
        else:
            # Return SVG
            return Response(
                content=svg_output,
                media_type="image/svg+xml",
                headers={"Content-Disposition": "attachment; filename=layout.svg"}
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process CSV: {str(e)}"
        )


@router.post("/upload/graphic")
async def upload_graphic(file: UploadFile = File(...)):
    """
    Upload a graphic/SVG file for use in templates.
    
    **Parameters:**
    - `file`: SVG or image file
    
    **Returns:**
    - File path to use in templates
    """
    try:
        from pathlib import Path
        
        # Create graphics directory if it doesn't exist
        graphics_dir = Path("static/graphics")
        graphics_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = graphics_dir / file.filename
        content = await file.read()
        file_path.write_bytes(content)
        
        return {
            "success": True,
            "filename": file.filename,
            "path": f"/static/graphics/{file.filename}",
            "message": "Graphic uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload graphic: {str(e)}"
        )


@router.get("/graphics")
async def list_graphics():
    """
    List all uploaded graphics.
    
    **Returns:**
    - List of available graphics with paths
    """
    try:
        from pathlib import Path
        
        graphics_dir = Path("static/graphics")
        if not graphics_dir.exists():
            return {"graphics": []}
        
        graphics = []
        for file_path in graphics_dir.iterdir():
            if file_path.is_file():
                graphics.append({
                    "filename": file_path.name,
                    "path": f"/static/graphics/{file_path.name}",
                    "size": file_path.stat().st_size
                })
        
        return {"graphics": graphics}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list graphics: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "layout-engine",
        "version": "1.0.0"
    }
