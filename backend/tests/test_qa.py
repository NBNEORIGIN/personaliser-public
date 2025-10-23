import json
import re
from pathlib import Path
import pytest

# Import the qa helper and pydantic model
from app.utils.qa import run_qa, PHOTO_MISSING, OVER_MAXLEN
from app.models import QaWarning

CATALOG_PATH = Path("backend/data/catalog.json")

def _maxlens_for_template(template_id: str) -> dict[str, int]:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    tmpl = next(t for t in data["templates"] if t["id"] == template_id)
    maxlens = {}
    for f in tmpl.get("options", {}).get("fields", []):
        if f["type"] == "text":
            maxlens[f["id"]] = int(f.get("maxLen", 10**9))
    return maxlens

TEMPLATE_REGULAR = "PLAQUE-140x90-V1"

@pytest.mark.parametrize("text,expect_code", [
    ("In living memory of my twin", "PHRASE_INCORRECT"),
    ("in LIVING memory", "PHRASE_INCORRECT"),
])
def test_phrase_incorrect_warn(text, expect_code):
    lines = {"line_1": text, "line_2": "", "line_3": ""}
    warns = run_qa(lines, template_maxlens=_maxlens_for_template(TEMPLATE_REGULAR), current_year=2025)
    codes = [w.code for w in warns]
    assert expect_code in codes
    # severity should be warn
    assert any(w.code == expect_code and w.severity == "warn" for w in warns)

@pytest.mark.parametrize("line3,expect_code,year", [
    ("1950–2026", "DATE_FUTURE", 2025),
    ("d. 2030", "DATE_FUTURE", 2025),
])
def test_date_future_error(line3, expect_code, year):
    lines = {"line_1": "", "line_2": "", "line_3": line3}
    warns = run_qa(lines, template_maxlens=_maxlens_for_template(TEMPLATE_REGULAR), current_year=year)
    assert any(w.code == expect_code and w.severity == "error" for w in warns)

def test_over_maxlen_warn():
    maxlens = _maxlens_for_template(TEMPLATE_REGULAR)
    long_l1 = "X" * (maxlens.get("line_1", 40) + 1)
    lines = {"line_1": long_l1, "line_2": "", "line_3": ""}
    warns = run_qa(lines, template_maxlens=maxlens, current_year=2025)
    assert any(w.code == "OVER_MAXLEN" and w.severity == "warn" for w in warns)

@pytest.mark.parametrize("has_photo,should_error", [
    (False, True),
    (True, False),
])
def test_photo_missing_rule(has_photo, should_error):
    # Simulate a template that requires a photo (REGULAR does not; we force the rule via require_photo=True)
    lines = {"line_1": "Hello", "line_2": "", "line_3": ""}
    warns = run_qa(lines,
                   template_maxlens=_maxlens_for_template(TEMPLATE_REGULAR),
                   require_photo=True,
                   has_photo=has_photo,
                   current_year=2025)
    has_error = any(w.code == "PHOTO_MISSING" and w.severity == "error" for w in warns)
    assert has_error == should_error
import json
import re
from pathlib import Path
import pytest

# Import the qa helper and pydantic model
from app.utils.qa import run_qa
from app.models import QaWarning

CATALOG_PATH = Path("backend/data/catalog.json")

def _maxlens_for_template(template_id: str) -> dict[str, int]:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    tmpl = next(t for t in data["templates"] if t["id"] == template_id)
    maxlens = {}
    for f in tmpl.get("options", {}).get("fields", []):
        if f["type"] == "text":
            maxlens[f["id"]] = int(f.get("maxLen", 10**9))
    return maxlens

TEMPLATE_REGULAR = "PLAQUE-140x90-V1"

@pytest.mark.parametrize("text,expect_code", [
    ("In living memory of my twin", "PHRASE_INCORRECT"),
    ("in LIVING memory", "PHRASE_INCORRECT"),
])
def test_phrase_incorrect_warn(text, expect_code):
    lines = {"line_1": text, "line_2": "", "line_3": ""}
    warns = run_qa(lines, template_maxlens=_maxlens_for_template(TEMPLATE_REGULAR), current_year=2025)
    codes = [w.code for w in warns]
    assert expect_code in codes
    # severity should be warn
    assert any(w.code == expect_code and w.severity == "warn" for w in warns)

@pytest.mark.parametrize("line3,expect_code,year", [
    ("1950–2026", "DATE_FUTURE", 2025),
    ("d. 2030", "DATE_FUTURE", 2025),
])
def test_date_future_error(line3, expect_code, year):
    lines = {"line_1": "", "line_2": "", "line_3": line3}
    warns = run_qa(lines, template_maxlens=_maxlens_for_template(TEMPLATE_REGULAR), current_year=year)
    assert any(w.code == expect_code and w.severity == "error" for w in warns)

def test_over_maxlen_warn():
    maxlens = _maxlens_for_template(TEMPLATE_REGULAR)
    long_l1 = "X" * (maxlens.get("line_1", 40) + 1)
    lines = {"line_1": long_l1, "line_2": "", "line_3": ""}
    warns = run_qa(lines, template_maxlens=maxlens, current_year=2025)
    assert any(w.code == "OVER_MAXLEN" and w.severity == "warn" for w in warns)

@pytest.mark.parametrize("has_photo,should_error", [
    (False, True),
    (True, False),
])
def test_photo_missing_rule(has_photo, should_error):
    # Simulate a template that requires a photo (REGULAR does not; we force the rule via require_photo=True)
    lines = {"line_1": "Hello", "line_2": "", "line_3": ""}
    warns = run_qa(lines,
                   template_maxlens=_maxlens_for_template(TEMPLATE_REGULAR),
                   require_photo=True,
                   has_photo=has_photo,
                   current_year=2025)
    has_error = any(w.code == "PHOTO_MISSING" and w.severity == "error" for w in warns)
    assert has_error == should_error
    warns = run_qa(lines, template_maxlens={"line_1":30, "line_2":30, "line_3":30}, current_year=2025)
    codes = [w.code for w in warns]
    assert OVER_MAXLEN in codes
    # ensure field is set
    fields = [w.field for w in warns if w.code==OVER_MAXLEN]
    assert "line_1" in fields


def test_photo_missing():
    lines = {"line_1":"","line_2":"","line_3":""}
    warns = run_qa(lines, template_maxlens=None, require_photo=True, has_photo=False, current_year=2025)
    codes = [w.code for w in warns]
    assert PHOTO_MISSING in codes
