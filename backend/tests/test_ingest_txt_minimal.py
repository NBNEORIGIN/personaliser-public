from pathlib import Path
import io
import zipfile
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings

client = TestClient(app)


def _make_zip_with_json(zip_path: Path, data: dict):
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("personalisation.json", json.dumps(data))


def test_ingest_txt_minimal(monkeypatch, tmp_path: Path):
    # Monkeypatch download_zip to write a tiny zip with personalisation.json
    def fake_download(url: str, dest_path: Path, *, timeout: int, user_agent: str, retries: int = 3) -> Path:
        _make_zip_with_json(dest_path, {"line_1": "Hello", "line_2": "World", "line_3": "2024"})
        return dest_path

    import app.routers.ingest_amazon as ia
    monkeypatch.setattr(ia, "download_zip", fake_download)

    tsv = "\t".join([
        "amazon-order-id",
        "sku",
        "quantity",
        "customized-url",
    ]) + "\n"
    row1 = "\t".join(["113-1111111-1111111", "OD045004-PLAQUE", "1", "https://example.com/personalisation.zip"]) + "\n"
    row2 = "\t".join(["113-1111111-1111111", "OD045004-PLAQUE", "1", ""]) + "\n"
    txt = tsv + row1 + row2

    resp = client.post("/api/ingest/amazon", json={"text": txt})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "items" in data and "warnings" in data
    assert len(data["items"]) == 2

    # First item should have parsed lines from JSON
    it0 = data["items"][0]
    lines0 = {l["id"]: l["value"] for l in it0["lines"]}
    assert lines0["line_1"] == "Hello"
    assert lines0["line_2"] == "World"
    assert lines0["line_3"] == "2024"

    # Second item should warn missing customized-url
    codes = [w["code"] for w in data["warnings"]]
    assert "MISSING_CUSTOMIZED_URL" in codes or any("MISSING_CUSTOMIZED_URL" == w["code"] and ":1" in (it0.get("order_ref") or "") for w in data["warnings"])  # tolerant to ordering

    # Assets directory should exist for first row
    dl_dir = settings.DATA_DIR / "storage" / "downloads" / "113-1111111-1111111" / "0"
    assert dl_dir.exists()
