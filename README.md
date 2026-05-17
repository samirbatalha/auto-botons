# Auto Botons

Webapp para gerar PDFs prontos para impressão de botons de 38mm, 44mm e 58mm. Suba várias imagens, ajusta crop circular, baixa o PDF e imprime em A4 escala 100%.

Funciona no notebook (via navegador) e no celular (instalável como PWA — "Adicionar à tela inicial").

---

## Stack

- **Backend:** FastAPI + Pillow + OpenCV + ReportLab
- **Frontend:** HTML + Tailwind (CDN) + Alpine.js + Cropper.js
- **Deploy:** Render.com (free tier)

---

## Rodar localmente

Pré-requisitos: Python 3.11+ (3.14 também funciona com as deps do `requirements.txt`).

```powershell
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8765
```

Abre http://127.0.0.1:8765 no navegador.

### Acessar do celular pelo Wi-Fi local

Roda o servidor escutando em todas as interfaces:

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8765
```

Descubra o IP do PC (`ipconfig`) e no celular abra `http://<IP-do-PC>:8765`.

---

## Deploy no Render (gratuito)

1. Cria um repositório no GitHub e dá push deste projeto.
2. Em [render.com](https://render.com), conecta o repo e cria um **Web Service** apontando para ele.
3. O `render.yaml` na raiz já configura build, start, healthcheck e Python 3.11.
4. Em ~3 minutos a URL pública sobe (`https://auto-botons.onrender.com` ou similar).
5. No celular: abre a URL → menu do Chrome → **Adicionar à tela inicial** → vira app standalone.

> **Free tier:** o servidor dorme após 15min sem uso. A primeira request da sessão demora ~30s (cold start). Aceitável para uso pessoal.

---

## Como funciona

Pipeline por imagem (em `backend/pipeline/`):

```
upload → enhance.apply     (white balance + denoise + unsharp + contraste)
       → circle_crop.auto  (detecta rosto, centraliza, aplica máscara circular)
       → preview no grid
       → (opcional) recrop manual via Cropper.js
       → pdf_builder.build (gera A4 com gabarito + imagens nos slots)
```

Especificações em `backend/config.py`:

| Tamanho | Visível | Corte | Grid | Por A4 |
|---|---|---|---|---|
| 38mm | 38mm | 48mm | 3×5 | 15 |
| 44mm | 44mm | 54mm | 3×4 | 12 |
| 58mm | 58mm | 68mm | 2×3 | 6 |

**Por que a imagem ocupa o círculo de corte (48/54/68mm) e não o visível?** Os ~5mm extras dobram para trás do boton durante a montagem — sem isso, fica borda branca na lateral.

---

## Imprimir corretamente

1. Baixa o PDF gerado.
2. Imprime em papel A4 (preferencialmente couché 90-120g/m² para boton).
3. **No diálogo de impressão: escala 100% (NÃO use "ajustar à página").**
4. Confere com régua: 10mm na régua impressa = 10mm reais.
5. Recorta na linha contínua, alinha a área tracejada com a frente do boton, monta.

---

## Estrutura

```
auto-botons/
├── backend/
│   ├── main.py              # FastAPI app + rotas
│   ├── config.py            # Specs dos tamanhos
│   ├── storage.py           # Armazenamento temporário (TTL 1h)
│   ├── models/schemas.py    # Pydantic
│   └── pipeline/
│       ├── enhance.py       # Melhoria clássica de imagem
│       ├── circle_crop.py   # Recorte circular + detecção de rosto
│       ├── upscale.py       # Stub para futuro upscaling com IA
│       └── pdf_builder.py   # Gera PDF A4 com gabarito + imagens
├── frontend/
│   ├── index.html           # UI (1 página)
│   ├── app.js               # Alpine state + chamadas API
│   ├── styles.css           # Customizações sobre Tailwind/Cropper
│   ├── manifest.json        # PWA
│   ├── sw.js                # Service worker (offline shell)
│   └── icons/               # Ícones PWA gerados em scripts/make_icons.py
├── gabaritos/               # PDFs originais (referência visual)
├── scripts/
│   ├── smoke_test.py        # Gera 3 PDFs de teste (1 por tamanho)
│   ├── make_test_imgs.py    # Gera JPGs sintéticos pra testar upload
│   └── make_icons.py        # (Re)gera ícones PWA
├── render.yaml              # Deploy
└── requirements (via backend/requirements.txt)
```

---

## Roadmap

- [ ] **Fase 9 (futuro):** plugar IA real de upscaling. O `backend/pipeline/upscale.py` já tem a interface preparada — basta implementar `provider="replicate"` chamando a API do Real-ESRGAN no Replicate (env var `REPLICATE_API_TOKEN`).
- [ ] (opcional) Background removal automático via `rembg`.
- [ ] (opcional) Mix de tamanhos diferentes no mesmo PDF.
