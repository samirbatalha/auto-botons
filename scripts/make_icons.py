"""Gera os ícones PWA (192, 512, maskable 512) — um círculo escuro com um boton ilustrado."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "frontend" / "icons"
OUT.mkdir(parents=True, exist_ok=True)


def _make_icon(size: int, maskable: bool = False) -> Image.Image:
    img = Image.new("RGBA", (size, size), (15, 23, 42, 255))  # slate-950
    draw = ImageDraw.Draw(img)

    safe = size if not maskable else int(size * 0.8)
    pad = (size - safe) // 2

    inset = size // 8
    cx = size // 2
    cy = size // 2
    r = safe // 2 - inset

    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(99, 102, 241, 255))

    r2 = int(r * 0.72)
    draw.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=(255, 255, 255, 255))

    r3 = int(r * 0.40)
    draw.ellipse((cx - r3, cy - r3, cx + r3, cy + r3), fill=(99, 102, 241, 255))

    return img


def main() -> None:
    _make_icon(192).save(OUT / "icon-192.png")
    _make_icon(512).save(OUT / "icon-512.png")
    _make_icon(512, maskable=True).save(OUT / "icon-maskable-512.png")
    print(f"Ícones gerados em {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
