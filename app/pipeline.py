"""Оркестрация двухэтапного pipeline: extraction -> synthesis.

Принципы под критерии оценки:
- Достоверность/полнота: факты привязаны к источникам, синтез строго по фактам.
- Без галлюцинаций: t=0, два разделённых этапа, валидация схемы, пустые поля
  вместо домыслов.
- Эффективность токенов: усечение больших файлов, батчинг по бюджету.
- Мало вызовов LLM: типичный случай — 2 вызова (1 extraction + 1 synthesis);
  для крупных входов extraction идёт батчами, synthesis всегда один.
- Время: фиксируется поэтапно в trace и суммарно в metadata.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Dict, List

from .ingest import NormalizedFile, normalize_files
from .jsonutil import extract_json
from .llm import LLMBase, make_llm
from .prompts import (
    EXTRACTION_SYSTEM,
    SYNTHESIS_SYSTEM,
    build_extraction_user,
    build_synthesis_user,
)
from .schema import Document, GenerateResponse, Metadata, Trace, coerce_document

# Бюджет символов на один extraction-вызов (батчинг крупных входов).
EXTRACTION_CHAR_BUDGET = 45_000
CACHE_FILE = ".fact_cache.json"
CONFIG_JSON = "config.json"


def load_app_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_JSON):
        try:
            with open(CONFIG_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_app_config(cfg: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_JSON, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _now_ms() -> float:
    return time.perf_counter() * 1000.0


def _md5(content: str) -> str:
    return hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()


def _load_cache() -> Dict[str, Any]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _batch(files: List[NormalizedFile], budget: int) -> List[List[NormalizedFile]]:
    batches: List[List[NormalizedFile]] = []
    cur: List[NormalizedFile] = []
    size = 0
    for f in files:
        flen = len(f.content) + len(f.name) + 40
        if cur and size + flen > budget:
            batches.append(cur)
            cur, size = [], 0
        cur.append(f)
        size += flen
    if cur:
        batches.append(cur)
    return batches or [[]]


def _extract(llm: LLMBase, files: List[NormalizedFile], trace_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    cache = _load_cache()
    all_facts: List[Dict[str, Any]] = []
    all_conflicts: List[Dict[str, Any]] = []

    hits: List[str] = []
    misses: List[NormalizedFile] = []

    for f in files:
        h = _md5(f.content)
        if f.name in cache and cache[f.name].get("hash") == h:
            hits.append(f.name)
            all_facts.extend(cache[f.name].get("facts", []))
            all_conflicts.extend(cache[f.name].get("conflicts", []))
        else:
            misses.append(f)

    # Логируем результаты проверки кэша в trace
    trace_steps.append({
        "step": "cache_lookup",
        "files_total": len(files),
        "cache_hits": hits,
        "cache_misses": [m.name for m in misses],
        "cached_facts_loaded": len(all_facts)
    })

    if misses:
        batches = _batch(misses, EXTRACTION_CHAR_BUDGET)
        for i, batch in enumerate(batches):
            t0 = _now_ms()
            user = build_extraction_user(batch)
            raw = llm.complete(EXTRACTION_SYSTEM, user, max_tokens=4096)
            step: Dict[str, Any] = {
                "step": "extraction",
                "batch": i + 1,
                "batches_total": len(batches),
                "files": [f.name for f in batch],
                "input_tokens": llm._last_usage.input_tokens,
                "output_tokens": llm._last_usage.output_tokens,
                "duration_ms": round(_now_ms() - t0, 1),
            }
            try:
                data = extract_json(raw)
                facts = data.get("facts", []) if isinstance(data, dict) else []
                conflicts = data.get("conflicts", []) if isinstance(data, dict) else []
                
                new_facts = [f for f in facts if isinstance(f, dict)]
                new_conflicts = [c for c in conflicts if isinstance(c, dict)]
                
                all_facts.extend(new_facts)
                all_conflicts.extend(new_conflicts)
                
                step["facts_extracted"] = len(new_facts)
                step["conflicts_found"] = len(new_conflicts)

                # Сохраняем извлечённые факты по каждому файлу в кэш
                for f in batch:
                    file_facts = [fact for fact in new_facts if fact.get("source") == f.name]
                    file_conflicts = [c for c in new_conflicts if f.name in c.get("sources", [])]
                    
                    cache[f.name] = {
                        "hash": _md5(f.content),
                        "facts": file_facts,
                        "conflicts": file_conflicts
                    }
            except ValueError as e:
                step["error"] = f"extraction parse failed: {e}"
            trace_steps.append(step)

        # Сохраняем обновлённый кэш на диск
        _save_cache(cache)

    return {"facts": all_facts, "conflicts": all_conflicts}


def _synthesize(llm: LLMBase, facts: Dict[str, Any], trace_steps: List[Dict[str, Any]]) -> Document:
    t0 = _now_ms()
    facts_json = json.dumps(facts, ensure_ascii=False)
    user = build_synthesis_user(facts_json)
    raw = llm.complete(SYNTHESIS_SYSTEM, user, max_tokens=4096)
    step: Dict[str, Any] = {
        "step": "synthesis",
        "facts_in": len(facts.get("facts", [])),
        "conflicts_in": len(facts.get("conflicts", [])),
        "input_tokens": llm._last_usage.input_tokens,
        "output_tokens": llm._last_usage.output_tokens,
        "duration_ms": round(_now_ms() - t0, 1),
    }
    doc_obj: Dict[str, Any] = {}
    try:
        data = extract_json(raw)
        if isinstance(data, dict):
            doc_obj = data.get("document", data)
            notes = data.get("resolution_notes", [])
            if notes:
                step["resolution_notes"] = notes
    except ValueError as e:
        step["error"] = f"synthesis parse failed: {e}"
    trace_steps.append(step)
    return coerce_document(doc_obj)


def generate_document(
    files: List[dict],
    model: str | None = None,
    openrouter_key: str | None = None,
    anthropic_key: str | None = None,
    gemini_key: str | None = None
) -> GenerateResponse:
    start = _now_ms()
    trace_steps: List[Dict[str, Any]] = []

    # Загружаем настройки по умолчанию с диска в качестве fallbacks
    cfg = load_app_config()
    model = model or cfg.get("default_model")
    openrouter_key = openrouter_key or cfg.get("openrouter_api_key")
    anthropic_key = anthropic_key or cfg.get("anthropic_api_key")
    gemini_key = gemini_key or cfg.get("gemini_api_key")

    llm = make_llm(
        model=model,
        openrouter_key=openrouter_key,
        anthropic_key=anthropic_key,
        gemini_key=gemini_key
    )

    t0 = _now_ms()
    norm = normalize_files(files)
    trace_steps.append(
        {
            "step": "ingest",
            "files": [f.name for f in norm],
            "truncated": [f.name for f in norm if f.truncated],
            "duration_ms": round(_now_ms() - t0, 1),
        }
    )

    if not norm:
        # ничего не выдумываем — возвращаем пустой валидный документ
        return GenerateResponse(
            document=coerce_document({}),
            metadata=Metadata(
                model_name=llm.model,
                llm_calls=0,
                total_tokens=0,
                duration_ms=round(_now_ms() - start),
            ),
            trace=Trace(steps=trace_steps + [{"step": "noop", "reason": "no input files"}]),
        )

    facts = _extract(llm, norm, trace_steps)
    document = _synthesize(llm, facts, trace_steps)

    return GenerateResponse(
        document=document,
        metadata=Metadata(
            model_name=llm.model,
            llm_calls=llm.calls,
            total_tokens=llm.total_tokens,
            duration_ms=round(_now_ms() - start),
        ),
        trace=Trace(steps=trace_steps),
    )
