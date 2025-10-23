from pathlib import Path
import json
import zipfile
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings

client = TestClient(app)


def _make_zip_with_json(zip_path: Path, data: dict):
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("personalization.json", json.dumps(data))


def test_ingest_txt_zip_parse(monkeypatch, tmp_path: Path):
    # Ensure downloads allowed and local storage
    monkeypatch.setattr(settings, "ALLOW_EXTERNAL_DOWNLOADS", True)
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")

    def fake_download(url: str, dest_path: Path, *, timeout: int, user_agent: str, retries: int = 3) -> Path:
        _make_zip_with_json(dest_path, {
            "line_1":"Loving Memories of Joan",
            "line_2":"A Very Special Friend",
            "line_3":"Sleep in Peace xxx",
            "graphic":"Rose"
        })
        return dest_path

    import app.routers.ingest_amazon as ia
    monkeypatch.setattr(ia, "download_zip", fake_download)

    tsv = "\t".join(["amazon-order-id","sku","quantity","customized-url"]) + "\n"
    row = "\t".join(["113-1111111-1111111","OD045004-PLAQUE","1","https://example.com/personalisation.zip"]) + "\n"
    txt = tsv + row

    resp = client.post("/api/ingest/amazon", json={"text": txt})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data.get("items", [])) == 1
    item = data["items"][0]
    lines = {l["id"]: l["value"] for l in item["lines"]}
    assert lines["line_1"] == "Loving Memories of Joan"
    assert lines["line_2"] == "A Very Special Friend"
    assert lines["line_3"] == "Sleep in Peace xxx"
    assert item.get("graphics_key") == "Rose"
