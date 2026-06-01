"""Тесты pipeline в offline-режиме (FakeLLM, без сети).

Запуск:  DOCGEN_FAKE=1 python tests/test_pipeline.py
"""
from __future__ import annotations

import os
import sys

# Добавляем родительскую директорию (корень проекта) в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DOCGEN_FAKE"] = "1"

from app.ingest import load_dir  # noqa: E402
from app.pipeline import generate_document  # noqa: E402
from app.schema import ALL_DOC_FIELDS, coerce_document  # noqa: E402


def test_schema_always_complete():
    res = generate_document([])  # пустой вход
    doc = res.document.model_dump()
    for field in ALL_DOC_FIELDS:
        assert field in doc, f"missing field {field}"
    assert res.metadata.llm_calls == 0
    assert isinstance(res.trace.steps, list)


def test_no_fabrication_on_empty():
    res = generate_document([])
    d = res.document
    assert d.project_overview == ""
    assert d.goals == []
    assert d.budget == ""


def test_coerce_drops_unknown_and_fixes_types():
    raw = {
        "project_overview": ["a", "b"],     # список -> строка
        "goals": "одна цель",                # строка -> список
        "risks": None,                        # None -> []
        "totally_made_up": "x",              # неизвестное поле выкидывается
    }
    doc = coerce_document(raw).model_dump()
    assert doc["project_overview"] == "a b"
    assert doc["goals"] == ["одна цель"]
    assert doc["risks"] == []
    assert "totally_made_up" not in doc


def test_pipeline_on_sample_dir():
    # Гарантируем холодный кэш для проверки полной двухэтапной оркестрации
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_file = os.path.join(root_dir, ".fact_cache.json")
    if os.path.exists(cache_file):
        try:
            os.remove(cache_file)
        except Exception:
            pass

    here = os.path.dirname(os.path.abspath(__file__))
    sample = os.path.join(os.path.dirname(here), "sample_data")
    files = load_dir(sample)
    assert files, "sample_data must contain files"
    res = generate_document(files)
    # минимум 2 вызова LLM (extraction + synthesis) при холодном запуске
    assert res.metadata.llm_calls >= 2
    assert res.metadata.total_tokens > 0
    steps = [s["step"] for s in res.trace.steps]
    assert "ingest" in steps and "extraction" in steps and "synthesis" in steps


if __name__ == "__main__":
    test_schema_always_complete()
    test_no_fabrication_on_empty()
    test_coerce_drops_unknown_and_fixes_types()
    test_pipeline_on_sample_dir()
    print("all tests passed")
