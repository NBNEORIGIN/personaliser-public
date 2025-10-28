"""
REST API endpoints for template-driven layout engine.

Provides HTTP interface for generating SVG and PDF outputs.
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io

from app.layout_engine import TemplateJSON, ContentJSON, renderPlateSVG
from app.layout_engine.pdf_export import export_svg_to_pdf


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


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "layout-engine",
        "version": "1.0.0"
    }
