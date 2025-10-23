from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)

def test_generate_happy_path():
    # Ingest rows via JSON
    rows = [
        {"order_id":"113-1111111-1111111","line_item_id":"A1","template_id":"PLAQUE-140x90-V1","line_1":"In loving memory","line_2":"John K Newman","line_3":"1950-2024"},
        {"order_id":"113-1111111-1111111","line_item_id":"A2","template_id":"PLAQUE-140x90-V1","line_1":"In loving memory","line_2":"Jane K Newman","line_3":"1951-2024"},
        {"order_id":"113-1111111-1111111","line_item_id":"A3","template_id":"PLAQUE-140x90-V1","line_1":"In loving memory","line_2":"Alex Newman","line_3":"2001-2020"},
    ]
    ing = client.post("/api/ingest/amazon", json={"rows": rows})
    assert ing.status_code == 200, ing.text
    payload = ing.json()
    items = payload["items"]

    # Generate once
    resp1 = client.post("/api/jobs/generate", json={"items": items, "machine_id":"MUTOH-UJF-461", "seed":42})
    assert resp1.status_code == 200, resp1.text
    data1 = resp1.json()
    # Generate again identically
    resp2 = client.post("/api/jobs/generate", json={"items": items, "machine_id":"MUTOH-UJF-461", "seed":42})
    assert resp2.status_code == 200, resp2.text
    data2 = resp2.json()

    # Artifacts exist
    assert any(a.endswith("bed_1.png") for a in data1["artifacts"]) 
    # Determinism: compare bed_1.svg bytes
    import requests
    url1 = [a for a in data1["artifacts"] if a.endswith("bed_1.svg")][0]
    url2 = [a for a in data2["artifacts"] if a.endswith("bed_1.svg")][0]
    b1 = client.get(url1)
    b2 = client.get(url2)
    assert b1.status_code == 200 and b2.status_code == 200
    assert b1.content == b2.content
