"""HTTP API.

POST /generate_document
  Тело запроса (JSON):
    {
      "files": [{"name": "notes.md", "content": "..."}, ...],
      "model": "<необязательно: id модели>"
    }
  Ответ — строго в формате из ТЗ: { document, metadata, trace }.

Запуск:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse

from .pipeline import generate_document, save_app_config, load_app_config
from .schema import GenerateRequest, GenerateResponse, ConfigSettings

app = FastAPI(title="Project Documentation Generator", version="1.0.0")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    here = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(here, "dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/config", response_model=ConfigSettings)
def get_config() -> ConfigSettings:
    cfg = load_app_config()
    return ConfigSettings(
        default_model=cfg.get("default_model"),
        openrouter_api_key=cfg.get("openrouter_api_key"),
        anthropic_api_key=cfg.get("anthropic_api_key"),
        gemini_api_key=cfg.get("gemini_api_key")
    )


@app.post("/config")
def save_config(settings: ConfigSettings) -> dict:
    save_app_config({
        "default_model": settings.default_model,
        "openrouter_api_key": settings.openrouter_api_key,
        "anthropic_api_key": settings.anthropic_api_key,
        "gemini_api_key": settings.gemini_api_key
    })
    return {"status": "success", "message": "Configuration saved successfully"}


@app.post("/generate_document", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> JSONResponse:
    files = [{"name": f.name, "content": f.content} for f in req.files]
    result = generate_document(
        files,
        model=req.model,
        openrouter_key=req.openrouter_api_key,
        anthropic_key=req.anthropic_api_key,
        gemini_key=req.gemini_api_key
    )
    return JSONResponse(content=result.model_dump())


@app.post("/generate_document_multipart", response_model=GenerateResponse)
async def generate_multipart(
    files: list[UploadFile] = File(...),
    model: str | None = Form(None),
    openrouter_api_key: str | None = Form(None),
    anthropic_api_key: str | None = Form(None),
    gemini_api_key: str | None = Form(None)
) -> JSONResponse:
    doc_files = []
    for f in files:
        content_bytes = await f.read()
        try:
            content_str = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            content_str = ""
        doc_files.append({"name": f.filename, "content": content_str})

    result = generate_document(
        doc_files,
        model=model,
        openrouter_key=openrouter_api_key,
        anthropic_key=anthropic_api_key,
        gemini_key=gemini_api_key
    )
    return JSONResponse(content=result.model_dump())
