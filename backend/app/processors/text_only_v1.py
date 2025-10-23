from __future__ import annotations
from typing import List, Tuple, Any
from pathlib import Path
import math
import svgwrite

from ..settings import settings
from ..utils import storage
from .registry import register_batch
from .base import write_batch_csv


BED_W_MM = 439.8
BED_H_MM = 289.9
MARGIN_MM = 5.0
GUTTER_MM = 5.0
CELL_W_MM = 140.0
CELL_H_MM = 90.0
COLS = 3


def _cell_origin(col: int, row: int) -> Tuple[float, float]:
    x = MARGIN_MM + col * (CELL_W_MM + GUTTER_MM)
    y = MARGIN_MM + row * (CELL_H_MM + GUTTER_MM)
    return x, y


def _text_lines_map(it: Any) -> Tuple[str, str, str]:
    lines = getattr(it, "lines", []) or []
    mp = {getattr(l, "id", getattr(l, "get", lambda k: None)("id")): getattr(l, "value", getattr(l, "get", lambda k: None)("value")) for l in lines}
    return mp.get("line_1", ""), mp.get("line_2", ""), mp.get("line_3", "")


def run(items: List[Any], cfg: dict) -> Tuple[str, str, List[str]]:
    job_id = cfg["job_id"]
    out_dir: Path = cfg["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    # Basic SVG document sized to bed
    dwg = svgwrite.Drawing(size=(f"{BED_W_MM}mm", f"{BED_H_MM}mm"), profile="full")

    # Optional: draw bed outline (invisible stroke to ensure consistent ordering)
    dwg.add(dwg.rect(insert=(0, 0), size=(f"{BED_W_MM}mm", f"{BED_H_MM}mm"), fill="white"))

    # Place items in deterministic order (input order)
    rows_csv: List[dict] = []
    for idx, it in enumerate(items):
        col = idx % COLS
        row = idx // COLS
        x, y = _cell_origin(col, row)

        # Cell border (light, optional)
        dwg.add(dwg.rect(insert=(f"{x}mm", f"{y}mm"), size=(f"{CELL_W_MM}mm", f"{CELL_H_MM}mm"), fill="none", stroke="none"))

        # Text placement (centered). Font sizes in mm (approx legacy scale)
        l1, l2, l3 = _text_lines_map(it)
        cx = x + CELL_W_MM / 2.0
        # Baseline positions within the cell
        ty1 = y + 30.0
        ty2 = y + 45.0
        ty3 = y + 60.0

        def add_text(txt: str, font_mm: float, ty: float):
            if not txt:
                return
            t = dwg.text(
                txt,
                insert=(f"{cx}mm", f"{ty}mm"),
                text_anchor="middle",
                dominant_baseline="middle",
                style=f"font-family: Arial; font-size:{font_mm}mm;"
            )
            dwg.add(t)

        add_text(l1, 7.94, ty1)
        add_text(l2, 5.0, ty2)
        add_text(l3, 5.0, ty3)

        rows_csv.append({
            "order_ref": getattr(it, "order_ref", "") or "",
            "sku": (getattr(it, "sku", None) or ""),
            "graphics_key": (getattr(it, "graphics_key", None) or getattr(it, "graphic", None) or ""),
            "colour": (getattr(it, "colour", None) or ""),
            "type": (getattr(it, "product_type", None) or ""),
            "decoration": (getattr(it, "decoration_type", None) or ""),
            "theme": (getattr(it, "theme", None) or ""),
            "line_1": l1,
            "line_2": l2,
            "line_3": l3,
            "cell_row": row,
            "cell_col": col,
        })

    # Save outputs deterministically
    svg_path = out_dir / "bed_1.svg"
    dwg.saveas(svg_path)
    csv_path = out_dir / "batch.csv"
    write_batch_csv(rows_csv, csv_path)

    # Publish
    svg_url = storage.put_artifact(job_id, svg_path)
    csv_url = storage.put_artifact(job_id, csv_path)
    return svg_url, csv_url, []


register_batch("text_only_v1", run)
