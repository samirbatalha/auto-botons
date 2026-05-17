"""Armazenamento temporário das imagens processadas em sessão.

Sem banco: tudo vive numa pasta temp, com TTL de 1h. Limpeza preguiçosa
(checada em cada upload, sem thread em background — funciona em Render free tier
sem manter processo extra).
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from threading import Lock

from PIL import Image

TMP_ROOT = Path(__file__).resolve().parent.parent / ".tmp_uploads"
TMP_ROOT.mkdir(exist_ok=True)
TTL_SECONDS = 60 * 60  # 1 hora


@dataclass
class StoredImage:
    image_id: str
    original_name: str
    original_path: Path
    processed_path: Path
    width: int
    height: int
    created_at: float = field(default_factory=time.time)


_REGISTRY: dict[str, StoredImage] = {}
_LOCK = Lock()


def _cleanup_expired() -> None:
    now = time.time()
    expired = [k for k, v in _REGISTRY.items() if now - v.created_at > TTL_SECONDS]
    for k in expired:
        entry = _REGISTRY.pop(k, None)
        if entry:
            for p in (entry.original_path, entry.processed_path):
                p.unlink(missing_ok=True)


def save(original_bytes: bytes, original_name: str, processed: Image.Image) -> StoredImage:
    with _LOCK:
        _cleanup_expired()
        image_id = uuid.uuid4().hex
        original_path = TMP_ROOT / f"{image_id}_orig{Path(original_name).suffix or '.bin'}"
        processed_path = TMP_ROOT / f"{image_id}.png"

        original_path.write_bytes(original_bytes)
        processed.save(processed_path, format="PNG")

        entry = StoredImage(
            image_id=image_id,
            original_name=original_name,
            original_path=original_path,
            processed_path=processed_path,
            width=processed.width,
            height=processed.height,
        )
        _REGISTRY[image_id] = entry
        return entry


def get(image_id: str) -> StoredImage | None:
    with _LOCK:
        _cleanup_expired()
        return _REGISTRY.get(image_id)


def load_original(image_id: str) -> Image.Image | None:
    entry = get(image_id)
    if not entry or not entry.original_path.exists():
        return None
    return Image.open(BytesIO(entry.original_path.read_bytes()))


def load_processed(image_id: str) -> Image.Image | None:
    entry = get(image_id)
    if not entry or not entry.processed_path.exists():
        return None
    return Image.open(entry.processed_path)


def update_processed(image_id: str, processed: Image.Image) -> StoredImage | None:
    with _LOCK:
        entry = _REGISTRY.get(image_id)
        if not entry:
            return None
        processed.save(entry.processed_path, format="PNG")
        entry.width = processed.width
        entry.height = processed.height
        return entry


def remove(image_id: str) -> None:
    with _LOCK:
        entry = _REGISTRY.pop(image_id, None)
        if entry:
            for p in (entry.original_path, entry.processed_path):
                p.unlink(missing_ok=True)
