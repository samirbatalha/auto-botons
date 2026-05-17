"""Interface de upscaling/melhoria.

Hoje só faz melhoria clássica (delega para `enhance.apply`). Amanhã, basta plugar
um provider de IA (Replicate Real-ESRGAN, por exemplo) sem mudar os callsites.
"""
from __future__ import annotations

from PIL import Image

from . import enhance


def enhance_image(img: Image.Image, provider: str = "classic", level: str = "balanced") -> Image.Image:
    """Aplica melhoria de imagem.

    provider:
      - "classic":   Pillow/OpenCV (sempre disponível)
      - "replicate": (FUTURO) Real-ESRGAN via API Replicate — requer REPLICATE_API_TOKEN
    """
    if provider == "replicate":
        raise NotImplementedError(
            "Provider 'replicate' ainda não implementado. "
            "Quando implementar, ler REPLICATE_API_TOKEN do env e chamar a API."
        )
    return enhance.apply(img, level=level)
