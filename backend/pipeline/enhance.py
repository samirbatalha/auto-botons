"""Melhoria clássica de imagem para impressão de boton.

Pipeline: white balance leve → denoise → unsharp mask → boost contraste/saturação.
Tudo via Pillow/OpenCV — sem dependências de IA. Rápido e funciona em qualquer ambiente.
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def _pil_to_cv(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)


def _cv_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


def _auto_white_balance(arr: np.ndarray) -> np.ndarray:
    """Gray-world white balance — simples e robusto."""
    result = arr.astype(np.float32)
    avg_b, avg_g, avg_r = [result[:, :, c].mean() for c in range(3)]
    avg_gray = (avg_b + avg_g + avg_r) / 3.0
    if avg_gray < 1e-3:
        return arr
    result[:, :, 0] *= avg_gray / max(avg_b, 1e-3)
    result[:, :, 1] *= avg_gray / max(avg_g, 1e-3)
    result[:, :, 2] *= avg_gray / max(avg_r, 1e-3)
    return np.clip(result, 0, 255).astype(np.uint8)


def _denoise(arr: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoisingColored(arr, None, h=4, hColor=4, templateWindowSize=7, searchWindowSize=21)


def apply(img: Image.Image, level: str = "balanced") -> Image.Image:
    """Aplica melhoria clássica e retorna nova PIL.Image RGB.

    level:
      - "light":     só unsharp + leve boost (rápido, p/ imagens já boas)
      - "balanced":  pipeline completo (padrão)
      - "strong":    pipeline + denoise mais agressivo (p/ fotos ruidosas/baixa luz)
    """
    base = img.convert("RGB")

    arr = _pil_to_cv(base)
    if level in ("balanced", "strong"):
        arr = _auto_white_balance(arr)
        if level == "strong":
            arr = cv2.fastNlMeansDenoisingColored(arr, None, h=8, hColor=8, templateWindowSize=7, searchWindowSize=21)
        else:
            arr = _denoise(arr)

    out = _cv_to_pil(arr)
    out = out.filter(ImageFilter.UnsharpMask(radius=1.5, percent=140, threshold=3))
    out = ImageEnhance.Contrast(out).enhance(1.10)
    out = ImageEnhance.Color(out).enhance(1.08)

    return out
