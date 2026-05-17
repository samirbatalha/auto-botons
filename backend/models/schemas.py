"""Pydantic schemas para requests/responses da API."""
from typing import Literal
from pydantic import BaseModel, Field

ButtonSize = Literal["38", "44", "58"]


class CropParams(BaseModel):
    """Parâmetros de crop manual vindos do Cropper.js (normalizados 0..1)."""
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    size: float = Field(gt=0, le=1)  # lado do quadrado (será cortado em círculo)


class ProcessedImage(BaseModel):
    """Resultado do processamento de uma imagem."""
    id: str
    original_name: str
    preview_url: str
    width: int
    height: int


class GeneratePdfRequest(BaseModel):
    button_size: ButtonSize
    image_ids: list[str]


class RecropRequest(BaseModel):
    image_id: str
    crop: CropParams
