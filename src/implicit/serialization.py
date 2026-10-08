import hashlib
import json
from dataclasses import fields, is_dataclass
from typing import cast

from .models import JSON


def json_value(value: object) -> JSON:
    def encode(item: object) -> object:
        if is_dataclass(item) and not isinstance(item, type):
            return {f.name: getattr(item, f.name) for f in fields(item)}
        raise TypeError(f"nonserializable lifecycle value: {type(item).__name__}")

    # Strict serialization rejects opaque runtime handles and nonfinite numbers.
    return cast(JSON, json.loads(json.dumps(value, default=encode, ensure_ascii=False, allow_nan=False)))


def _encode(item: object) -> object:
    if is_dataclass(item) and not isinstance(item, type):
        return {f.name: getattr(item, f.name) for f in fields(item)}
    raise TypeError(f"nonserializable lifecycle value: {type(item).__name__}")


def canonical(value: object) -> str:
    return json.dumps(
        value, default=_encode, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def content_hash(value: object) -> str:
    return hashlib.blake2b(canonical(value).encode("utf-8"), digest_size=16).hexdigest()
