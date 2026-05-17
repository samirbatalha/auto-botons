"""Especificações de cada tamanho de boton.

Dimensões em mm. A imagem do usuário é encaixada no círculo EXTERNO (corte),
porque os ~5mm extras dobram para trás do boton durante a montagem.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ButtonSpec:
    visible_mm: float
    outer_mm: float
    cols: int
    rows: int
    header: str
    footer: str

    @property
    def slots_per_page(self) -> int:
        return self.cols * self.rows


BUTTON_SIZES: dict[str, ButtonSpec] = {
    "38": ButtonSpec(
        visible_mm=38,
        outer_mm=48,
        cols=3,
        rows=5,
        header="Gabarito de impressão — Botão 38mm",
        footer="Círculo externo (cortar): 48mm  |  Área visível do botão (linha tracejada): 38mm  |  Total: 15 botões por folha A4",
    ),
    "44": ButtonSpec(
        visible_mm=44,
        outer_mm=54,
        cols=3,
        rows=4,
        header="Gabarito de impressão — Botão 44mm",
        footer="Círculo externo (cortar): 54mm  |  Área visível do botão (linha tracejada): 44mm  |  Total: 12 botões por folha A4",
    ),
    "58": ButtonSpec(
        visible_mm=58,
        outer_mm=68,
        cols=2,
        rows=3,
        header="Gabarito de impressão — Botão 58mm",
        footer="Círculo externo (cortar): 68mm  |  Área visível do botão (linha tracejada): 58mm  |  Total: 6 botões por folha A4",
    ),
}

LEGEND = (
    "— Linha contínua: cortar aqui    "
    "- - - Linha tracejada: área visível do botão (depois da dobra)    "
    "+ Centro: alinhar imagem"
)
PRINT_NOTE = "Imprimir em escala 100% (sem ajustar à página). Confira a régua: 10mm = 10mm."

A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0
