from __future__ import annotations
from xml.sax.saxutils import escape
from ..models import OrderItem
from .registry import register

NAME = "uv_regular"
VERSION = "1.0.0"

SVG_W = 140
SVG_H = 90
R = 6


def render(item: OrderItem) -> str:
    # Extract lines by id
    text_map = {l.id: l.value for l in item.lines}
    l1 = escape(text_map.get("line_1", ""))
    l2 = escape(text_map.get("line_2", ""))
    l3 = escape(text_map.get("line_3", ""))
    # Center positions (mm units)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}mm" height="{SVG_H}mm" viewBox="0 0 {SVG_W} {SVG_H}">
  <rect x="0" y="0" width="{SVG_W}" height="{SVG_H}" rx="{R}" ry="{R}" fill="white" stroke="#ccc"/>
  <g font-family="DejaVu Sans" fill="#000" text-anchor="middle">
    <text x="{SVG_W/2}" y="{SVG_H/2 - 10}" font-size="6">{l1}</text>
    <text x="{SVG_W/2}" y="{SVG_H/2}" font-size="5">{l2}</text>
    <text x="{SVG_W/2}" y="{SVG_H/2 + 10}" font-size="6">{l3}</text>
  </g>
</svg>'''
    return svg

# auto-register
register(NAME, VERSION, render)
