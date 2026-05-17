"""Recorte circular com detecção de rosto (auto) e versão manual."""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from ..models.schemas import CropParams

_FACE_CASCADE: cv2.CascadeClassifier | None = None


def _face_cascade() -> cv2.CascadeClassifier:
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(path)
    return _FACE_CASCADE


def _detect_face_center(img: Image.Image) -> tuple[int, int] | None:
    """Retorna (cx, cy) do maior rosto encontrado, ou None."""
    gray = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    faces = _face_cascade().detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(48, 48))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return x + w // 2, y + h // 2


def _square_around(img: Image.Image, cx: int, cy: int) -> Image.Image:
    """Recorta o maior quadrado possível ao redor de (cx, cy)."""
    w, h = img.size
    side = min(w, h)
    half = side // 2

    left = max(0, min(cx - half, w - side))
    top = max(0, min(cy - half, h - side))
    return img.crop((left, top, left + side, top + side))


def _apply_circle_mask(square: Image.Image) -> Image.Image:
    """Recebe imagem quadrada, devolve PNG com máscara circular anti-aliased."""
    size = square.size[0]
    scale = 4
    big = size * scale
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(square.convert("RGBA"), (0, 0), mask)
    return out


def auto(img: Image.Image, target_size_px: int | None = None) -> Image.Image:
    """Recorte automático: centra no rosto se houver, senão no centro geométrico."""
    rgb = img.convert("RGB")
    center = _detect_face_center(rgb)
    if center is None:
        w, h = rgb.size
        center = (w // 2, h // 2)

    square = _square_around(rgb, *center)
    if target_size_px and square.size[0] != target_size_px:
        square = square.resize((target_size_px, target_size_px), Image.LANCZOS)
    return _apply_circle_mask(square)


def manual(img: Image.Image, params: CropParams, target_size_px: int | None = None) -> Image.Image:
    """Aplica crop manual vindo do Cropper.js (coords normalizadas)."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    side_px = int(round(params.size * min(w, h)))
    left = int(round(params.x * w))
    top = int(round(params.y * h))

    left = max(0, min(left, w - side_px))
    top = max(0, min(top, h - side_px))

    square = rgb.crop((left, top, left + side_px, top + side_px))
    if target_size_px and square.size[0] != target_size_px:
        square = square.resize((target_size_px, target_size_px), Image.LANCZOS)
    return _apply_circle_mask(square)
