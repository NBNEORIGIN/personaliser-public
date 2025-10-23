from pathlib import Path
import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings

client = TestClient(app)


def _make_zip_with_bytes(zip_path: Path, size: int):
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    payload = b"X" * size
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("payload.bin", payload)


def test_zip_too_large(monkeypatch, tmp_path: Path):
    # Set a very small MAX_ZIP_MB so our tiny file exceeds the limit
    monkeypatch.setattr(settings, "MAX_ZIP_MB", 0)  # 0 MB total allowed

    def fake_download(url: str, dest_path: Path, *, timeout: int, user_agent: str, retries: int = 3) -> Path:
        _make_zip_with_bytes(dest_path, size=200)  # any non-zero triggers > 0MB
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
    txt = tsv + row1

    resp = client.post("/api/ingest/amazon", json={"text": txt})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    codes = [w["code"] for w in data.get("warnings", [])]
    assert "ZIP_TOO_LARGE" in codes
