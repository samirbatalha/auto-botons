"""Smoke test: gera 3 imagens sintéticas, processa e exporta um PDF para cada tamanho.

Roda:  python -m scripts.smoke_test
Saída: scripts/_out/test_{38,44,58}.pdf
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from backend.pipeline import circle_crop, pdf_builder  # noqa: E402


OUT_DIR = ROOT / "scripts" / "_out"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _make_test_image(label: str, color: tuple[int, int, int], size: int = 800) -> Image.Image:
    img = Image.new("RGB", (size, size), color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", size // 5)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2), label, fill=(255, 255, 255), font=font)
    draw.ellipse((40, 40, size - 40, size - 40), outline=(255, 255, 255), width=8)
    return img


def main() -> None:
    test_images = [
        _make_test_image("A", (180, 30, 60)),
        _make_test_image("B", (30, 90, 180)),
        _make_test_image("C", (40, 150, 80)),
        _make_test_image("D", (220, 120, 30)),
        _make_test_image("E", (110, 40, 180)),
    ]
    processed = [circle_crop.auto(img) for img in test_images]

    for size_key in ("38", "44", "58"):
        out = OUT_DIR / f"test_{size_key}.pdf"
        pdf_builder.build(processed, size_key, out)
        print(f"[OK] {out.relative_to(ROOT)}  ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
