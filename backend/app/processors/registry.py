from __future__ import annotations
from typing import Callable, Dict, Tuple, List
from ..models import OrderItem
from ..models import IngestItem

RenderFn = Callable[[OrderItem], str]

_registry: Dict[Tuple[str, str], RenderFn] = {}
BatchProcessorFn = Callable[[List[IngestItem], dict], Tuple[str, str, list[str]]]
_batch_registry: Dict[str, BatchProcessorFn] = {}

def register(name: str, version: str, fn: RenderFn) -> None:
    _registry[(name, version)] = fn

def get(name: str, version: str) -> RenderFn:
    key = (name, version)
    if key not in _registry:
        raise KeyError(f"Processor not found: {name} v{version}")
    return _registry[key]

def register_batch(key: str, fn: BatchProcessorFn) -> None:
    _batch_registry[key] = fn

def get_batch(key: str) -> BatchProcessorFn:
    if key not in _batch_registry:
        raise KeyError(f"Batch processor not found: {key}")
    return _batch_registry[key]

def key_for_item(item) -> str:
    """
    Route items to appropriate processor based on SKU attributes.
    
    Priority:
    1. Explicit Processor column in SKULIST.csv (if specified)
    2. Logic-based routing (fallback):
       - Photo Stakes: COLOUR in (Copper, Gold, Silver, Stone, Marble) + Type=Regular Stake + DecorationType=Photo
       - Regular Stakes: DecorationType=Graphic
       - Text Only: Everything else
    """
    # Check for explicit processor assignment from SKU metadata
    explicit_processor = (getattr(item, "processor", None) or "").strip()
    if explicit_processor:
        return explicit_processor
    
    # Fallback to logic-based routing
    dt = (getattr(item, "decoration_type", None) or "").lower()
    product_type = (getattr(item, "product_type", None) or "").lower()
    colour = (getattr(item, "colour", None) or "").lower()
    
    # Photo stakes: specific colours + regular stake + photo decoration
    # Note: Large Stakes and Slate/Black colors will have separate processors in future
    if dt == "photo" and product_type == "regular stake":
        allowed_colours = ["copper", "gold", "silver", "stone", "marble"]
        if colour in allowed_colours:
            return "photo_stakes_pdf_v1"  # Use PDF processor for better reliability
    
    # Regular graphic stakes
    if dt == "graphic":
        return "regular_stake_v1"
    
    # Default to text only
    return "text_only_v1"
