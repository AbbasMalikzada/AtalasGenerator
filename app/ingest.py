"""Приём и нормализация входных файлов.

Поддерживаемые форматы: .txt, .md, .json, .py, .java
JSON предварительно красиво форматируется (чтобы модель видела структуру),
исходный код помечается языком. Слишком большие файлы усекаются с пометкой,
чтобы не раздувать число токенов.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List

# Мягкий лимит символов на один файл при подаче в LLM (~ экономия токенов).
MAX_CHARS_PER_FILE = 20_000

_EXT_LANG = {
    ".py": "python",
    ".java": "java",
    ".md": "markdown",
    ".txt": "text",
    ".json": "json",
}


@dataclass
class NormalizedFile:
    name: str
    kind: str
    content: str
    truncated: bool


def _ext(name: str) -> str:
    return os.path.splitext(name)[1].lower()


def normalize_one(name: str, content: str) -> NormalizedFile:
    ext = _ext(name)
    kind = _EXT_LANG.get(ext, "text")
    text = content if content is not None else ""

    if kind == "json":
        try:
            parsed = json.loads(text)
            text = json.dumps(parsed, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, ValueError):
            # оставляем как есть — модель разберётся с «сырым» текстом
            pass

    truncated = False
    if len(text) > MAX_CHARS_PER_FILE:
        text = text[:MAX_CHARS_PER_FILE]
        truncated = True

    return NormalizedFile(name=name, kind=kind, content=text, truncated=truncated)


def normalize_files(files: List[dict]) -> List[NormalizedFile]:
    out: List[NormalizedFile] = []
    for f in files:
        name = f.get("name") if isinstance(f, dict) else getattr(f, "name", "unknown")
        content = (
            f.get("content") if isinstance(f, dict) else getattr(f, "content", "")
        )
        if not name:
            continue
        out.append(normalize_one(name, content or ""))
    return out


def render_for_prompt(nf: NormalizedFile) -> str:
    """Готовит блок одного файла для промпта с чёткими разделителями."""
    note = " [TRUNCATED]" if nf.truncated else ""
    return (
        f"<file name=\"{nf.name}\" type=\"{nf.kind}\"{note}>\n"
        f"{nf.content}\n"
        f"</file>"
    )


def load_dir(path: str) -> List[dict]:
    """Загружает поддерживаемые файлы из директории (удобно для CLI/тестов)."""
    supported = set(_EXT_LANG.keys())
    result: List[dict] = []
    for root, _dirs, names in os.walk(path):
        for n in sorted(names):
            if _ext(n) in supported:
                full = os.path.join(root, n)
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    result.append({"name": os.path.relpath(full, path), "content": fh.read()})
    return result
