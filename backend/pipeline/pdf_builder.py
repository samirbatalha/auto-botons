"""Gera PDF A4 com gabarito de impressão de botons.

Replica visualmente os gabaritos existentes em `gabaritos/*.pdf`:
- Header e footer com texto descritivo
- Grid de círculos: externo (sólido = corte), interno (tracejado = área visível), cruz central
- Imagens do usuário coladas centradas em cada slot

REGRA CRÍTICA: a imagem ocupa o círculo EXTERNO (corte), não o interno.
Os ~5mm extras dobram para trás do boton — sem isso, fica borda branca na lateral.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import black, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from ..config import A4_HEIGHT_MM, A4_WIDTH_MM, BUTTON_SIZES, LEGEND, PRINT_NOTE, ButtonSpec


HEADER_HEIGHT_MM = 18
FOOTER_HEIGHT_MM = 14
LINE_COLOR = HexColor("#666666")


def _slot_positions(spec: ButtonSpec) -> list[tuple[float, float]]:
    """Retorna (cx, cy) em mm de cada slot, distribuídos uniformemente na página.

    Distribui o espaço restante (após header/footer) igualmente entre margens e gaps.
    """
    usable_w = A4_WIDTH_MM
    usable_h = A4_HEIGHT_MM - HEADER_HEIGHT_MM - FOOTER_HEIGHT_MM
    diameter = spec.outer_mm

    gap_x = (usable_w - spec.cols * diameter) / (spec.cols + 1)
    gap_y = (usable_h - spec.rows * diameter) / (spec.rows + 1)

    positions: list[tuple[float, float]] = []
    for row in range(spec.rows):
        cy_from_top = HEADER_HEIGHT_MM + gap_y + diameter / 2 + row * (diameter + gap_y)
        cy = A4_HEIGHT_MM - cy_from_top
        for col in range(spec.cols):
            cx = gap_x + diameter / 2 + col * (diameter + gap_x)
            positions.append((cx, cy))
    return positions


def _draw_slot_marks(c: canvas.Canvas, cx_mm: float, cy_mm: float, spec: ButtonSpec) -> None:
    """Desenha círculo externo (sólido), interno (tracejado) e cruz central."""
    cx, cy = cx_mm * mm, cy_mm * mm

    c.setStrokeColor(LINE_COLOR)
    c.setLineWidth(0.4)
    c.setDash()
    c.circle(cx, cy, (spec.outer_mm / 2) * mm, stroke=1, fill=0)

    c.setDash(1.4, 1.4)
    c.circle(cx, cy, (spec.visible_mm / 2) * mm, stroke=1, fill=0)
    c.setDash()

    cross = 2 * mm
    c.setLineWidth(0.3)
    c.line(cx - cross, cy, cx + cross, cy)
    c.line(cx, cy - cross, cx, cy + cross)


def _draw_image_in_slot(c: canvas.Canvas, img: Image.Image, cx_mm: float, cy_mm: float, spec: ButtonSpec) -> None:
    """Cola imagem (PNG com canal alpha circular) centrada no slot.

    Tamanho da imagem = círculo externo. Como já é circular (com alpha),
    o ReportLab respeita a transparência fora do círculo.
    """
    diameter_mm = spec.outer_mm
    cx, cy = cx_mm * mm, cy_mm * mm
    half = (diameter_mm / 2) * mm

    buf = BytesIO()
    img.convert("RGBA").save(buf, format="PNG")
    buf.seek(0)
    reader = ImageReader(buf)

    c.drawImage(
        reader,
        cx - half,
        cy - half,
        width=diameter_mm * mm,
        height=diameter_mm * mm,
        mask="auto",
        preserveAspectRatio=False,
    )


def _draw_header_footer(c: canvas.Canvas, spec: ButtonSpec, page_num: int, total_pages: int) -> None:
    c.setFillColor(black)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(15 * mm, (A4_HEIGHT_MM - 12) * mm, spec.header)

    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#444444"))
    c.drawString(15 * mm, (A4_HEIGHT_MM - 16) * mm, spec.footer)

    c.setFont("Helvetica", 7)
    c.drawString(15 * mm, 10 * mm, LEGEND)
    c.drawString(15 * mm, 7 * mm, PRINT_NOTE)

    if total_pages > 1:
        c.drawRightString((A4_WIDTH_MM - 15) * mm, 7 * mm, f"Página {page_num} de {total_pages}")

    c.setFillColor(black)


def build(images: list[Image.Image], button_size: str, out_path: Path) -> Path:
    """Gera PDF A4 com `images` distribuídas em páginas do gabarito do tamanho escolhido.

    Se houver mais imagens que slots/página, gera múltiplas páginas no mesmo PDF.
    """
    if button_size not in BUTTON_SIZES:
        raise ValueError(f"Tamanho inválido: {button_size}. Use uma de {list(BUTTON_SIZES)}")

    spec = BUTTON_SIZES[button_size]
    positions = _slot_positions(spec)
    per_page = spec.slots_per_page
    total_pages = max(1, (len(images) + per_page - 1) // per_page)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=A4)
    c.setTitle(spec.header)

    for page_idx in range(total_pages):
        _draw_header_footer(c, spec, page_idx + 1, total_pages)

        page_images = images[page_idx * per_page : (page_idx + 1) * per_page]

        for slot_idx, (cx_mm, cy_mm) in enumerate(positions):
            if slot_idx < len(page_images):
                _draw_image_in_slot(c, page_images[slot_idx], cx_mm, cy_mm, spec)
            _draw_slot_marks(c, cx_mm, cy_mm, spec)

        c.showPage()

    c.save()
    return out_path
