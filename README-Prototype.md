# Bed-Optimised Batch Production Prototype

## Run

- docker compose up --build
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## HTTPS downloads

- The backend image includes `ca-certificates` so it can fetch `customized-url` over HTTPS when allowed.

### Enable external downloads

- Windows PowerShell:

```powershell
docker compose down
$env:ALLOW_EXTERNAL_DOWNLOADS = "true"
docker compose up --build
```

- macOS/Linux:

```bash
ALLOW_EXTERNAL_DOWNLOADS=true docker compose up --build
```

## API
- GET /api/catalog
- POST /api/jobs/preview { template_id, lines:[{id,value}...] }
- POST /api/jobs/generate { items:[...], machine_id:"MUTOH-UJF-461", seed:42 }

## Artifacts
- Saved under backend/app/data/jobs/{job_id}
- Static URLs served at /static/jobs/{job_id}/*

## Tests (backend)
- Inside backend container: `pytest -q`

## Ingest (JSON rows)

Example cURL for ingesting Amazon-like rows via JSON:

```bash
curl -s -X POST http://localhost:8000/api/ingest/amazon \
  -H 'Content-Type: application/json' \
  -d '{
        "rows":[
          {"order_id":"113-1111111-1111111","line_item_id":"A1","template_id":"PLAQUE-140x90-V1","line_1":"In loving memory","line_2":"John K Newman","line_3":"1950-2024"},
          {"order_id":"113-1111111-1111111","line_item_id":"A2","template_id":"PLAQUE-140x90-V1","line_1":"In loving memory","line_2":"Jane K Newman","line_3":"1951-2024"}
        ]
      }' | jq .
```

Response shape:

```json
{
  "items": [ { "template_id": "PLAQUE-140x90-V1", "lines": [...], "order_ref": "113-...:A1", "channel": "amazon" }, ... ],
  "warnings": [ { "code": "PHOTO_EXTERNAL_URL", "severity": "info", "message": "Photo URL provided; not downloaded" } ]
}
```

## Smoke: Amazon TXT with downloads

When external downloads are enabled, you can ingest raw Amazon TXT (tab-delimited) and expect parsed lines and background/graphics to populate automatically. Example (replace the TSV body with your file contents, e.g., `124890684926020382.txt`):

```bash
curl -s -X POST http://localhost:8000/api/ingest/amazon \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "amazon-order-id\tsku\tquantity\tcustomized-url\n113-...\tOM008015RegUK\t1\thttps://example.com/personalisation.zip\n"
  }' | jq .
```

Expected: items include `template_id` resolved from SKU, `graphics_key` from options/background, `lines` (line_1..3) from personalization JSON/XML, and `photo_asset_id` if an image exists in the ZIP.

## Determinism

This prototype guarantees deterministic bed composition given identical inputs and seed. To reproduce:

1. Ingest items (see cURL above) or submit items directly to `/api/jobs/generate`.
2. Call `/api/jobs/generate` twice with the same payload and `seed` (e.g., `42`).
3. Compare the bytes of `bed_1.svg` from both responses’ artifact URLs. They must be identical.

Example (using two sequential calls):

```bash
REQ='{"items":[{"template_id":"PLAQUE-140x90-V1","lines":[{"id":"line_1","value":"In loving memory"},{"id":"line_2","value":"John K Newman"},{"id":"line_3","value":"1950-2024"}]}],"machine_id":"MUTOH-UJF-461","seed":42}'

R1=$(curl -s -X POST http://localhost:8000/api/jobs/generate -H 'Content-Type: application/json' -d "$REQ")
R2=$(curl -s -X POST http://localhost:8000/api/jobs/generate -H 'Content-Type: application/json' -d "$REQ")
U1=$(echo $R1 | jq -r '.artifacts[] | select(endswith("bed_1.svg"))')
U2=$(echo $R2 | jq -r '.artifacts[] | select(endswith("bed_1.svg"))')
curl -s http://localhost:8000$U1 -o /tmp/bed1.svg
curl -s http://localhost:8000$U2 -o /tmp/bed2.svg
cmp /tmp/bed1.svg /tmp/bed2.svg && echo "Deterministic: identical" || echo "Mismatch"
```

## Ingest (Amazon TXT via rows JSON)

Example cURL using raw Amazon TXT rows mapped into JSON `rows`:

```bash
curl -s -X POST http://localhost:8000/api/ingest/amazon \
  -H 'Content-Type: application/json' \
  -d '{
    "rows": [
      {
        "amazon-order-id": "113-1111111-1111111",
        "sku": "OD045004-PLAQUE",
        "quantity": "1",
        "customized-url": "https://example.com/personalisation.zip",
        "line_1": "In loving memory",
        "line_2": "John K Newman",
        "line_3": "1950–2024"
      }
    ]
  }' | jq .
```

## Determinism (How to reproduce)

Two identical `/api/jobs/generate` requests with the same payload and `seed` MUST produce byte-identical `bed_1.svg`:

```bash
REQ='{"items":[{"template_id":"PLAQUE-140x90-V1","type":"REGULAR","quantity":1,"lines":[{"id":"line_1","value":"A"},{"id":"line_2","value":"B"},{"id":"line_3","value":"C"}]}],"machine_id":"MUTOH-UJF-461","seed":42}'

curl -s -X POST http://localhost:8000/api/jobs/generate \
  -H 'Content-Type: application/json' -d "$REQ" > /tmp/run1.json

curl -s -X POST http://localhost:8000/api/jobs/generate \
  -H 'Content-Type: application/json' -d "$REQ" > /tmp/run2.json

JID1=$(jq -r .job_id /tmp/run1.json)
JID2=$(jq -r .job_id /tmp/run2.json)

curl -s "http://localhost:8000/static/jobs/$JID1/bed_1.svg" -o /tmp/bed1.svg
curl -s "http://localhost:8000/static/jobs/$JID2/bed_1.svg" -o /tmp/bed2.svg

cmp -s /tmp/bed1.svg /tmp/bed2.svg && echo "Identical!" || echo "Different!"
```

## Environment flags

- **ALLOW_EXTERNAL_DOWNLOADS**: defaults to True. Set to False in CI to avoid network calls.
- **DEFAULT_SEED**: controls layout reproducibility when a seed isn’t provided.
- **Paths via settings**: all paths are configured in `backend/app/settings.py`.

## SKU metadata (SKULIST.csv)

- Location: preferred `backend/app/data/SKULIST.csv`. If missing, the backend falls back to `assets/SKULIST.csv`.
- Columns (header-sensitive, case-insensitive for `SKU` key):
  - `SKU`: the SKU string used to look up metadata (normalized: trim, lower, remove spaces)
  - `COLOUR`: free text colour (mapped to `item.colour`)
  - `TYPE`: product type (mapped to `item.product_type`)
  - `DecorationType`: one of `Photo`, `Graphic`, or `None` (mapped to `item.decoration_type`)
  - `Theme`: optional thematic tag (mapped to `item.theme`)
- The ingestion route `/api/ingest/amazon` loads metadata via `app/utils/sku_map.py` and enriches each `IngestItem` with the above fields.
- Template selection rules:
  - If the CSV row has `template_id`, it is used.
  - Else, a simple type map applies: `Regular Stake → PLAQUE-140x90-V1`, `Large Metal → PLAQUE-LARGE-METAL-V1`.
  - Else, defaults to `PLAQUE-140x90-V1` and emits `UNKNOWN_TEMPLATE`.

## DecorationType → Processor routing

- The field `item.decoration_type` drives processor selection:
  - `Photo` → `photo_basic_v1`
  - `Graphic` → `regular_v1`
  - otherwise → `text_only_v1`
- Helper location: `backend/app/processors/registry.py` → `key_for_item(item) -> str`.
- Integrate by computing `proc_key = registry.key_for_item(item)` wherever processors are invoked and mapping that key to a registered renderer.

## CSV hot-reload (optional)

- On startup, the SKU map loads once.
- Env: `APP_SKU_MAP_RELOAD_SEC` (default `0`). If `> 0`, a background thread re-reads the CSV every N seconds and updates the in-memory map atomically.
- Useful during development while editing `assets/SKULIST.csv` without restarting the server.

## Notes

- **Order ref** now shows only the Amazon order-id in the UI (e.g., `123-1111111-2222222`).
- **SKU enrichment** from `SKULIST.csv` populates the table columns: `colour`, `type` (`product_type`), `decoration`, and `theme`.
- **Photo column** displays the uploaded image derived from `ImageCustomization.image.imageName` where available (fallbacks apply). A thumbnail is shown and the original filename is displayed. Files are cached under `/static/photos` in local mode, or a presigned URL is returned in S3 mode.

## SKU enrichment

- **Location**: place `SKULIST.csv` under `./assets/` (mounted read-only to `/app/assets` in Docker).
- **Columns**: `SKU`, `COLOUR`, `TYPE`, `DecorationType`, `Theme`.
- **Matching**: case-insensitive. The loader tries both the exact-lowercased SKU and a variant with all spaces removed to improve robustness.
