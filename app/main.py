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
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

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


@app.get("/download_docs_template", response_model=None)
def download_docs_template() -> FileResponse | HTMLResponse:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docx_path = os.path.join(here, "documentation.docx")
    if os.path.exists(docx_path):
        return FileResponse(
            docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="documentation.docx"
        )
    return HTMLResponse(content="<h1>Documentation file not found</h1>", status_code=404)


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
    try:
        files = [{"name": f.name, "content": f.content} for f in req.files]
        result = generate_document(
            files,
            model=req.model,
            openrouter_key=req.openrouter_api_key,
            anthropic_key=req.anthropic_api_key,
            gemini_key=req.gemini_api_key
        )
        return JSONResponse(content=result.model_dump())
    except Exception as e:
        import traceback
        error_msg = f"Pipeline execution failed: {str(e)}"
        print(f"[ERROR] {error_msg}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": error_msg,
                "error_type": type(e).__name__
            }
        )


@app.post("/generate_document_multipart", response_model=GenerateResponse)
async def generate_multipart(
    files: list[UploadFile] = File(...),
    model: str | None = Form(None),
    openrouter_api_key: str | None = Form(None),
    anthropic_api_key: str | None = Form(None),
    gemini_api_key: str | None = Form(None)
) -> JSONResponse:
    try:
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
    except Exception as e:
        import traceback
        error_msg = f"Pipeline execution failed: {str(e)}"
        print(f"[ERROR] {error_msg}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": error_msg,
                "error_type": type(e).__name__
            }
        )


if __name__ == "__main__":
    import uvicorn
    # Render assigns the port dynamically using the PORT environment variable
    port = int(os.environ.get("PORT", 80))
    # Bind to 0.0.0.0 for external cloud access
    uvicorn.run(app, host="0.0.0.0", port=port)
