"""Reject sensitive completion fields without importing any provider or research code."""

from __future__ import annotations

import os
from typing import Any

from .serialization import canonical, json_value


def safe(value: Any) -> Any:
    forbidden = {
        "api_key",
        "authorization",
        "password",
        "secret",
        "reasoning",
        "reasoning_content",
        "reasoning_details",
        "chain_of_thought",
        "access_token",
        "headers",
    }

    def check(node: Any) -> None:
        if isinstance(node, dict):
            if any(str(k).lower() in forbidden for k in node):
                raise ValueError("non-public durable content rejected")
            for child in node.values():
                check(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                check(child)

    check(value)
    serialized = canonical(value)
    key = os.environ.get("OPENROUTER_API_KEY")
    if key and key in serialized:
        raise ValueError("credential durable content rejected")
    return json_value(value)
