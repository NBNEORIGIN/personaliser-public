"""
CSV/table parser for bulk content upload.

Maps CSV columns to template element IDs.
"""

import csv
import io
from typing import List, Dict, Any
from .models import ContentJSON, SlotContent


def parse_csv_to_content(
    csv_data: str,
    column_mapping: Dict[str, str],
    has_header: bool = True,
    user_id: int = None,
    base_url: str = ""
) -> ContentJSON:
    """
    Parse CSV data and map columns to element IDs.
    
    Args:
        csv_data: CSV string data
        column_mapping: Dict mapping CSV column names/indices to element IDs
                       e.g., {"Name": "line1", "Date": "line2", "Photo": "photo"}
        has_header: Whether CSV has header row
        
    Returns:
        ContentJSON with slots populated from CSV rows
        
    Example:
        csv_data = "Name,Date,Message\\nJohn,2024,Hello\\nJane,2025,World"
        mapping = {"Name": "line1", "Date": "line2", "Message": "line3"}
        content = parse_csv_to_content(csv_data, mapping)
    """
    # Strip BOM (Byte Order Mark) if present
    if csv_data.startswith('\ufeff'):
        csv_data = csv_data[1:]
    
    slots = []
    reader = csv.DictReader(io.StringIO(csv_data)) if has_header else csv.reader(io.StringIO(csv_data))
    
    for slot_index, row in enumerate(reader):
        slot_data = {"slot_index": slot_index}
        
        if has_header:
            # Row is a dict with column names as keys
            if slot_index == 0:
                print(f"[CSV PARSER] First row keys: {list(row.keys())}")
                print(f"[CSV PARSER] First row values: {list(row.values())}")
            
            for csv_col, element_id in column_mapping.items():
                if csv_col in row:
                    value = row[csv_col]
                    
                    # Check if column name suggests it's a graphic
                    is_graphic_column = 'graphic' in csv_col.lower() or 'image' in csv_col.lower()
                    
                    # Handle graphics: if value is just a filename (e.g., "Cat.png" or "Cat"), 
                    # convert to full path
                    if value and not value.startswith('/') and not value.startswith('http'):
                        if is_graphic_column:
                            # If no extension, try common image extensions
                            if not value.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                                # Try adding .png first (most common)
                                value = f"{value}.png"
                                print(f"[CSV PARSER] No extension found, trying: {value}", flush=True)
                            
                            # Use user-specific path if user_id provided, otherwise use public
                            if user_id:
                                relative_path = f"/static/graphics/user_{user_id}/{value}"
                            else:
                                relative_path = f"/static/graphics/public/{value}"
                            
                            # Make absolute URL if base_url provided
                            if base_url:
                                value = f"{base_url}{relative_path}"
                            else:
                                value = relative_path
                            
                            print(f"[CSV PARSER] Converted graphic: {row[csv_col]} -> {value}", flush=True)
                    
                    if slot_index == 0:
                        print(f"[CSV PARSER] Mapping '{csv_col}' -> '{element_id}' = '{value}'")
                    slot_data[element_id] = value
                    
                    # Extra debug for graphics
                    if is_graphic_column:
                        print(f"[CSV PARSER] Slot {slot_index}: Set {element_id} = {value}", flush=True)
                else:
                    if slot_index == 0:
                        print(f"[CSV PARSER] Column '{csv_col}' NOT FOUND in row")
        else:
            # Row is a list, mapping uses indices
            for csv_idx, element_id in column_mapping.items():
                try:
                    idx = int(csv_idx)
                    if idx < len(row):
                        slot_data[element_id] = row[idx]
                except (ValueError, IndexError):
                    continue
        
        slots.append(SlotContent(**slot_data))
    
    return ContentJSON(slots=slots)


def parse_tsv_to_content(
    tsv_data: str,
    column_mapping: Dict[str, str],
    has_header: bool = True
) -> ContentJSON:
    """
    Parse TSV (tab-separated) data and map columns to element IDs.
    
    Args:
        tsv_data: TSV string data
        column_mapping: Dict mapping TSV column names/indices to element IDs
        has_header: Whether TSV has header row
        
    Returns:
        ContentJSON with slots populated from TSV rows
    """
    slots = []
    reader = csv.DictReader(io.StringIO(tsv_data), delimiter='\t') if has_header else csv.reader(io.StringIO(tsv_data), delimiter='\t')
    
    for slot_index, row in enumerate(reader):
        slot_data = {"slot_index": slot_index}
        
        if has_header:
            for tsv_col, element_id in column_mapping.items():
                if tsv_col in row:
                    slot_data[element_id] = row[tsv_col]
        else:
            for tsv_idx, element_id in column_mapping.items():
                try:
                    idx = int(tsv_idx)
                    if idx < len(row):
                        slot_data[element_id] = row[idx]
                except (ValueError, IndexError):
                    continue
        
        slots.append(SlotContent(**slot_data))
    
    return ContentJSON(slots=slots)


def parse_table_to_content(
    table_data: List[List[str]],
    column_mapping: Dict[int, str],
    has_header: bool = True
) -> ContentJSON:
    """
    Parse table data (list of lists) and map columns to element IDs.
    
    Args:
        table_data: List of rows, each row is a list of values
        column_mapping: Dict mapping column indices to element IDs
                       e.g., {0: "line1", 1: "line2", 2: "photo"}
        has_header: Whether first row is header
        
    Returns:
        ContentJSON with slots populated from table rows
    """
    slots = []
    start_row = 1 if has_header else 0
    
    for slot_index, row in enumerate(table_data[start_row:]):
        slot_data = {"slot_index": slot_index}
        
        for col_idx, element_id in column_mapping.items():
            if col_idx < len(row):
                slot_data[element_id] = row[col_idx]
        
        slots.append(SlotContent(**slot_data))
    
    return ContentJSON(slots=slots)


def auto_detect_mapping(
    csv_data: str,
    element_ids: List[str],
    has_header: bool = True
) -> Dict[str, str]:
    """
    Auto-detect column mapping based on element IDs.
    
    Tries to match CSV column names to element IDs using fuzzy matching.
    
    Args:
        csv_data: CSV string data
        element_ids: List of element IDs from template
        has_header: Whether CSV has header row
        
    Returns:
        Dict mapping CSV columns to element IDs
    """
    if not has_header:
        # Without headers, map by position
        return {str(i): element_id for i, element_id in enumerate(element_ids)}
    
    reader = csv.DictReader(io.StringIO(csv_data))
    headers = reader.fieldnames or []
    
    mapping = {}
    for header in headers:
        header_lower = header.lower().strip()
        
        # Try exact match first
        for element_id in element_ids:
            if element_id.lower() == header_lower:
                mapping[header] = element_id
                break
        
        # Try fuzzy match (contains)
        if header not in mapping:
            for element_id in element_ids:
                if element_id.lower() in header_lower or header_lower in element_id.lower():
                    mapping[header] = element_id
                    break
    
    return mapping
