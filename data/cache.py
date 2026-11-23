"""Local disk cache for raw API responses.

Entries are keyed on the request path + params *without* the API key, so the
key never ends up in a filename.
"""

import hashlib
import json
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"


def _path_for(endpoint: str, params: dict) -> Path:
    ident = json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True, default=str)
    digest = hashlib.sha256(ident.encode()).hexdigest()[:32]
    return CACHE_DIR / f"{digest}.parquet"


def get(endpoint: str, params: dict) -> bytes | None:
    path = _path_for(endpoint, params)
    return path.read_bytes() if path.exists() else None


def put(endpoint: str, params: dict, content: bytes) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    _path_for(endpoint, params).write_bytes(content)
