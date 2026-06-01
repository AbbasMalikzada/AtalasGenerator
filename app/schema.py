"""Строгая схема результата и её валидация/нормализация.

Гарантирует, что в ответе всегда присутствуют ВСЕ поля документа в нужных
типах. Отсутствующие данные не выдумываются — пустая строка или пустой список.
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


# Поля документа, разбитые по типу значения.
STR_FIELDS = [
    "project_overview",
    "technical_solution",
    "architecture",
    "timeline",
    "budget",
]
LIST_FIELDS = [
    "goals",
    "requirements",
    "team",
    "risks",
]
ALL_DOC_FIELDS = STR_FIELDS + LIST_FIELDS


class InputFile(BaseModel):
    name: str
    content: str


class GenerateRequest(BaseModel):
    files: List[InputFile] = Field(default_factory=list)
    # Необязательное переопределение модели для конкретного запроса.
    model: str | None = None
    # Опциональные ключи API для гибкости UI
    openrouter_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None


class Document(BaseModel):
    project_overview: str = ""
    goals: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    technical_solution: str = ""
    architecture: str = ""
    team: List[str] = Field(default_factory=list)
    timeline: str = ""
    budget: str = ""
    risks: List[str] = Field(default_factory=list)


class Metadata(BaseModel):
    model_name: str = ""
    llm_calls: int = 0
    total_tokens: int = 0
    duration_ms: int = 0


class Trace(BaseModel):
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    document: Document
    metadata: Metadata
    trace: Trace


class ConfigSettings(BaseModel):
    default_model: str | None = None
    openrouter_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None


def coerce_document(raw: Dict[str, Any] | None) -> Document:
    """Приводит произвольный словарь от LLM к строгой схеме документа.

    - неизвестные ключи отбрасываются;
    - строковые поля, пришедшие как список, склеиваются; и наоборот;
    - None -> пустое значение.
    Это защищает выход от структурных галлюцинаций модели.
    """
    raw = raw or {}
    out: Dict[str, Any] = {}

    for f in STR_FIELDS:
        v = raw.get(f, "")
        if v is None:
            v = ""
        if isinstance(v, list):
            v = " ".join(str(x).strip() for x in v if str(x).strip())
        out[f] = str(v).strip()

    for f in LIST_FIELDS:
        v = raw.get(f, [])
        if v is None:
            v = []
        if isinstance(v, str):
            v = [v] if v.strip() else []
        if isinstance(v, list):
            v = [str(x).strip() for x in v if str(x).strip()]
        else:
            v = [str(v).strip()]
        # дедупликация с сохранением порядка
        seen = set()
        deduped = []
        for item in v:
            if item.lower() not in seen:
                seen.add(item.lower())
                deduped.append(item)
        out[f] = deduped

    return Document(**out)
