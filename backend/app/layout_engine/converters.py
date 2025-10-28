"""
Converters to transform order data into ContentJSON format.
"""

from typing import List, Dict, Any
from .models import ContentJSON, SlotContent


def convert_regular_stakes_order(items: List[Dict[str, Any]]) -> ContentJSON:
    """
    Convert regular stakes order items to ContentJSON.
    
    Args:
        items: List of order items with line1, line2, line3, graphics_key
        
    Returns:
        ContentJSON with slots populated
    """
    slots = []
    
    for idx, item in enumerate(items):
        # Extract text lines
        line1 = item.get("line1", "") or ""
        line2 = item.get("line2", "") or ""
        line3 = item.get("line3", "") or ""
        
        # Extract graphic key
        graphic_key = item.get("graphics_key", "") or item.get("graphic", "") or ""
        
        # Create slot
        slot = SlotContent(
            slot_index=idx,
            line1=line1,
            line2=line2,
            line3=line3,
            graphic=graphic_key
        )
        
        slots.append(slot)
    
    return ContentJSON(slots=slots)


def convert_photo_stakes_order(items: List[Dict[str, Any]]) -> ContentJSON:
    """
    Convert photo stakes order items to ContentJSON.
    
    Args:
        items: List of order items with line1, line2, line3, photo_path
        
    Returns:
        ContentJSON with slots populated
    """
    slots = []
    
    for idx, item in enumerate(items):
        # Extract text lines
        line1 = item.get("line1", "") or ""
        line2 = item.get("line2", "") or ""
        line3 = item.get("line3", "") or ""
        
        # Extract photo path
        photo_path = item.get("photo_path", "") or item.get("photo", "") or ""
        
        # Create slot
        slot = SlotContent(
            slot_index=idx,
            line1=line1,
            line2=line2,
            line3=line3,
            photo=photo_path
        )
        
        slots.append(slot)
    
    return ContentJSON(slots=slots)
