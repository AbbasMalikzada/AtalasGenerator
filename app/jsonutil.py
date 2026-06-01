"""Утилиты для устойчивого разбора JSON, который вернула LLM."""
from __future__ import annotations

import json
import re
from typing import Any


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> Any:
    """Достаёт первый валидный JSON-объект/массив из ответа модели.

    Терпимо относится к ```json``` ограждениям и предисловиям. Если ничего
    распарсить не удалось — возбуждает ValueError, чтобы вызывающий код мог
    зафиксировать это в trace, а не молча проглотить.
    """
    if text is None:
        raise ValueError("empty LLM response")

    candidates = []

    # 1) содержимое code-fence
    m = _FENCE_RE.search(text)
    if m:
        candidates.append(m.group(1).strip())

    # 2) весь текст как есть
    candidates.append(text.strip())

    # 3) первый сбалансированный {...} или [...]
    span = _first_balanced(text)
    if span:
        candidates.append(span)

    for c in candidates:
        try:
            return json.loads(c)
        except (json.JSONDecodeError, ValueError):
            continue

    raise ValueError("no valid JSON found in LLM response")


def _first_balanced(text: str) -> str | None:
    start = None
    opener = None
    closer = None
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if start is None:
            if ch in "{[":
                start = i
                opener = ch
                closer = "}" if ch == "{" else "]"
                depth = 1
            continue
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None
