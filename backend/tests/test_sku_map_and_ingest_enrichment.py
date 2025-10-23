from pathlib import Path
import json
import io
import zipfile
import time
import pytest
from fastapi.testclient import TestClient

from app.utils import sku_map as _sku_map
from app.settings import settings as _settings
from app.main import app


def test_sku_meta_loads_columns(tmp_path: Path, monkeypatch):
    # Prepare temp SKULIST.csv with new columns
    csv_text = """SKU,COLOUR,TYPE,DecorationType,Theme
OD045004_1Silver,Silver,Regular Stake,Graphic,Pet
om008015uk   regular   gold,Gold,Regular Stake,Photo,Pet
""".strip()
    (tmp_path / "SKULIST.csv").write_text(csv_text, encoding="utf-8")

    # Point DATA_DIR to tmp so loader finds our CSV
    # Point both settings references used by code to tmp DATA_DIR
    monkeypatch.setattr(_settings, "DATA_DIR", tmp_path, raising=False)
    monkeypatch.setattr(_sku_map, "settings", _settings, raising=False)
    monkeypatch.setattr(_sku_map, "_SKU_CACHE", None)
    monkeypatch.setattr(_sku_map, "_SKU_MTIME", None)

    _sku_map.init()  # load once

    m1 = _sku_map.get_meta_for_sku("OD045004_1Silver")
    assert m1.get("COLOUR") == "Silver"
    assert m1.get("TYPE") == "Regular Stake"
    assert m1.get("DecorationType") == "Graphic"
    assert m1.get("Theme") == "Pet"

    # normalization: spaces/case-insensitive
    m2 = _sku_map.get_meta_for_sku("  OM008015UK   Regular   Gold  ")
    assert m2.get("COLOUR") == "Gold"
    assert m2.get("DecorationType") == "Photo"


def test_ingest_enriches_item_fields(tmp_path: Path, monkeypatch):
    # Write SKULIST.csv (Photo and Graphic rows)
    csv_text = """SKU,COLOUR,TYPE,DecorationType,Theme
SKU-PHOTO,Black,Regular Stake,Photo,Pet
SKU-GRAPHIC,Silver,Regular Stake,Graphic,Pet
""".strip()
    (tmp_path / "SKULIST.csv").write_text(csv_text, encoding="utf-8")

    # Minimal catalog with max lens for PLAQUE-140x90-V1 to trigger run_qa
    catalog = {
        "templates": [
            {
                "id": "PLAQUE-140x90-V1",
                "options": {
                    "fields": [
                        {"id": "line_1", "label": "Line 1", "type": "text", "maxLen": 32},
                        {"id": "line_2", "label": "Line 2", "type": "text", "maxLen": 32},
                        {"id": "line_3", "label": "Line 3", "type": "text", "maxLen": 32},
                    ]
                },
            }
        ]
    }
    (tmp_path / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")

    # Point DATA_DIR to tmp so ingest uses our CSV and catalog
    monkeypatch.setattr(_settings, "DATA_DIR", tmp_path, raising=False)
    monkeypatch.setattr(_sku_map, "settings", _settings, raising=False)

    # Reset and init SKU map
    monkeypatch.setattr(_sku_map, "_SKU_CACHE", None)
    monkeypatch.setattr(_sku_map, "_SKU_MTIME", None)
    _sku_map.init()

    # Disable downloads to avoid network
    monkeypatch.setattr(_settings, "ALLOW_EXTERNAL_DOWNLOADS", False, raising=False)

    client = TestClient(app)

    # Provide two rows: one Photo type without photo, one Graphic without graphics_key
    txt = (
        "amazon-order-id\tsku\tquantity\tcustomized-url\n"
        "ORDER-1\tSKU-PHOTO\t1\t\n"
        "ORDER-2\tSKU-GRAPHIC\t1\t\n"
    )

    resp = client.post("/api/ingest/amazon", json={"text": txt})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    items = data.get("items") or []
    warns = data.get("warnings") or []

    assert len(items) == 2

    # Enrichment present
    it_photo = items[0]
    assert it_photo.get("colour") == "Black"
    assert it_photo.get("product_type") == "Regular Stake"
    assert (it_photo.get("decoration_type") or "").lower() == "photo"
    assert (it_photo.get("theme") or "").lower() == "pet"

    it_graphic = items[1]
    assert it_graphic.get("colour") == "Silver"
    assert (it_graphic.get("decoration_type") or "").lower() == "graphic"

    # Warnings: PHOTO_MISSING for photo item (no photo), GRAPHIC_MISSING for graphic item (no graphics)
    codes = [w.get("code") for w in warns]
    assert "PHOTO_MISSING" in codes
    assert "GRAPHIC_MISSING" in codes
