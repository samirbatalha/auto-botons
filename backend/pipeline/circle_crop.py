"""Recorte circular puro em Pillow — sem OpenCV, sem detecção de rosto.

Posicionamento fino é feito pelo Cropper.js no frontend (modal de ajuste manual).
"""
from __future__ import annotations

from PIL import Image, ImageDraw

from ..models.schemas import CropParams


def _square_center(img: Image.Image) -> Image.Image:
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def _apply_circle_mask(square: Image.Image) -> Image.Image:
    """Aplica máscara circular anti-aliased usando supersampling."""
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
    """Crop centrado + máscara circular. Ajuste fino é via crop manual no frontend."""
    rgb = img.convert("RGB")
    square = _square_center(rgb)
    if target_size_px and square.size[0] != target_size_px:
        square = square.resize((target_size_px, target_size_px), Image.LANCZOS)
    return _apply_circle_mask(square)


def manual(img: Image.Image, params: CropParams, target_size_px: int | None = None) -> Image.Image:
    """Aplica crop manual vindo do Cropper.js (coords normalizadas 0..1)."""
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
