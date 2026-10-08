"""Opt-in exact page retention, stored once per canonical content hash."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Protocol, cast

from .models import JSON


def payload_hash(payload: bytes) -> str:
    return hashlib.blake2b(payload, digest_size=16).hexdigest()


class ContentStore(Protocol):
    def put(self, digest: str, payload: bytes) -> bool:
        """Persist canonical bytes; return whether new content was written."""
        ...

    def get(self, digest: str) -> JSON: ...


class DirectoryContentStore:
    """Explicit local replay policy. No payload files are written unless this is supplied."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        if self.directory.is_symlink():
            raise ValueError("content directory must not be a symlink")
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, digest: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{32}", digest):
            raise ValueError("invalid content hash")
        path = self.directory / f"{digest}.json"
        if path.is_symlink():
            raise ValueError("content file must not be a symlink")
        return path

    def put(self, digest: str, payload: bytes) -> bool:
        if payload_hash(payload) != digest:
            raise ValueError("content/hash mismatch")
        path = self._path(digest)
        if path.exists():
            if path.read_bytes() != payload:
                raise ValueError("existing content is corrupt")
            return False
        # Atomic publication prevents a failed write from becoming an apparently valid page.
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(dir=self.directory, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            except BaseException:
                stream.close()
                temporary.unlink(missing_ok=True)
                raise
        try:
            try:
                os.link(temporary, path)
                return True
            except FileExistsError:
                if path.read_bytes() != payload:
                    raise ValueError("existing content is corrupt") from None
                return False
        finally:
            temporary.unlink(missing_ok=True)

    def get(self, digest: str) -> JSON:
        payload = self._path(digest).read_bytes()
        if payload_hash(payload) != digest:
            raise ValueError("retained content is corrupt")
        return cast(JSON, json.loads(payload))


def execution_payload(payload: JSON, store: ContentStore) -> JSON:
    """Resolve an optional journal execution artifact; hash verification belongs to the store."""
    if isinstance(payload, dict) and payload.get("format") == "execution-v2":
        digest = payload.get("artifact_hash")
        if not isinstance(digest, str):
            raise ValueError("invalid execution artifact reference")
        return store.get(digest)
    return payload
