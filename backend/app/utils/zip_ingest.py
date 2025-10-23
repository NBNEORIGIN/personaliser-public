from __future__ import annotations
from typing import List, Tuple, Dict, Any
from pathlib import Path
import time
import zipfile
import json
import xml.etree.ElementTree as ET
import requests
import re
import logging
from ..settings import settings

ALLOWED_EXTS = {".json", ".xml", ".svg", ".png", ".jpg", ".jpeg", ".gif"}

class ZipHttpError(Exception):
    def __init__(self, status: int, url: str):
        super().__init__(f"HTTP {status} for {url}")
        self.status = status
        self.url = url


class ZipTooLargeError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


def download_zip(url: str, dest_path: Path, *, timeout: int, user_agent: str, retries: int = 3, max_mb: int | None = None) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            headers = {"User-Agent": user_agent}
            with requests.get(url, headers=headers, allow_redirects=True, stream=True, timeout=(10, timeout)) as r:
                if r.status_code != 200:
                    raise ZipHttpError(r.status_code, url)
                limit = (max_mb or 10**9) * 1024 * 1024
                written = 0
                with dest_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        written += len(chunk)
                        if written > limit:
                            raise ZipTooLargeError(f"Download exceeded {max_mb} MB")
                        f.write(chunk)
            return dest_path
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)
    if last_err:
        raise last_err
    return dest_path


def _is_within(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def safe_extract(zip_path: Path, dest_dir: Path, *, max_mb: int) -> List[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    max_bytes = max_mb * 1024 * 1024
    total_bytes = 0
    out_files: List[Path] = []

    with zipfile.ZipFile(zip_path) as zf:
        # Pre-validate size
        for info in zf.infolist():
            total_bytes += info.file_size
            if total_bytes > max_bytes:
                raise ZipTooLargeError(f"ZIP exceeds {max_mb} MB limit")
        # Extract allowed files safely
        for info in zf.infolist():
            if info.is_dir():
                continue
            ext = Path(info.filename).suffix.lower()
            if ext not in ALLOWED_EXTS:
                continue
            target = dest_dir / info.filename
            if not _is_within(target, dest_dir):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as dst:
                dst.write(src.read())
            out_files.append(target)

    return out_files


def parse_personalisation(files: List[Path]) -> Dict[str, Any]:
    """
    Returns dict: { line_1, line_2, line_3, graphics_key, photo }
    Missing entries set to None. Prefers JSON then XML.
    """
    def _norm_keys(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {str(k).lower(): _norm_keys(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_norm_keys(x) for x in obj]
        return obj

    def _short(s: str | None) -> str:
        return (s or "")[:10]

    _TEXT_INPUT_RE = re.compile(r"^text\s*input\s*\d+\s*$", re.I)
    _CONTAINER_NOISE = {"face","front","back","surface","surface 1","surface 2","default","none"}
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip()).lower() if isinstance(s, str) else ""

    def _load_graphic_catalog_names() -> set[str]:
        names: set[str] = set()
        try:
            base = settings.DATA_DIR / "assets" / "graphics"
            if base.exists():
                for p in base.rglob("*"):
                    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".svg"}:
                        names.add(_norm(p.stem))
        except Exception:
            return set()
        return names

    # Collect images list; photo may be overridden by ImageCustomization below
    images = [p for p in files if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    photo_path: Path | None = images[0] if images else None
    photo_image_name: str | None = None
    photo_buyer_name: str | None = None
    photo_via: str = "-"

    lines: List[str] = []
    graphics: str | None = None
    KEYWORDS = ["graphic", "background", "design", "surface", "face", "border", "frame", "vine", "rose", "cat", "dog"]
    candidates: List[Tuple[str, str]] = []  # (path_hint, value)
    selected_by_surfaces: List[str] = []

    # JSON first
    for p in files:
        if p.suffix.lower() == ".json":
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                data = _norm_keys(raw)
                # direct keys
                for k in ("line_1", "line_2", "line_3"):
                    v = data.get(k)
                    if isinstance(v, str):
                        lines.append(v)
                if isinstance(data.get("graphic"), str) and not graphics:
                    graphics = data.get("graphic")

                # walk customizationData trees
                def walk(node: Any, ancestors: List[str] | None = None):
                    nonlocal graphics, lines, candidates, photo_path
                    ancestors = ancestors or []
                    if isinstance(node, dict):
                        t = node.get("__typename") or node.get("type")
                        if isinstance(t, str) and t.lower().startswith("textcustomization"):
                            iv = node.get("inputvalue")
                            if isinstance(iv, str):
                                lines.append(iv)
                        # ImageCustomization: prefer explicit imageName
                        if isinstance(t, str) and t.lower() == "imagecustomization":
                            img = node.get("image") or {}
                            if isinstance(img, dict):
                                name = img.get("imagename") or img.get("imageName")
                                buyer = img.get("buyerfilename") or img.get("buyerFilename")
                                # Prefer primary imageName (real photo)
                                if isinstance(name, str) and name.strip():
                                    for cand in images:
                                        if cand.name.lower() == name.strip().lower():
                                            photo_path = cand
                                            photo_image_name = name.strip()
                                            photo_via = "imageName"
                                            break
                                # Fallback to buyerFilename if primary not matched
                                if (photo_via == "-" or photo_path is None) and isinstance(buyer, str) and buyer.strip():
                                    for cand in images:
                                        if cand.name.lower() == buyer.strip().lower():
                                            photo_path = cand
                                            photo_buyer_name = buyer.strip()
                                            photo_via = "buyerFilename"
                                            break
                        # Explicitly ignore preview snapshots and SVG overlay images
                        snap = node.get("snapshot") if isinstance(node.get("snapshot"), dict) else None
                        if isinstance(snap, dict):
                            # ignore snapshot.imageName entirely
                            pass
                        # explicit support for Option/Select customizations: collect candidates
                        if isinstance(t, str) and t in ("OptionCustomization", "SelectCustomization"):
                            sel = node.get("optionSelection") or {}
                            val = None
                            if isinstance(sel, dict):
                                val = sel.get("name") or sel.get("label")
                            if not isinstance(val, str) or not val.strip():
                                dv = node.get("displayValue")
                                if isinstance(dv, str) and dv.strip():
                                    val = dv
                            if isinstance(val, str) and val.strip():
                                name_or_label = (node.get("name") or node.get("label") or "")
                                hint = " > ".join([*ancestors, str(name_or_label)])
                                candidates.append((hint, val.strip()))
                        # other select-like nodes: still collect optionvalue/value/name as weak candidates
                        for key in ("optionvalue", "value", "name", "graphic"):
                            val = node.get(key)
                            if isinstance(val, str) and val.strip():
                                hint = " > ".join([*ancestors, str(node.get("name") or node.get("label") or t or "")])
                                candidates.append((hint, val.strip()))
                        # recurse
                        for child_key in ("children", "items", "nodes", "options"):
                            child = node.get(child_key)
                            if isinstance(child, list):
                                for el in child:
                                    walk(el, ancestors + [str(node.get("name") or node.get("label") or t or "")])
                            elif isinstance(child, dict):
                                walk(child, ancestors + [str(node.get("name") or node.get("label") or t or "")])
                    elif isinstance(node, list):
                        for el in node:
                            walk(el, ancestors)

                for k in ("customizationdata", "customization_data"):
                    if k in data:
                        walk(data[k])

                # PRIMARY: customizationInfo.version3.0.surfaces[].areas[]
                ci = data.get("customizationinfo") or {}
                v3 = isinstance(ci, dict) and (ci.get("version3.0") or ci.get("version3_0") or ci.get("v3"))
                if isinstance(v3, dict):
                    surfaces = v3.get("surfaces")
                    if isinstance(surfaces, list):
                        done = False
                        for s in surfaces:
                            areas = isinstance(s, dict) and s.get("areas")
                            if isinstance(areas, list):
                                for a in areas:
                                    if not isinstance(a, dict):
                                        continue
                                    ctype = _norm(a.get("customizationtype") or "")
                                    nm = (a.get("name") or a.get("label") or "")
                                    nm_l = _norm(nm)
                                    val = a.get("optionvalue") or a.get("optionValue")
                                    if (ctype == "options" and "graphic" in nm_l and isinstance(val, str) and val.strip()):
                                        graphics = val.strip()
                                        done = True
                                        break
                                    # also collect surface values for ranking reference
                                    if isinstance(val, str) and val.strip():
                                        selected_by_surfaces.append(val.strip())
                            if done:
                                break

                if lines or candidates or selected_by_surfaces or photo:
                    break
            except Exception:
                continue

    # XML fallback
    if not (lines or graphics):
        for p in files:
            if p.suffix.lower() == ".xml":
                try:
                    root = ET.fromstring(p.read_text(encoding="utf-8"))
                    # find text-like nodes
                    texts: List[str] = []
                    for el in root.iter():
                        tag = el.tag.lower() if isinstance(el.tag, str) else ""
                        if "text" in tag and el.text and el.text.strip():
                            texts.append(el.text.strip())
                        if ("graphic" in tag or "option" in tag) and (el.text and el.text.strip()):
                            if not graphics:
                                graphics = el.text.strip()
                    lines.extend(texts)
                    if lines or graphics:
                        break
                except Exception:
                    continue

    # If surfaces logic selected, keep it; otherwise FALLBACK to Option/Select candidates in encounter order
    if not graphics:
        noise = _CONTAINER_NOISE | {"text", "line 1", "line 2", "line 3"}
        chosen: str | None = None
        for hint, v in candidates:
            # derive node label from hint's last segment
            label = _norm(hint.split(" > ")[-1]) if hint else ""
            if _TEXT_INPUT_RE.match(label):
                continue
            if _norm(v) in noise:
                continue
            if isinstance(v, str) and v.strip():
                chosen = v.strip()
                break
        graphics = chosen

    # Final photo fallback to first extracted image if none matched by name
    if photo_path is None and images:
        photo_path = images[0]
        photo_via = "fallback"

    out = {
        "line_1": lines[0] if len(lines) > 0 else None,
        "line_2": lines[1] if len(lines) > 1 else None,
        "line_3": lines[2] if len(lines) > 2 else None,
        "graphics_key": graphics,
        # New explicit photo fields
        "photo_path": photo_path,
        "photo_filename": (photo_image_name or photo_buyer_name),
        "photo_via": photo_via,
        # Backward compatibility
        "photo": {
            "path": str(photo_path) if photo_path else None,
            "imageName": photo_image_name,
            "buyerFilename": photo_buyer_name,
        },
    }

    # Concise summary log
    try:
        logger = logging.getLogger("ingest")
        logger.info(
            "[ingest] parsed graphics candidates=%s surfaces=%s text=(%s,%s,%s) photo=%s via=%s",
            len(candidates), len(selected_by_surfaces),
            _short(out["line_1"]), _short(out["line_2"]), _short(out["line_3"]),
            (photo_image_name or photo_buyer_name or (photo_path.name if photo_path else '-') or '-'),
            photo_via,
        )
    except Exception:
        pass
    return out


# Backward-compatibility helper (if needed elsewhere)
def parse_personalisation_legacy(files: List[Path]) -> Tuple[Dict[str, str], List[Path]]:
    d = parse_personalisation(files)
    fields: Dict[str, str] = {}
    if d.get("line_1"): fields["line_1"] = d["line_1"]
    if d.get("line_2"): fields["line_2"] = d["line_2"]
    if d.get("line_3"): fields["line_3"] = d["line_3"]
    if d.get("graphics_key"): fields["graphic"] = d["graphics_key"]
    images = [p for p in files if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}]
    return fields, images
