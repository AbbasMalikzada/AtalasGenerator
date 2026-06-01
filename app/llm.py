"""Обёртки над LLM с учётом числа вызовов и токенов.

AnthropicLLM — боевой клиент Anthropic (требует пакет `anthropic` и ANTHROPIC_API_KEY).
GeminiLLM — боевой клиент Gemini via HTTP REST API (требует GEMINI_API_KEY или GOOGLE_API_KEY).
OpenRouterLLM — боевой клиент OpenRouter (требует OPENROUTER_API_KEY).
FakeLLM — детерминированная заглушка для offline-тестов и CI: реальная сеть не
нужна, что позволяет проверить весь pipeline без ключа.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import List

# Модель по умолчанию. Переопределяется переменной окружения DOCGEN_MODEL или
# полем `model` в запросе.
DEFAULT_MODEL = os.getenv("DOCGEN_MODEL", "claude-sonnet-4-20250514")


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMBase:
    model: str = DEFAULT_MODEL
    calls: int = 0
    total_tokens: int = 0
    _last_usage: Usage = field(default_factory=Usage)

    def complete(self, system: str, user: str, max_tokens: int = 4096) -> str:
        raise NotImplementedError


class AnthropicLLM(LLMBase):
    def __init__(self, model: str | None = None, api_key: str | None = None):
        super().__init__(model=model or DEFAULT_MODEL)
        from anthropic import Anthropic  # импорт здесь, чтобы offline не падал

        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def complete(self, system: str, user: str, max_tokens: int = 4096) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0,  # детерминизм -> воспроизводимость
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        self.calls += 1
        u = resp.usage
        self._last_usage = Usage(u.input_tokens, u.output_tokens)
        self.total_tokens += u.input_tokens + u.output_tokens
        return "".join(
            b.text for b in resp.content if getattr(b, "type", None) == "text"
        )


class GeminiLLM(LLMBase):
    """Боевой клиент Gemini через официальный HTTP REST API."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        model_name = model or os.getenv("DOCGEN_MODEL") or "gemini-2.5-flash"
        super().__init__(model=model_name)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def complete(self, system: str, user: str, max_tokens: int = 4096) -> str:
        import requests

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": user}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system}]
            },
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
                "maxOutputTokens": max_tokens
            }
        }
        
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        res_json = resp.json()
        
        try:
            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Failed to parse Gemini API response: {e}. Full response: {res_json}")
            
        usage = res_json.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", len(user) // 4)
        output_tokens = usage.get("candidatesTokenCount", len(text) // 4)
        
        self.calls += 1
        self._last_usage = Usage(input_tokens, output_tokens)
        self.total_tokens += input_tokens + output_tokens
        return text


class OpenRouterLLM(LLMBase):
    """Боевой клиент OpenRouter через HTTP API."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        model_name = model or os.getenv("DOCGEN_MODEL") or "anthropic/claude-3.5-sonnet:beta"
        super().__init__(model=model_name)
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

    def complete(self, system: str, user: str, max_tokens: int = 4096) -> str:
        import requests

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "Project Documentation Generator",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        res_json = resp.json()
        
        try:
            text = res_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Failed to parse OpenRouter response: {e}. Response: {res_json}")
            
        usage = res_json.get("usage", {})
        input_tokens = usage.get("prompt_tokens", len(user) // 4)
        output_tokens = usage.get("completion_tokens", len(text) // 4)
        
        self.calls += 1
        self._last_usage = Usage(input_tokens, output_tokens)
        self.total_tokens += input_tokens + output_tokens
        return text


class FakeLLM(LLMBase):
    """Заглушка без сети. Грубо «извлекает» факты регулярками из промпта."""

    def __init__(self, model: str | None = None):
        super().__init__(model=(model or "fake-offline-model"))

    def complete(self, system: str, user: str, max_tokens: int = 4096) -> str:
        self.calls += 1
        # грубая оценка токенов: ~4 символа на токен
        self._last_usage = Usage(len(user) // 4, 200)
        self.total_tokens += self._last_usage.input_tokens + self._last_usage.output_tokens

        if "Извлеки атомарные факты" in user:
            return json.dumps(self._fake_extract(user), ensure_ascii=False)
        return json.dumps(self._fake_synthesize(user), ensure_ascii=False)

    # --- очень простая эвристика, только для демонстрации/тестов ---
    def _fake_extract(self, user: str) -> dict:
        facts = []
        for fname, body in re.findall(r'<file name="([^"]+)"[^>]*>\n(.*?)\n</file>', user, re.DOTALL):
            for line in body.splitlines():
                s = line.strip(" -*\t")
                if not s:
                    continue
                low = s.lower()
                cat = "requirements"
                if any(w in low for w in ["цель", "goal"]):
                    cat = "goals"
                elif any(w in low for w in ["риск", "risk"]):
                    cat = "risks"
                elif any(w in low for w in ["бюджет", "budget", "$", "руб"]):
                    cat = "budget"
                elif any(w in low for w in ["срок", "timeline", "недел", "месяц", "week"]):
                    cat = "timeline"
                elif any(w in low for w in ["команда", "team", "разработчик", "инженер"]):
                    cat = "team"
                elif any(w in low for w in ["архитектур", "architecture", "сервис", "api"]):
                    cat = "architecture"
                facts.append({"category": cat, "statement": s[:200], "source": fname})
        return {"facts": facts[:50], "conflicts": []}

    def _fake_synthesize(self, user: str) -> dict:
        from .jsonutil import extract_json  # первый сбалансированный {...} = блок фактов

        facts = []
        try:
            data = extract_json(user)
            facts = data.get("facts", []) if isinstance(data, dict) else []
        except Exception:
            facts = []
        doc = {
            "project_overview": "",
            "goals": [],
            "requirements": [],
            "technical_solution": "",
            "architecture": "",
            "team": [],
            "timeline": "",
            "budget": "",
            "risks": [],
        }
        for f in facts:
            cat = f.get("category")
            st = f.get("statement", "")
            if cat in ("goals", "requirements", "team", "risks"):
                doc[cat].append(st)
            elif cat in doc and not doc[cat]:
                doc[cat] = st
        return {"document": doc, "resolution_notes": []}


def make_llm(
    model: str | None = None,
    openrouter_key: str | None = None,
    anthropic_key: str | None = None,
    gemini_key: str | None = None
) -> LLMBase:
    if os.getenv("DOCGEN_FAKE") == "1":
        return FakeLLM(model)
        
    selected_model = model or os.getenv("DOCGEN_MODEL", "")
    
    # Ключи API (переданные аргументы имеют приоритет над переменными окружения)
    openrouter_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")
    anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY")
    gemini_key = gemini_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    # 1. Если задан ключ OpenRouter
    if openrouter_key:
        model_name = selected_model if "/" in selected_model else "anthropic/claude-3.5-sonnet:beta"
        return OpenRouterLLM(model_name, openrouter_key)
        
    # 2. Если явно выбрана модель gemini
    if selected_model.startswith("gemini") or "flash" in selected_model or "pro" in selected_model:
        if gemini_key:
            return GeminiLLM(selected_model, gemini_key)
            
    # 3. Если есть ключ Anthropic
    if anthropic_key:
        try:
            return AnthropicLLM(selected_model, anthropic_key)
        except Exception:
            pass
            
    # 4. Если есть ключ Gemini
    if gemini_key:
        try:
            return GeminiLLM(selected_model or "gemini-2.5-flash", gemini_key)
        except Exception:
            pass
            
    return FakeLLM(model)
