from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi import Body
from typing import List
from uuid import uuid4
from pathlib import Path
from ..settings import settings
from ..models import OrderItem, GenerateRequest, PreviewResponse, GenerateResponse, QaWarning, Severity
from ..utils.qa import qa_item, merge_qa
from ..processors import uv_regular_v1  # ensure registration
from ..processors import text_only_v1  # batch stub registration
from ..processors import photo_basic_v1  # batch stub registration
from ..processors import regular_stake_v1  # regular stake batch registration
# from ..processors import photo_stakes_v1  # DISABLED - using PDF version
from ..processors import photo_stakes_pdf_v1  # photo stakes PDF processor (new)
from ..processors.item_router import get as get_processor
from ..processors.item_router import get_batch as get_batch_processor
from ..processors.item_router import key_for_item
from ..utils.svg_compose import compose_bed_svg, save_svg_and_png, svg_to_png_bytes, BED_W, BED_H
from ..packer.rect_packer import pack_first_fit, pack_paginated, Rect
import csv
from ..auth import get_current_user
from ..utils.storage import get_storage

router = APIRouter()

# simple in-memory catalog (in real app, load from data)
TEMPLATE_MAP = {
    "PLAQUE-140x90-V1": {
        "processor": {"name": "uv_regular", "version": "1.0.0"},
        "w": 140.0,
        "h": 90.0,
        "maxLen": 30,
        "requiresPhoto": False,
    }
}

MACHINES = {
    "MUTOH-UJF-461": {
        "bed_w": 480.0,
        "bed_h": 330.0,
        "margin": 5.0,
        "gutter": 5.0,
        "keepouts": [(0.0, 0.0, 20.0, 330.0)],
    }
}

@router.post("/jobs/preview", response_model=PreviewResponse)
def preview_item(item: OrderItem = Body(...)):
    job_id = uuid4().hex[:8]
    # QA
    template = TEMPLATE_MAP.get(item.template_id)
    if not template:
        raise HTTPException(status_code=400, detail="Unknown template_id")
    warnings = qa_item(item, template)
    # Render
    proc = get_processor(template["processor"]["name"], template["processor"]["version"])
    svg = proc(item)
    # Save preview
    out_dir = settings.PREVIEWS_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = out_dir / "preview.svg"
    png_path = out_dir / "preview.png"
    save_svg_and_png(svg, svg_path, png_path)
    return PreviewResponse(job_id=job_id, preview_url=f"/static/previews/{job_id}/preview.png", warnings=warnings)

@router.post("/jobs/generate", response_model=GenerateResponse)
def generate_job(req: GenerateRequest, user=Depends(get_current_user)):
    job_id = uuid4().hex[:8]
    template = TEMPLATE_MAP["PLAQUE-140x90-V1"]
    # QA all
    all_warnings: List[QaWarning] = []
    for it in req.items:
        w = qa_item(it, template)
        all_warnings.extend(w)
    if any(w.severity == Severity.error for w in all_warnings):
        raise HTTPException(status_code=422, detail={"warnings": [w.model_dump() for w in all_warnings]})

    # Group items by processor key
    groups: dict[str, List[OrderItem]] = {}
    for it in req.items:
        k = key_for_item(it)
        # Debug logging
        print(f"[ROUTING] Item {it.order_ref}: decoration_type={getattr(it, 'decoration_type', None)}, product_type={getattr(it, 'product_type', None)}, colour={getattr(it, 'colour', None)} -> processor={k}")
        groups.setdefault(k, []).append(it)

    # If all items are text_only_v1 AND all of (decoration_type, graphics_key, product_type) are empty/None for all,
    # use the legacy per-item renderer and bed packer (old happy-path). Otherwise, use batch processors.
    def _is_plain_text_only(x):
        dec = (getattr(x, "decoration_type", None) or "").strip()
        gfx = (getattr(x, "graphics_key", None) or getattr(x, "graphic", None) or "").strip()
        ptyp = (getattr(x, "product_type", None) or "").strip()
        return dec == "" and gfx == "" and ptyp == ""

    if set(groups.keys()) == {"text_only_v1"} and all(_is_plain_text_only(it) for it in req.items):
        proc = get_processor(template["processor"]["name"], template["processor"]["version"])
        rects: List[Rect] = []
        item_svgs: List[str] = []
        for idx, it in enumerate(req.items):
            svg = proc(it)
            item_svgs.append(svg)
            rects.append(Rect(id=str(idx), w=template["w"], h=template["h"]))

        m = MACHINES.get(req.machine_id)
        if not m:
            raise HTTPException(status_code=400, detail="Unknown machine_id")

        beds = pack_paginated(
            rects,
            bed_w=m["bed_w"],
            bed_h=m["bed_h"],
            margin=m["margin"],
            gutter=m["gutter"],
            keepouts=m["keepouts"],
            seed=req.seed or settings.DEFAULT_SEED,
        )

        storage = get_storage()

        def _url_for(key: str) -> str:
            if settings.STORAGE_BACKEND.lower() == "s3":
                return storage.presign_get(key, settings.PRESIGN_EXPIRES_S)
            return f"/static/{key}"

        # Per-item SVGs
        for idx in range(len(item_svgs)):
            key = f"jobs/{job_id}/i{idx}.svg"
            storage.put_bytes(key, item_svgs[idx].encode("utf-8"), content_type="image/svg+xml")

        # Bed SVG/PNG
        artifacts_beds: List[str] = []
        for bi, bed in enumerate(beds, start=1):
            placed_tuples = [(p.x, p.y, p.w, p.h, p.id) for p in bed]
            bed_svg = compose_bed_svg(placed_tuples, m["keepouts"]) 
            # Inject minimal text overlays (line_1) for visibility in tests; centered in each rect.
            try:
                overlays = []
                for p in bed:
                    idx_i = int(p.id)
                    it = req.items[idx_i]
                    line_map = {l.id: l.value for l in it.lines}
                    l1 = line_map.get("line_1", "")
                    if l1:
                        cx = p.x + p.w / 2.0
                        cy = p.y + p.h / 2.0
                        overlays.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="5mm">{l1}</text>')
                if overlays:
                    bed_svg = bed_svg.replace("</svg>", "".join(overlays) + "</svg>")
            except Exception:
                pass
            svg_key = f"jobs/{job_id}/bed_{bi}.svg"
            png_key = f"jobs/{job_id}/bed_{bi}.png"
            storage.put_bytes(svg_key, bed_svg.encode("utf-8"), content_type="image/svg+xml")
            png_bytes = svg_to_png_bytes(bed_svg)
            storage.put_bytes(png_key, png_bytes, content_type="image/png")
            artifacts_beds.extend([_url_for(png_key), _url_for(svg_key)])

        # Batch CSV for placements
        import io as _io
        csv_buf = _io.StringIO()
        writer = csv.writer(csv_buf)
        writer.writerow(["job_id","bed_index","position_index","item_global_index","item_id","order_ref","template_id","x_mm","y_mm","w_mm","h_mm","line_1","line_2","line_3"])
        for bi, bed in enumerate(beds, start=1):
            for pi, p in enumerate(bed):
                idx = int(p.id)
                it = req.items[idx]
                line_map = {l.id: l.value for l in it.lines}
                writer.writerow([
                    job_id, bi, pi, idx, it.item_id, (it.order_ref or ""), it.template_id,
                    f"{p.x}", f"{p.y}", f"{p.w}", f"{p.h}",
                    line_map.get("line_1",""), line_map.get("line_2",""), line_map.get("line_3",""),
                ])
        csv_key = f"jobs/{job_id}/batch.csv"
        storage.put_bytes(csv_key, csv_buf.getvalue().encode("utf-8"), content_type="text/csv")

        artifacts = [*artifacts_beds, _url_for(csv_key)]
        for idx in range(len(item_svgs)):
            artifacts.append(_url_for(f"jobs/{job_id}/i{idx}.svg"))
        return GenerateResponse(job_id=job_id, artifacts=artifacts, warnings=all_warnings)

    # Otherwise, dispatch each group to batch processors
    artifacts: List[str] = []
    out_dir = settings.JOBS_DIR / job_id
    cfg = {"job_id": job_id, "output_dir": out_dir, "seed": req.seed or settings.DEFAULT_SEED}
    print(f"[BATCH] Processing {len(groups)} processor groups: {list(groups.keys())}")
    for k, items in groups.items():
        print(f"[BATCH] Processor '{k}' handling {len(items)} items")
        try:
            proc = get_batch_processor(k)
        except KeyError:
            print(f"[BATCH] ERROR: Processor '{k}' not found in registry")
            # Unknown processor: skip
            continue
        svg_url, csv_url, warns = proc(items, cfg)
        artifacts.extend([svg_url, csv_url])
    return GenerateResponse(job_id=job_id, artifacts=artifacts, warnings=all_warnings)
