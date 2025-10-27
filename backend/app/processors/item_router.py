from __future__ import annotations
from typing import Callable, Dict, Tuple, List
from ..models import OrderItem
from ..models import IngestItem

print("[ITEM_ROUTER] Module loaded - using PDF processor for photo stakes", flush=True)

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
    print(f"[KEY_FOR_ITEM] Called for item {getattr(item, 'order_ref', 'UNKNOWN')}", flush=True)
    
    # Check for explicit processor assignment from SKU metadata
    explicit_processor = (getattr(item, "processor", None) or "").strip()
    if explicit_processor:
        print(f"[KEY_FOR_ITEM] Using explicit processor: {explicit_processor}", flush=True)
        return explicit_processor
    
    # Fallback to logic-based routing
    dt = (getattr(item, "decoration_type", None) or "").lower()
    product_type = (getattr(item, "product_type", None) or "").lower()
    colour = (getattr(item, "colour", None) or "").lower()
    
    # DEBUG: Log the actual values
    print(f"[KEY_FOR_ITEM DEBUG] dt='{dt}', product_type='{product_type}', colour='{colour}'", flush=True)
    
    # Photo stakes: specific colours + regular stake + photo decoration
    # Note: Large Stakes and Slate/Black colors will have separate processors in future
    if dt == "photo" and product_type == "regular stake":
        allowed_colours = ["copper", "gold", "silver", "stone", "marble"]
        print(f"[KEY_FOR_ITEM] Photo + Regular Stake detected, checking colour '{colour}' in {allowed_colours}", flush=True)
        if colour in allowed_colours:
            print(f"[REGISTRY V2] Routing photo stake to PDF processor", flush=True)
            return "photo_stakes_pdf_v1"  # Use PDF processor for better reliability
        else:
            print(f"[KEY_FOR_ITEM] Colour '{colour}' not in allowed list, falling through", flush=True)
    
    # Regular graphic stakes
    if dt == "graphic":
        return "regular_stake_v1"
    
    # Default to text only
    return "text_only_v1"
