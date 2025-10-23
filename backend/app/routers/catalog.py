from fastapi import APIRouter
from pathlib import Path
import json
from ..settings import settings

router = APIRouter()

@router.get("/catalog")
def get_catalog():
    cat_path = settings.DATA_DIR / "catalog.json"
    machines = json.loads((settings.DATA_DIR / "machines" / "MUTOH-UJF-461.json").read_text("utf-8"))
    materials = json.loads((settings.DATA_DIR / "materials" / "ALU-ACM-1MM.json").read_text("utf-8"))
    catalog = json.loads(cat_path.read_text("utf-8"))
    return {
        "templates": catalog.get("templates", []),
        "machines": [machines],
        "materials": [materials],
    }
