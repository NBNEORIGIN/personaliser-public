from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .settings import settings
from .routers import catalog, ingest_amazon, jobs, assets
from .utils import sku_map
import shutil

app = FastAPI(title="Bed Optimised Batch Production API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(catalog.router, prefix=settings.API_PREFIX)
app.include_router(ingest_amazon.router, prefix=settings.API_PREFIX)
app.include_router(jobs.router, prefix=settings.API_PREFIX)
app.include_router(assets.router, prefix=settings.API_PREFIX)

# Static mounts for previews and jobs artifacts
app.mount("/static/previews", StaticFiles(directory=settings.PREVIEWS_DIR), name="previews")
app.mount("/static/jobs", StaticFiles(directory=settings.JOBS_DIR), name="jobs")
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")
app.mount("/static/storage", StaticFiles(directory=settings.DATA_DIR / "storage"), name="storage")
app.mount("/static/photos", StaticFiles(directory=settings.PHOTOS_DIR), name="photos")

# Ensure temp/download directory exists at startup
settings.DOWNLOAD_TMP_DIR.mkdir(parents=True, exist_ok=True)

# Optionally clear photos cache on start
try:
    if settings.CLEAN_PHOTOS_ON_START and settings.PHOTOS_DIR.exists():
        for p in settings.PHOTOS_DIR.iterdir():
            if p.is_file():
                p.unlink(missing_ok=True)
            elif p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
except Exception:
    pass

# Initialize SKU map (load once; start hot-reload if configured)
try:
    sku_map.init()
except Exception:
    pass
