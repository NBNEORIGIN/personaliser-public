from __future__ import annotations
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Tuple

class Severity(str, Enum):
    info = "info"
    warn = "warn"
    error = "error"

class QaWarning(BaseModel):
    code: str
    message: str
    severity: Severity = Severity.warn
    field: Optional[str] = None

class LineField(BaseModel):
    id: str
    value: str

# compatibility alias
TextLine = LineField

class OrderItem(BaseModel):
    item_id: str = Field(default_factory=lambda: "")
    order_id: Optional[str] = None
    line_item_id: Optional[str] = None
    order_ref: Optional[str] = None
    channel: Optional[str] = None
    template_id: str
    lines: List[LineField] = Field(default_factory=list)
    graphic: Optional[str] = None
    photo_url: Optional[str] = None
    requires_photo: bool = False
    # Enrichment fields (optional) passed from ingest for routing/placement
    sku: Optional[str] = None
    graphics_key: Optional[str] = None
    colour: Optional[str] = None
    product_type: Optional[str] = None
    decoration_type: Optional[str] = None
    theme: Optional[str] = None
    processor: Optional[str] = None

class Rect(BaseModel):
    id: str
    w: float
    h: float

class PlacedRect(Rect):
    x: float
    y: float

class GenerateRequest(BaseModel):
    items: List[OrderItem]
    machine_id: str
    seed: Optional[int] = None

class PreviewResponse(BaseModel):
    job_id: str
    preview_url: str
    warnings: List[QaWarning] = Field(default_factory=list)

class GenerateResponse(BaseModel):
    job_id: str
    artifacts: List[str]
    warnings: List[QaWarning] = Field(default_factory=list)

class IngestItem(BaseModel):
    order_ref: str
    template_id: Optional[str] = None
    sku: Optional[str] = None
    quantity: int = 1
    lines: List[TextLine] = []
    graphics_key: Optional[str] = None
    photo_asset_id: Optional[str] = None
    photo_asset_url: Optional[str] = None
    photo_filename: Optional[str] = None
    assets: List[str] = []
    # SKU enrichment
    colour: Optional[str] = None
    product_type: Optional[str] = None  # from CSV TYPE
    decoration_type: Optional[str] = None
    theme: Optional[str] = None
    processor: Optional[str] = None

class IngestResponse(BaseModel):
    items: List[IngestItem]
    warnings: List[QaWarning] = []
