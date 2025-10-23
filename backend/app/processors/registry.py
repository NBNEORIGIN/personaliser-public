from __future__ import annotations
from typing import Callable, Dict, Tuple, List
from ..models import OrderItem
from ..models import IngestItem

RenderFn = Callable[[OrderItem], str]

_registry: Dict[Tuple[str, str], RenderFn] = {}
BatchProcessorFn = Callable[[List[IngestItem], dict], Tuple[str, str, list[str]]]
_batch_registry: Dict[str, BatchProcessorFn] = {}

def register(name: str, version: str, fn: RenderFn) -> None:
    _registry[(name, version)] = fn

def get(name: str, version: str) -> RenderFn:
    key = (name, version)
    if key not in _registry:
        raise KeyError(f"Processor not found: {name} v{version}")
    return _registry[key]

def register_batch(key: str, fn: BatchProcessorFn) -> None:
    _batch_registry[key] = fn

def get_batch(key: str) -> BatchProcessorFn:
    if key not in _batch_registry:
        raise KeyError(f"Batch processor not found: {key}")
    return _batch_registry[key]

def key_for_item(item) -> str:
    dt = (getattr(item, "decoration_type", None) or "").lower()
    if dt == "photo":
        return "photo_basic_v1"
    if dt == "graphic":
        return "regular_stake_v1"
    return "text_only_v1"
