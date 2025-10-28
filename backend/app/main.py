from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .settings import settings
from .routers import catalog, ingest_amazon, jobs, assets, layout_engine
from .utils import sku_map
import shutil

# Cache bust: 2025-10-27-16:50 - Redeploy with upgraded tier (2GB RAM)
app = FastAPI(title="Bed Optimised Batch Production API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.nbne.uk",
        "https://personaliser.vercel.app",
        "http://localhost:3000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Routers
app.include_router(catalog.router, prefix=settings.API_PREFIX)
app.include_router(ingest_amazon.router, prefix=settings.API_PREFIX)
app.include_router(jobs.router, prefix=settings.API_PREFIX)
app.include_router(assets.router, prefix=settings.API_PREFIX)
app.include_router(layout_engine.router)  # Layout engine (has its own prefix)

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

# Root redirect
@app.get("/")
async def root():
    """Redirect root to demo page"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/demo")

# Health and status endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "personaliser-api"}

@app.get("/status")
async def status():
    """Status endpoint with version info"""
    return {
        "status": "operational",
        "service": "personaliser-api",
        "version": "1.0.3",  # Layout engine enabled
        "storage": settings.STORAGE_BACKEND,
        "timestamp": "2025-10-28T10:00:00Z"
    }

@app.get("/demo")
async def demo():
    """Serve demo HTML page"""
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    # Use absolute path resolution
    demo_path = Path(__file__).parent.parent / "demo.html"
    
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail=f"Demo file not found at {demo_path}")
    
    return FileResponse(
        str(demo_path),
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/demo/debug")
async def demo_debug():
    """Debug endpoint to check demo.html content"""
    from pathlib import Path
    demo_path = Path(__file__).parent.parent / "demo.html"
    
    if demo_path.exists():
        content = demo_path.read_text(encoding='utf-8')
        has_quick_templates = "Quick Templates" in content
        has_loadtemplate = "loadTemplate" in content
        title_match = content[content.find("<title>"):content.find("</title>")+8] if "<title>" in content else "Not found"
        
        return {
            "path": str(demo_path),
            "exists": True,
            "size": len(content),
            "has_quick_templates": has_quick_templates,
            "has_loadTemplate_function": has_loadtemplate,
            "title": title_match,
            "first_500_chars": content[:500]
        }
    else:
        return {"path": str(demo_path), "exists": False}
