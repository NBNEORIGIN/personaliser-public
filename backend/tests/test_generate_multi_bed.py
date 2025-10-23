from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_generate_multi_bed_and_determinism():
    # Build 20 identical items
    items = []
    for _ in range(20):
        items.append({
            "template_id":"PLAQUE-140x90-V1",
            "lines":[
                {"id":"line_1","value":"A"},
                {"id":"line_2","value":"B"},
                {"id":"line_3","value":"C"},
            ]
        })

    req = {"items": items, "machine_id":"MUTOH-UJF-461", "seed":42}

    r1 = client.post("/api/jobs/generate", json=req)
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    r2 = client.post("/api/jobs/generate", json=req)
    assert r2.status_code == 200, r2.text
    d2 = r2.json()

    # Expect bed_1.svg and bed_2.svg exist in artifacts
    a1 = d1["artifacts"]
    assert any(x.endswith("bed_1.svg") for x in a1)
    assert any(x.endswith("bed_2.svg") for x in a1)

    # Determinism: compare bed_1.svg and bed_2.svg across runs
    def get(url):
        return client.get(url)
    b1_1 = get([x for x in d1["artifacts"] if x.endswith("bed_1.svg")][0])
    b1_2 = get([x for x in d2["artifacts"] if x.endswith("bed_1.svg")][0])
    assert b1_1.status_code == 200 and b1_2.status_code == 200
    assert b1_1.content == b1_2.content

    b2_1 = get([x for x in d1["artifacts"] if x.endswith("bed_2.svg")][0])
    b2_2 = get([x for x in d2["artifacts"] if x.endswith("bed_2.svg")][0])
    assert b2_1.status_code == 200 and b2_2.status_code == 200
    assert b2_1.content == b2_2.content
