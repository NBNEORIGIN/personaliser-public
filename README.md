# Personaliser

Batch personalisation tool (Amazon TXT ingest → QA → deterministic SVG/CSV plate generation).

- Frontend: Next.js (Docker)
- Backend: FastAPI (Docker)
- Processors: Regular Stake v1 (SVG + CSV)
- Assets: place graphics in `/assets/graphics`, `SKULIST.csv` in `/assets/`

## Run (local)

```sh
docker compose up --build
```

## Env

- Frontend: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`)
- Backend: `FRONTEND_ORIGIN` (default `http://localhost:3000`)

## Deploy

- Frontend → Vercel (root=`frontend`)
- Backend → Docker host/Render/Railway
