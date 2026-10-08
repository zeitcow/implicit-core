"""Versioned local recovery contracts; runtime objects are always rebound by the caller."""

from __future__ import annotations

import hashlib
from dataclasses import fields, is_dataclass
from types import UnionType
from typing import Any, TypeVar, get_args, get_origin, get_type_hints

from .serialization import json_value

T = TypeVar("T")


def restore(kind: type[T], value: Any) -> T:
    """Decode known product dataclasses only; no imports or executable objects from records."""
    if not is_dataclass(kind) or not isinstance(value, dict):
        raise ValueError("expected a dataclass record")
    hints = get_type_hints(kind)
    return kind(**{f.name: _decode(hints[f.name], value[f.name]) for f in fields(kind) if f.name in value})


def _decode(kind: Any, value: Any) -> Any:
    origin, args = get_origin(kind), get_args(kind)
    if isinstance(kind, type) and is_dataclass(kind):
        return restore(kind, value)
    if origin is tuple:
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_decode(args[0], x) for x in value)
        return tuple(_decode(t, x) for t, x in zip(args, value, strict=True))
    if origin is UnionType:
        return value  # JSON and optional scalar fields contain no runtime handles.
    return value


def seed_streams(root: int, attempt: int) -> dict[str, int]:
    return {
        name: int.from_bytes(
            hashlib.blake2b(f"implicit-seeds-v2:{root}:{attempt}:{name}".encode(), digest_size=8).digest(),
            "big",
        )
        for name in ("proposal", "search", "allocation", "environment", "agent", "user", "training")
    }


def strategy_record(strategy: object) -> object:
    # Built-ins and customer strategies with JSON configuration are restorable by rebinding.
    return {
        "type": f"{type(strategy).__module__}.{type(strategy).__qualname__}",
        "config": json_value(vars(strategy)),
    }
