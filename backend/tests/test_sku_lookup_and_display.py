from pathlib import Path
import sys

# Ensure 'backend/' is on sys.path when running from repo root
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings
from app.utils import sku_map as _sku_map


def test_sku_enrichment_and_order_ref(tmp_path: Path, monkeypatch):
    # Create temp SKULIST.csv
    csv_text = """SKU,COLOUR,TYPE,DecorationType,Theme
M0634S - CAT - SILVER,Silver,Regular Stake,Graphic,Feline
""".strip()
    csv_path = tmp_path / "SKULIST.csv"
    csv_path.write_text(csv_text, encoding="utf-8")

    # Point settings.SKULIST_PATH to temp file and reset sku_map cache
    monkeypatch.setattr(settings, "SKULIST_PATH", csv_path, raising=False)
    # ensure sku_map sees the updated settings and resets caches
    monkeypatch.setattr(_sku_map, "settings", settings, raising=False)
    monkeypatch.setattr(_sku_map, "_SKU_CACHE", None)
    monkeypatch.setattr(_sku_map, "_SKU_MTIME", None)

    client = TestClient(app)
    # Build a TSV row with the exact SKU
    header = "\t".join(["amazon-order-id","sku","quantity","customized-url"]) + "\n"
    row = "\t".join(["026-9691952-7693142","M0634S - CAT - SILVER","1",""]) + "\n"
    txt = header + row

    resp = client.post("/api/ingest/amazon", json={"text": txt})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data.get("items", [])) == 1
    item = data["items"][0]

    # Enrichment assertions
    assert item.get("colour") == "Silver"
    assert item.get("product_type") == "Regular Stake"
    assert item.get("decoration_type") == "Graphic"
    assert item.get("theme") == "Feline"

    # order_ref must be raw order id only
    assert item.get("order_ref") == "026-9691952-7693142"
