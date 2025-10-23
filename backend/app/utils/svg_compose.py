from __future__ import annotations
from typing import List, Tuple
from xml.sax.saxutils import escape
from cairosvg import svg2png
from pathlib import Path

BED_W = 480
BED_H = 330


def compose_bed_svg(placed: List[Tuple[float, float, float, float, str]], keepouts: List[Tuple[float, float, float, float]]) -> str:
    # placed entries: (x,y,w,h,id)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{BED_W}mm" height="{BED_H}mm" viewBox="0 0 {BED_W} {BED_H}">']
    parts.append(f'<rect x="0" y="0" width="{BED_W}" height="{BED_H}" fill="white" stroke="#333" stroke-width="0.5"/>')
    # keepouts shaded
    for (kx, ky, kw, kh) in keepouts:
        parts.append(f'<rect x="{kx}" y="{ky}" width="{kw}" height="{kh}" fill="#ccc" opacity="0.4"/>')
    # registration marks (small crosses) near printable corners (inside area)
    marks = [(5,5), (BED_W-5,5), (5,BED_H-5), (BED_W-5,BED_H-5)]
    for (mx,my) in marks:
        parts.append(f'<path d="M {mx-3} {my} L {mx+3} {my} M {mx} {my-3} L {mx} {my+3}" stroke="#000" stroke-width="0.5"/>')
    # slot outlines
    for (x,y,w,h,_id) in placed:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#3da9fc" stroke-dasharray="1.5,1.5" stroke-width="0.6"/>')
    parts.append('</svg>')
    return "".join(parts)


def save_svg_and_png(svg_text: str, svg_path: Path, png_path: Path) -> None:
    svg_path.write_text(svg_text, encoding="utf-8")
    svg2png(bytestring=svg_text.encode("utf-8"), write_to=str(png_path))


def svg_to_png_bytes(svg_text: str) -> bytes:
    """Render PNG bytes from SVG text deterministically (no timestamps)."""
    return svg2png(bytestring=svg_text.encode("utf-8"))
