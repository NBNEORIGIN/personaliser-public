from pathlib import Path
import sys

# Ensure 'backend/' is on sys.path when running from repo root
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
import json
import zipfile
import io
from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings
from app.utils import sku_map as _sku_map


def test_order_ref_is_order_id_only():
    client = TestClient(app)
    tsv = "\t".join(["amazon-order-id","sku","quantity","customized-url"]) + "\n"
    row = "\t".join(["123-1111111-2222222","ABC","1",""]) + "\n"
    txt = tsv + row
    resp = client.post("/api/ingest/amazon", json={"text": txt})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data.get("items", [])) == 1
    assert data["items"][0]["order_ref"] == "123-1111111-2222222"


def test_csv_enrichment_applies(tmp_path: Path, monkeypatch):
    # Prepare SKULIST.csv
    csv_text = """SKU,COLOUR,TYPE,DecorationType,Theme
OD045004_1Silver,Silver,Regular Stake,Graphic,Heart
""".strip()
    (tmp_path / "SKULIST.csv").write_text(csv_text, encoding="utf-8")

    # Point DATA_DIR and reset sku map
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path, raising=False)
    monkeypatch.setattr(_sku_map, "settings", settings, raising=False)
    monkeypatch.setattr(_sku_map, "_SKU_CACHE", None)
    monkeypatch.setattr(_sku_map, "_SKU_MTIME", None)
    _sku_map.init()

    client = TestClient(app)
    tsv = "\t".join(["amazon-order-id","sku","quantity","customized-url"]) + "\n"
    row = "\t".join(["113-1111111-1111111","OD045004_1Silver","1",""]) + "\n"
    txt = tsv + row
    resp = client.post("/api/ingest/amazon", json={"text": txt})
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    assert item.get("colour") == "Silver"
    assert item.get("product_type") == "Regular Stake"
    assert (item.get("decoration_type") or "").lower() == "graphic"
    assert item.get("theme") == "Heart"


def _make_zip_with_personalisation(dest: Path, *, image_name: str = "x.jpg") -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as z:
        # Add the image
        z.writestr(image_name, b"\x89IMGDATA")
        # Add personalization.json with ImageCustomization
        pdata = {
            "customizationData": {
                "items": [
                    {
                        "__typename": "ImageCustomization",
                        "image": {
                            "imageName": image_name,
                            "buyerFilename": "buyer-fallback.jpg"
                        }
                    }
                ]
            }
        }
        z.writestr("personalization.json", json.dumps(pdata))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(buf.getvalue())


def test_photo_filename_and_url(tmp_path: Path, monkeypatch):
    # Enable downloads and local storage
    monkeypatch.setattr(settings, "ALLOW_EXTERNAL_DOWNLOADS", True, raising=False)
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local", raising=False)
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path, raising=False)

    # Monkeypatch download_zip to write our ZIP
    def fake_download(url: str, dest_path: Path, *, timeout: int, user_agent: str, retries: int = 3, max_mb: int | None = None) -> Path:
        _make_zip_with_personalisation(dest_path, image_name="x.jpg")
        return dest_path

    import app.routers.ingest_amazon as ia
    monkeypatch.setattr(ia, "download_zip", fake_download)

    client = TestClient(app)
    tsv = "\t".join(["amazon-order-id","sku","quantity","customized-url"]) + "\n"
    row = "\t".join(["113-1111111-1111111","OD045004_1Silver","1","https://example.com/personalisation.zip"]) + "\n"
    txt = tsv + row
    resp = client.post("/api/ingest/amazon", json={"text": txt})
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]

    # Filename and URL checks
    assert item.get("photo_filename") == "x.jpg"
    url = item.get("photo_asset_url") or ""
    assert url.startswith("/static/photos/")
    # Ensure no literal 'photo' in filename or in URL beyond the folder prefix
    assert "photo" not in (item.get("photo_filename") or "").lower()
    remainder = url[len("/static/photos/"):]
    assert "photo" not in remainder.lower()
