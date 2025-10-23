from app.routers.jobs import TEMPLATE_MAP
from app.processors.registry import get

def test_svg_determinism():
    tpl = TEMPLATE_MAP["PLAQUE-140x90-V1"]
    proc = get(tpl["processor"]["name"], tpl["processor"]["version"])
    from app.models import OrderItem, LineField
    item = OrderItem(template_id="PLAQUE-140x90-V1", lines=[
        LineField(id="line_1", value="In loving memory"),
        LineField(id="line_2", value="John K Newman"),
        LineField(id="line_3", value="1950-2024"),
    ])
    svg1 = proc(item)
    svg2 = proc(item)
    assert svg1 == svg2
