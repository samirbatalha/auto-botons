"""Gera 4 JPGs de teste em scripts/_out/uploads/ para usar no E2E do frontend."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "_out" / "uploads"
OUT.mkdir(parents=True, exist_ok=True)

samples = [
    ("foto1.jpg", "1", (180, 30, 60)),
    ("foto2.jpg", "2", (30, 90, 180)),
    ("foto3.jpg", "3", (40, 150, 80)),
    ("foto4.jpg", "4", (220, 120, 30)),
]

for name, label, color in samples:
    img = Image.new("RGB", (1200, 1200), color)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 400)
    except Exception:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((1200 - tw) / 2, (1200 - th) / 2 - 60), label, fill=(255, 255, 255), font=font)
    d.ellipse((80, 80, 1120, 1120), outline=(255, 255, 255), width=12)
    img.save(OUT / name, quality=90)
    print(f"[OK] {OUT.relative_to(Path.cwd()) / name}")
