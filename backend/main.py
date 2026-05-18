"""FastAPI app: rotas de upload, recrop, geração de PDF + serve frontend estático."""
from __future__ import annotations

import tempfile
from io import BytesIO
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps

MAX_INPUT_SIDE_PX = 1800

from . import storage
from .config import BUTTON_SIZES
from .models.schemas import GeneratePdfRequest, ProcessedImage, RecropRequest
from .pipeline import circle_crop, pdf_builder

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"

app = FastAPI(title="Auto Botons", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/sizes")
def sizes() -> dict[str, dict]:
    """Devolve specs dos tamanhos para o frontend (contador de slots, etc.)."""
    return {
        key: {
            "visible_mm": spec.visible_mm,
            "outer_mm": spec.outer_mm,
            "cols": spec.cols,
            "rows": spec.rows,
            "slots_per_page": spec.slots_per_page,
        }
        for key, spec in BUTTON_SIZES.items()
    }


@app.post("/api/process", response_model=list[ProcessedImage])
async def process_images(
    files: Annotated[list[UploadFile], File()],
) -> list[ProcessedImage]:
    """Recebe N imagens, faz crop circular centrado. Ajuste fino via /api/recrop."""
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    results: list[ProcessedImage] = []
    errors: list[str] = []
    for f in files:
        raw = await f.read()
        if not raw:
            continue
        try:
            img = Image.open(BytesIO(raw))
            img = ImageOps.exif_transpose(img)
            img.thumbnail((MAX_INPUT_SIDE_PX, MAX_INPUT_SIDE_PX), Image.LANCZOS)
        except Exception as e:
            errors.append(f"{f.filename}: arquivo inválido ({e})")
            continue

        try:
            circular = circle_crop.auto(img)
        except Exception as e:
            errors.append(f"{f.filename}: falha no recorte ({type(e).__name__}: {e})")
            continue

        normalized_buf = BytesIO()
        img.convert("RGB").save(normalized_buf, format="JPEG", quality=92)
        entry = storage.save(normalized_buf.getvalue(), f.filename or "imagem.jpg", circular)
        results.append(
            ProcessedImage(
                id=entry.image_id,
                original_name=entry.original_name,
                preview_url=f"/api/preview/{entry.image_id}",
                width=entry.width,
                height=entry.height,
            )
        )

    if not results and errors:
        raise HTTPException(status_code=500, detail="; ".join(errors))
    return results


@app.get("/api/preview/{image_id}")
def preview(image_id: str) -> Response:
    entry = storage.get(image_id)
    if not entry or not entry.processed_path.exists():
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    return FileResponse(entry.processed_path, media_type="image/png")


@app.get("/api/original/{image_id}")
def original(image_id: str) -> Response:
    """Devolve a original (sem máscara) — usado pelo Cropper.js no modal de ajuste."""
    entry = storage.get(image_id)
    if not entry or not entry.original_path.exists():
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    return FileResponse(entry.original_path)


@app.post("/api/recrop", response_model=ProcessedImage)
def recrop(req: RecropRequest) -> ProcessedImage:
    img = storage.load_original(req.image_id)
    if img is None:
        raise HTTPException(status_code=404, detail="Imagem não encontrada")

    img = ImageOps.exif_transpose(img)
    img.thumbnail((MAX_INPUT_SIDE_PX, MAX_INPUT_SIDE_PX), Image.LANCZOS)

    try:
        recropped = circle_crop.manual(img, req.crop)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha no recorte ({type(e).__name__}: {e})")

    entry = storage.update_processed(req.image_id, recropped)
    if entry is None:
        raise HTTPException(status_code=404, detail="Imagem não encontrada")

    return ProcessedImage(
        id=entry.image_id,
        original_name=entry.original_name,
        preview_url=f"/api/preview/{entry.image_id}?v={int(entry.created_at)}",
        width=entry.width,
        height=entry.height,
    )


@app.delete("/api/image/{image_id}")
def delete_image(image_id: str) -> dict[str, str]:
    storage.remove(image_id)
    return {"status": "deleted"}


@app.post("/api/generate-pdf")
def generate_pdf(req: GeneratePdfRequest) -> Response:
    if not req.image_ids:
        raise HTTPException(status_code=400, detail="Nenhuma imagem selecionada")

    images: list[Image.Image] = []
    for img_id in req.image_ids:
        img = storage.load_processed(img_id)
        if img is None:
            raise HTTPException(status_code=404, detail=f"Imagem {img_id} não encontrada")
        images.append(img)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        out_path = Path(tmp.name)

    pdf_builder.build(images, req.button_size, out_path)
    data = out_path.read_bytes()
    out_path.unlink(missing_ok=True)

    filename = f"botons_{req.button_size}mm.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def root_fallback() -> JSONResponse:
        return JSONResponse({"message": "Frontend não encontrado. Veja /docs para a API."})
