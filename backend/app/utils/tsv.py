from __future__ import annotations
from typing import List, Tuple

def parse_tsv(text: str) -> Tuple[List[str], List[List[str]]]:
    """
    Parse a tab-delimited text into headers and rows.
    - Tolerates BOM, CRLF/LF, empty trailing lines.
    - Returns (headers, rows) where rows is a list of lists aligned with headers.
    """
    if not isinstance(text, str):
        text = text.decode("utf-8", errors="ignore")
    # Strip BOM if present
    if text and text[0] == "\ufeff":
        text = text.lstrip("\ufeff")
    # Normalize newlines
    lines = [ln for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if ln != ""]
    if not lines:
        return [], []
    headers = [h.strip() for h in lines[0].split("\t")]
    rows: List[List[str]] = []
    for ln in lines[1:]:
        cols = ln.split("\t")
        # pad/truncate to header length
        if len(cols) < len(headers):
            cols = cols + [""] * (len(headers) - len(cols))
        elif len(cols) > len(headers):
            cols = cols[:len(headers)]
        rows.append([c.strip() for c in cols])
    return headers, rows
