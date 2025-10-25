from fastapi import APIRouter, HTTPException, Body, Depends, Request, UploadFile, File
from typing import List, Optional, Dict, Any, Tuple
import io
import json
from pathlib import Path
from ..models import IngestItem, LineField, QaWarning, Severity
from ..utils.qa import merge_qa, run_qa
from ..utils.tsv import parse_tsv
from ..utils.zip_ingest import download_zip, safe_extract, parse_personalisation, ZipTooLargeError, ZipHttpError
from ..settings import settings
from ..auth import get_current_user
from ..utils.storage import get_storage, put_photo_local, upload_photo_and_presign, save_photo_local
from ..utils.sku_map import get_meta_for_sku
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest/amazon")
async def ingest_amazon(
    request: Request,
    file: Optional[UploadFile] = File(None),
    payload: Optional[Dict[str, Any]] = Body(None),
    user=Depends(get_current_user),
):
    items: List[IngestItem] = []
    warnings: List[QaWarning] = []
    rows: List[Dict[str, Any]] = []

    def _lower_keys(d: Dict[str, Any]) -> Dict[str, Any]:
        return {str(k).lower(): v for k, v in d.items()}

    def _get(d: Dict[str, Any], keys: List[str]) -> Any:
        dl = _lower_keys(d)
        for k in keys:
            if k.lower() in dl:
                return dl[k.lower()]
        return None

    # Load rows: from file upload, else explicit payload, else parse request.json
    if file is not None:
        raw = await file.read()
        text = raw.decode("utf-8", errors="ignore")
        headers, data_rows = parse_tsv(text)
        rows = [dict(zip(headers, r)) for r in data_rows]
    elif payload is not None and isinstance(payload, dict):
        if "text" in payload and isinstance(payload["text"], str):
            headers, data_rows = parse_tsv(payload["text"]) 
            rows = [dict(zip(headers, r)) for r in data_rows]
        elif "rows" in payload:
            rows = list(payload.get("rows") or [])
        else:
            raise HTTPException(status_code=400, detail="Provide multipart file, JSON {text:""}, or JSON {rows:[...]} payload")
    else:
        # Try to parse JSON body directly when no payload bound (e.g., application/json without file)
        try:
            body = await request.json()
            if isinstance(body, dict):
                if "text" in body and isinstance(body["text"], str):
                    headers, data_rows = parse_tsv(body["text"]) 
                    rows = [dict(zip(headers, r)) for r in data_rows]
                elif "rows" in body:
                    rows = list(body.get("rows") or [])
                else:
                    raise HTTPException(status_code=400, detail="Provide multipart file, JSON {text:""}, or JSON {rows:[...]} payload")
            else:
                raise HTTPException(status_code=400, detail="Provide multipart file, JSON {text:""}, or JSON {rows:[...]} payload")
        except Exception:
            raise HTTPException(status_code=400, detail="Provide multipart file, JSON {text:""}, or JSON {rows:[...]} payload")

    # catalog maxlens helper
    catalog_path = settings.DATA_DIR / "catalog.json"
    tmpl_maxlens: Dict[str, Dict[str, int]] = {}
    if catalog_path.exists():
        try:
            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            for t in data.get("templates", []):
                lens: Dict[str, int] = {}
                for f in t.get("options", {}).get("fields", []):
                    if f.get("type") == "text":
                        lens[f["id"]] = int(f.get("maxLen", 10**9))
                tmpl_maxlens[t.get("id")] = lens
        except Exception:
            pass

    def _infer_template_id(sku: str) -> Tuple[Optional[str], bool, str | None, List[QaWarning], Dict[str, Any]]:
        w: List[QaWarning] = []
        meta = get_meta_for_sku(sku)
        tmpl = meta.get("template_id")
        req_photo = bool(meta.get("requires_photo", False))
        default_type = meta.get("default_type")
        if tmpl:
            return tmpl, req_photo, default_type, w, meta
        # TYPE-based simple rule map if no template_id set
        type_val = (meta.get("TYPE") or "").strip().lower()
        type_map = {
            "regular stake": "PLAQUE-140x90-V1",
            "large metal": "PLAQUE-LARGE-METAL-V1",
        }
        if type_val in type_map:
            return type_map[type_val], req_photo, default_type, w, meta
        # leave template_id unset; warn
        w.append(QaWarning(code="UNKNOWN_TEMPLATE", message="Unable to infer template from sku", severity=Severity.warn))
        return None, req_photo, default_type, w, meta

    downloads_root = settings.DATA_DIR / "storage" / "downloads"
    storage = get_storage()

    for idx, r in enumerate(rows):
        order_id = str(_get(r, ["amazon-order-id", "order-id", "order_id"]) or "")
        sku = str(_get(r, ["sku"]) or "")
        qty = int((_get(r, ["quantity"]) or 1) or 1)
        cust_url = _get(r, ["customized-url", "customized url", "customized_url"]) or None
        # customized-page not used directly for now
        # Display-only reference: Amazon order-id only
        order_ref = order_id
        # Internal unique key for this row (not exposed in API response)
        internal_id = f"{order_id}:{idx}"
        logger.info("[ingest] row=%s order_id=%s sku=%s url=%r", idx, order_id, sku, cust_url)

        template_id, requires_photo, default_type, w_tmpl, sku_meta = _infer_template_id(sku)
        warnings.extend(w_tmpl)
        # If caller provided template_id explicitly in the row payload, honor it
        explicit_tmpl = _get(r, ["template_id"]) or None
        if explicit_tmpl:
            template_id = str(explicit_tmpl)
        if not template_id:
            template_id = "PLAQUE-140x90-V1"

        fields = {
            "line_1": str(_get(r, ["line_1"]) or ""),
            "line_2": str(_get(r, ["line_2"]) or ""),
            "line_3": str(_get(r, ["line_3"]) or ""),
        }
        images: List[Path] = []
        asset_keys: List[str] = []

        if cust_url:
            if settings.ALLOW_EXTERNAL_DOWNLOADS:
                try:
                    tmp_zip = settings.DOWNLOAD_TMP_DIR / "ingest" / order_id / f"{idx}.zip"
                    logger.info("ingest.download.start", extra={"order_id": order_id, "idx": idx, "url": str(cust_url)})
                    download_zip(str(cust_url), tmp_zip, timeout=settings.DOWNLOAD_TIMEOUT_S, user_agent=settings.USER_AGENT)
                    dest_dir = downloads_root / order_id / str(idx)
                    extracted = safe_extract(tmp_zip, dest_dir, max_mb=settings.MAX_ZIP_MB)
                    logger.info("ingest.download.done", extra={"order_id": order_id, "idx": idx, "files": len(extracted)})
                    # Upload extracted files to storage if S3 mode; in local mode, derive keys
                    for pth in extracted:
                        if settings.STORAGE_BACKEND.lower() == "s3":
                            key = f"downloads/{order_id}/{idx}/{pth.name}"
                            try:
                                ctype = _guess_content_type(pth.suffix)
                                storage.put_bytes(key, pth.read_bytes(), content_type=ctype)
                                asset_keys.append(key)
                            except Exception as e:
                                warnings.append(QaWarning(code="ZIP_UPLOAD_FAILED", message=str(e), severity=Severity.error))
                        else:
                            # local mode: key is relative to DATA_DIR
                            rel = pth.relative_to(settings.DATA_DIR)
                            asset_keys.append(str(rel))
                    pdata = parse_personalisation(extracted)
                    # Populate fields from parser
                    if pdata.get("line_1"):
                        fields["line_1"] = pdata["line_1"]
                    if pdata.get("line_2"):
                        fields["line_2"] = pdata["line_2"]
                    if pdata.get("line_3"):
                        fields["line_3"] = pdata["line_3"]
                    if pdata.get("graphics_key"):
                        fields["graphic"] = pdata["graphics_key"]
                    # photo mapping is set after this block
                    # structured summary log
                    summary = {
                        "graphics_key": fields.get("graphic"),
                        "line_1": (fields.get("line_1") or "")[:10],
                        "line_2": (fields.get("line_2") or "")[:10],
                        "line_3": (fields.get("line_3") or "")[:10],
                    }
                    logger.info("ingest.parse.summary", extra={"order_id": order_id, "idx": idx, **summary})
                except ZipTooLargeError as ze:
                    warnings.append(QaWarning(code="ZIP_TOO_LARGE", message=str(ze), severity=Severity.error, field="customized-url"))
                except ZipHttpError as he:
                    warnings.append(QaWarning(code="ZIP_DOWNLOAD_FAILED", message=f"HTTP {he.status}", severity=Severity.error, field="customized-url"))
                except Exception as e:
                    logger.exception("ingest.zip.error row=%s", idx)
                    warnings.append(QaWarning(code="ZIP_PROCESSING_ERROR", message=str(e)[:200], severity=Severity.error, field="customized-url"))
            else:
                warnings.append(QaWarning(code="DOWNLOADS_DISABLED", message="External downloads disabled by env; cannot fetch customized-url", severity=Severity.info, field="customized-url"))
        else:
            warnings.append(QaWarning(code="MISSING_CUSTOMIZED_URL", message="Row missing customized-url", severity=Severity.warn))

        # Choose photo from parsed data and persist
        photo_asset = None
        photo_filename: Optional[str] = None
        photo_via: str = "-"
        try:
            p_path = pdata.get("photo_path") if isinstance(pdata, dict) else None
            p_name = pdata.get("photo_filename") if isinstance(pdata, dict) else None
            photo_via = pdata.get("photo_via") or "-"
            if isinstance(p_path, Path) and p_path.exists():
                stored = f"{order_id}-{idx}-{(p_name or p_path.name)}"
                print(f"[INGEST] Saving photo: {p_path} -> {stored}", flush=True)
                if settings.STORAGE_BACKEND.lower() == "s3":
                    photo_asset = upload_photo_and_presign(p_path, stored)
                else:
                    photo_asset = save_photo_local(p_path, stored)
                print(f"[INGEST] Photo saved, URL: {photo_asset}", flush=True)
                photo_filename = p_name or p_path.name
        except Exception as e:
            print(f"[INGEST] Failed to save photo: {e}", flush=True)
            photo_asset = None

        # If nothing parsed, add explicit warning
        if not fields.get("graphic") and not any(fields.get(k) for k in ("line_1","line_2","line_3")) and not photo_asset:
            warnings.append(QaWarning(code="NO_PERSONALISATION_FOUND", message="ZIP had no usable JSON/XML/text", severity=Severity.warn, field="customized-url"))

        # QA wiring from decoration_type
        deco = (sku_meta.get("DecorationType") or "").strip().lower()
        require_photo_flag = (deco == "photo")
        if (deco == "graphic") and not (fields.get("graphic")):
            warnings.append(QaWarning(code="GRAPHIC_MISSING", message="DecorationType=Graphic but no graphics_key parsed", severity=Severity.warn))

        item = IngestItem(
            order_ref=order_ref,
            template_id=template_id,
            sku=sku or None,
            quantity=qty,
            lines=[
                LineField(id="line_1", value=fields.get("line_1", "")),
                LineField(id="line_2", value=fields.get("line_2", "")),
                LineField(id="line_3", value=fields.get("line_3", "")),
            ],
            graphics_key=(fields.get("graphic") or None),
            photo_asset_id=photo_asset,
            photo_asset_url=photo_asset,
            photo_filename=photo_filename,
            assets=asset_keys,
            colour=sku_meta.get("COLOUR"),
            product_type=sku_meta.get("TYPE"),
            decoration_type=sku_meta.get("DecorationType"),
            theme=sku_meta.get("Theme"),
            processor=sku_meta.get("Processor"),
        )
        items.append(item)

        # QA per item using catalog lens
        maxlens = tmpl_maxlens.get(template_id)
        if maxlens:
            qa = run_qa(
                {l.id: l.value for l in item.lines},
                template_maxlens=maxlens,
                require_photo=bool((item.decoration_type or "").lower() == "photo"),
                has_photo=bool(item.photo_asset_url),
                current_year=2025,
            )
            warnings.extend(qa)

        # concise per-row summary including photo status
        try:
            logger.info(
                "[ingest] row=%s sku=%s graphic=%r l1=%s l2=%s l3=%s photo=%s via=%s",
                idx,
                sku,
                item.graphics_key or '-',
                (fields.get("line_1") or "")[:10],
                (fields.get("line_2") or "")[:10],
                (fields.get("line_3") or "")[:10],
                (item.photo_filename or '-'),
                photo_via,
            )
        except Exception:
            pass

    # merge_qa kept for parity; here we have single source
    merged = merge_qa(warnings, [])
    return {"items": [i.model_dump() for i in items], "warnings": [w.model_dump() for w in merged]}


def _guess_content_type(ext: str) -> str:
    ext = ext.lower()
    return {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".json": "application/json",
        ".xml": "application/xml",
    }.get(ext, "application/octet-stream")
