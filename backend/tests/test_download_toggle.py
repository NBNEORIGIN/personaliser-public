import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings

client = TestClient(app)


def test_downloads_disabled(monkeypatch):
    # Disable external downloads
    monkeypatch.setattr(settings, "ALLOW_EXTERNAL_DOWNLOADS", False)

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

    # Should still produce items and an info warning for downloads disabled
    assert len(data.get("items", [])) == 1
    codes = [w["code"] for w in data.get("warnings", [])]
    assert "DOWNLOADS_DISABLED" in codes
