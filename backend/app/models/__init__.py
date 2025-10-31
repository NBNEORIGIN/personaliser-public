"""
Models package.
"""

# Import existing models from parent level models.py
# Use absolute import to avoid circular import
import sys
from pathlib import Path

# Import from backend.app.models module (the .py file, not this package)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "backend.app._models", 
    Path(__file__).parent.parent / "models.py"
)
_models_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_models_module)

# Re-export existing models
Severity = _models_module.Severity
QaWarning = _models_module.QaWarning
LineField = _models_module.LineField
TextLine = _models_module.TextLine
OrderItem = _models_module.OrderItem
Rect = _models_module.Rect
PlacedRect = _models_module.PlacedRect
GenerateRequest = _models_module.GenerateRequest
PreviewResponse = _models_module.PreviewResponse
GenerateResponse = _models_module.GenerateResponse
IngestItem = _models_module.IngestItem
IngestResponse = _models_module.IngestResponse

# Import new user/graphics models
from .user import User, Graphic

__all__ = [
    # Existing models
    "Severity", "QaWarning", "LineField", "TextLine", "OrderItem",
    "Rect", "PlacedRect", "GenerateRequest", "PreviewResponse",
    "GenerateResponse", "IngestItem", "IngestResponse",
    # New models
    "User", "Graphic"
]
