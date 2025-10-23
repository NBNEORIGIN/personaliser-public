from pathlib import Path
import sys
import re

# Ensure 'backend/' on path
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.processors import registry as reg
from app.settings import settings


def _make_items(n=3, key_prefix="rose"):
    items = []
    for i in range(n):
        items.append({
            "template_id": "PLAQUE-140x90-V1",
            "order_ref": f"026-9691952-769314{i}",
            "lines": [
                {"id": "line_1", "value": f"In loving memory {i}"},
                {"id": "line_2", "value": f"John Doe {i}"},
                {"id": "line_3", "value": f"1950-2024"},
            ],
            "sku": f"SKU-{i}",
            "graphics_key": f"{key_prefix}{i}",
            "colour": "Silver",
            "product_type": "Regular Stake",
            "decoration_type": "Graphic",
            "theme": "Floral",
        })
    return items


def test_regular_stake_batch_outputs(tmp_path: Path):
    client = TestClient(app)

    # Skip if regular_stake_v1 not registered yet (pending legacy port)
    try:
        reg.get_batch("regular_stake_v1")
    except KeyError:
        import pytest
        pytest.skip("regular_stake_v1 not implemented; skipping image embed assertions")

    payload = {"items": _make_items(3), "machine_id": "MUTOH-UJF-461", "seed": 42}
    r1 = client.post("/api/jobs/generate", json=payload)
    assert r1.status_code == 200, r1.text
    data1 = r1.json()
    arts = data1.get("artifacts", [])
    # Expect bed_1.svg and batch.csv URLs
    svg_url = next((a for a in arts if a.endswith("/bed_1.svg")), None)
    csv_url = next((a for a in arts if a.endswith("/batch.csv")), None)
    assert svg_url and csv_url

    # Fetch SVG contents
    svg_path = settings.DATA_DIR / svg_url.lstrip("/static/")
    assert svg_path.exists(), f"Missing {svg_path}"
    svg = svg_path.read_text(encoding="utf-8")

    # Embedded images count equals items placed
    embeds = re.findall(r"data:image/png;base64,", svg)
    assert len(embeds) == 3
    assert "In loving memory 0" in svg

    # CSV row count equals items placed (+1 header)
    csv_path = settings.DATA_DIR / csv_url.lstrip("/static/")
    assert csv_path.exists()
    rows = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1 + 3

    # Determinism: re-run with same payload/seed and compare bytes
    r2 = client.post("/api/jobs/generate", json=payload)
    assert r2.status_code == 200
    data2 = r2.json()
    svg_url2 = next((a for a in data2.get("artifacts", []) if a.endswith("/bed_1.svg")), None)
    svg_path2 = settings.DATA_DIR / svg_url2.lstrip("/static/")
    assert svg_path2.exists()
    assert svg_path.read_bytes() == svg_path2.read_bytes()


def test_text_only_batch_outputs(tmp_path: Path):
    client = TestClient(app)
    # Use text_only route by setting decoration_type != graphic/photo
    items = _make_items(3, key_prefix="noop")
    for it in items:
        it["decoration_type"] = "Text"
        it["graphics_key"] = ""
    payload = {"items": items, "machine_id": "MUTOH-UJF-461", "seed": 42}
    r1 = client.post("/api/jobs/generate", json=payload)
    assert r1.status_code == 200, r1.text
    data1 = r1.json()
    arts = data1.get("artifacts", [])
    svg_url = next((a for a in arts if a.endswith("/bed_1.svg")), None)
    csv_url = next((a for a in arts if a.endswith("/batch.csv")), None)
    assert svg_url and csv_url

    svg_path = settings.DATA_DIR / svg_url.lstrip("/static/")
    assert svg_path.exists()
    svg = svg_path.read_text(encoding="utf-8")
    assert "In loving memory 0" in svg

    csv_path = settings.DATA_DIR / csv_url.lstrip("/static/")
    rows = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1 + 3

    # Determinism
    r2 = client.post("/api/jobs/generate", json=payload)
    assert r2.status_code == 200
    svg_url2 = next((a for a in r2.json().get("artifacts", []) if a.endswith("/bed_1.svg")), None)
    svg_path2 = settings.DATA_DIR / svg_url2.lstrip("/static/")
    assert svg_path.read_bytes() == svg_path2.read_bytes()
