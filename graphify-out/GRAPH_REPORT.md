# Graph Report - .  (2026-05-31)

## Corpus Check
- Corpus is ~10,275 words - fits in a single context window. You may not need a graph.

## Summary
- 211 nodes · 407 edges · 22 communities (13 shown, 9 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 74 edges (avg confidence: 0.53)
- Token cost: 12,000 input · 2,800 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Core Ingestion and Caching|Core Ingestion and Caching]]
- [[_COMMUNITY_LLM Provider Implementations|LLM Provider Implementations]]
- [[_COMMUNITY_File Normalization Pipeline|File Normalization Pipeline]]
- [[_COMMUNITY_Document Pipeline Execution|Document Pipeline Execution]]
- [[_COMMUNITY_FastAPI HTTP Endpoints|FastAPI HTTP Endpoints]]
- [[_COMMUNITY_Ingest Module|Ingest Module]]
- [[_COMMUNITY_Document Generation and Schema|Document Generation and Schema]]
- [[_COMMUNITY_Configuration Management|Configuration Management]]
- [[_COMMUNITY_JSON Utilities|JSON Utilities]]
- [[_COMMUNITY_Budget Sample Data|Budget Sample Data]]
- [[_COMMUNITY_Project Data Conflicts|Project Data Conflicts]]
- [[_COMMUNITY_Web Dashboard|Web Dashboard]]
- [[_COMMUNITY_Document Schema|Document Schema]]
- [[_COMMUNITY_Generate Request Schema|Generate Request Schema]]
- [[_COMMUNITY_Generate Response Schema|Generate Response Schema]]
- [[_COMMUNITY_Metadata Schema|Metadata Schema]]
- [[_COMMUNITY_Trace Schema|Trace Schema]]
- [[_COMMUNITY_Config Settings Schema|Config Settings Schema]]
- [[_COMMUNITY_Engineering Notes|Engineering Notes]]
- [[_COMMUNITY_README Documentation|README Documentation]]

## God Nodes (most connected - your core abstractions)
1. `generate_document()` - 22 edges
2. `GenerateResponse` - 19 edges
3. `NormalizedFile` - 16 edges
4. `LLMBase` - 16 edges
5. `str` - 14 edges
6. `_extract()` - 13 edges
7. `str` - 12 edges
8. `Any` - 12 edges
9. `Document` - 12 edges
10. `Metadata` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Two-stage Extract+Synthesize Anti-Hallucination Design` --rationale_for--> `_extract()`  [EXTRACTED]
  README.md → app/pipeline.py
- `Two-stage Extract+Synthesize Anti-Hallucination Design` --conceptually_related_to--> `Strict Schema Coercion Anti-Hallucination Layer`  [INFERRED]
  README.md → app/schema.py
- `Two-stage Extract+Synthesize Anti-Hallucination Design` --rationale_for--> `_synthesize()`  [EXTRACTED]
  README.md → app/pipeline.py
- `main()` --calls--> `load_dir()`  [EXTRACTED]
  run_cli.py → app/ingest.py
- `test_pipeline_on_sample_dir()` --calls--> `load_dir()`  [EXTRACTED]
  tests/test_pipeline.py → app/ingest.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Two-Stage LLM Pipeline: Ingest → Extract → Synthesize** — ingest_normalize_files, pipeline_extract, pipeline_synthesize [EXTRACTED 1.00]
- **Anti-Hallucination Mechanism: temperature=0 + two-stage + schema coercion** — rationale_twostage_pipeline, rationale_schema_coercion, schema_coerce_document [INFERRED 0.90]
- **Multi-Provider LLM Strategy: OpenRouter / Anthropic / Gemini / Fake** — llm_make_llm, llm_AnthropicLLM, llm_GeminiLLM, llm_OpenRouterLLM, llm_FakeLLM [EXTRACTED 1.00]

## Communities (22 total, 9 thin omitted)

### Community 0 - "Core Ingestion and Caching"
Cohesion: 0.04
Nodes (43): NormalizedFile dataclass, _extract(), _load_cache(), _save_cache(), EXTRACTION_SYSTEM prompt, FACT_CATEGORIES constant, build_extraction_user(), File-hash-based Fact Cache Design (+35 more)

### Community 1 - "LLM Provider Implementations"
Cohesion: 0.19
Nodes (13): AnthropicLLM, FakeLLM, GeminiLLM, LLMBase, make_llm(), OpenRouterLLM, int, str (+5 more)

### Community 2 - "File Normalization Pipeline"
Cohesion: 0.12
Nodes (22): load_dir(), normalize_files(), normalize_one(), extract_json(), AnthropicLLM, FakeLLM (offline stub), GeminiLLM, LLMBase dataclass (+14 more)

### Community 3 - "Document Pipeline Execution"
Cohesion: 0.27
Nodes (20): _batch(), _extract(), _load_cache(), _md5(), _now_ms(), Any, int, NormalizedFile (+12 more)

### Community 4 - "FastAPI HTTP Endpoints"
Cohesion: 0.21
Nodes (19): generate(), generate_multipart(), get_config(), index(), str, HTTP API.  POST /generate_document   Тело запроса (JSON):     {       "files": [, save_config(), load_app_config() (+11 more)

### Community 5 - "Ingest Module"
Cohesion: 0.23
Nodes (15): _ext(), load_dir(), normalize_files(), normalize_one(), NormalizedFile, str, Приём и нормализация входных файлов.  Поддерживаемые форматы: .txt, .md, .json,, Готовит блок одного файла для промпта с чёткими разделителями. (+7 more)

### Community 6 - "Document Generation and Schema"
Cohesion: 0.21
Nodes (12): generate_document(), coerce_document(), Any, str, Приводит произвольный словарь от LLM к строгой схеме документа.      - неизвестн, main(), CLI: прогнать pipeline по директории с материалами.      python run_cli.py sampl, Тесты pipeline в offline-режиме (FakeLLM, без сети).  Запуск:  DOCGEN_FAKE=1 pyt (+4 more)

### Community 7 - "Configuration Management"
Cohesion: 0.22
Nodes (8): GET /config endpoint, POST /config endpoint, load_app_config(), save_app_config(), anthropic_api_key, default_model, gemini_api_key, openrouter_api_key

### Community 8 - "JSON Utilities"
Cohesion: 0.38
Nodes (6): extract_json(), _first_balanced(), Any, str, Утилиты для устойчивого разбора JSON, который вернула LLM., Достаёт первый валидный JSON-объект/массив из ответа модели.      Терпимо относи

### Community 9 - "Budget Sample Data"
Cohesion: 0.29
Nodes (6): breakdown, infrastructure_cloud, labor_cost, licensing_fees, currency, total_budget

### Community 10 - "Project Data Conflicts"
Cohesion: 0.50
Nodes (5): Budget Conflict: $150k vs $120k, budget.json (Project Atlas budget $150k USD), meeting_notes.md (Meeting May 28 2026), project_brief.md (Project Atlas Brief), Timeline Conflict: 8 weeks vs 10 weeks

## Knowledge Gaps
- **57 isolated node(s):** `hash`, `facts`, `conflicts`, `hash`, `facts` (+52 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_extract()` connect `Core Ingestion and Caching` to `File Normalization Pipeline`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `generate_document()` connect `File Normalization Pipeline` to `Core Ingestion and Caching`, `Configuration Management`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `generate_document()` connect `Document Generation and Schema` to `LLM Provider Implementations`, `Document Pipeline Execution`, `FastAPI HTTP Endpoints`, `Ingest Module`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `GenerateResponse` (e.g. with `str` and `Any`) actually correct?**
  _`GenerateResponse` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `NormalizedFile` (e.g. with `Any` and `int`) actually correct?**
  _`NormalizedFile` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `LLMBase` (e.g. with `Any` and `int`) actually correct?**
  _`LLMBase` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `str` (e.g. with `NormalizedFile` and `LLMBase`) actually correct?**
  _`str` has 6 INFERRED edges - model-reasoned connections that need verification._