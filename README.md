# Project Documentation Generator (Task 1)

The system generates structured project documentation from a set of raw materials
(`.txt`, `.md`, `.json`, `.py`, `.java`) using an LLM.
Entry point: HTTP API `POST /generate_document`. The response strictly matches
the required format: `{ document, metadata, trace }`.

## Core Idea: Two-Stage Pipeline

The key technique against hallucinations is **separating "extraction" from "synthesis"**:

1. **Extraction.** The LLM reads all files (with delimiters and type labels) and
   returns *only explicit facts*, each linked to its source file.
   Mutually exclusive statements are flagged as `conflicts` — the model does not
   resolve them on its own.
2. **Synthesis.** The LLM assembles the document **strictly from the fact list**. Fields
   with no supporting facts are left empty (`""` / `[]`) — no invention allowed.
   Conflicts are resolved with a justification written to `resolution_notes` (included in trace).

On top of the model response, **strict schema normalization** (`coerce_document`) runs:
unknown keys are dropped, types are coerced, duplicates removed. Even if the model
drifts from the format, the output is always a valid structure.

```
files → ingest (normalize, truncate) → extraction (facts + conflicts) → synthesis (document) → schema validation
```

## Evaluation Criteria

| Criterion | How it is met |
|---|---|
| Accuracy & completeness (40%) | Facts linked to source; synthesis strictly from facts; batching preserves all files |
| No hallucinations (20%) | `temperature=0`; separated extract/synthesize stages; prompts forbid invention; empty fields instead of guesses; schema validation |
| Token efficiency (10%) | Large files truncated; single extraction call; compact facts passed to synthesis instead of raw text |
| LLM call count (10%) | Typically **2 calls** (1 extraction + 1 synthesis); batching only for very large inputs |
| Execution time (10%) | Tracked per step in `trace` and totalled in `metadata.duration_ms` |
| Structure & format (10%) | Pydantic response schema + forced normalization |

Reproducibility: fixed model, `temperature=0`, deterministic prompts; full `trace` per step.

## Setup & Running (Windows)

Convenience `.bat` files are provided in the root directory:
- **Start server**: Double-click `start_server.bat` (launches FastAPI on `http://127.0.0.1:8000`).
- **Offline CLI simulation**: Double-click `run_cli_simulation.bat` (runs CLI over `sample_data` with no network).
- **Live CLI**: `run_cli_live.bat <path_to_directory>` (runs live generation over a directory).

---

## Setup & Running (Linux / Terminal)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# For Anthropic:
export ANTHROPIC_API_KEY=sk-...
export DOCGEN_MODEL=claude-sonnet-4-20250514

# OR for Google Gemini:
export GEMINI_API_KEY=AIzaSy...
export DOCGEN_MODEL=gemini-2.5-flash

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Example request:

```bash
curl -X POST http://localhost:8000/generate_document \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {"name": "notes.md", "content": "Goal: accelerate spec writing. Timeline: 8 weeks."},
      {"name": "budget.json", "content": "{\"total\": 150000, \"currency\": \"USD\"}"}
    ]
  }'
```

## Offline Mode (no network, no API key)

For development/CI there is a deterministic stub `FakeLLM` (heuristic parsing,
no network calls). Enable it with `DOCGEN_FAKE=1`:

```bash
# run over sample data
DOCGEN_FAKE=1 python run_cli.py sample_data

# run tests
python tests/test_pipeline.py
```

> The stub only verifies the "wiring" (fact routing, schema, trace, call/token counting).
> Its extraction quality is primitive — a real model produces meaningful output.

## Project Structure

```
app/
  main.py       — FastAPI, POST /generate_document
  pipeline.py   — orchestration: ingest → extraction → synthesis, trace, metadata
  prompts.py    — prompts for both stages (strict, JSON-only)
  llm.py        — LLM clients (Anthropic, OpenAI, Gemini, OpenRouter) + FakeLLM
  ingest.py     — file ingestion/normalization, batching
  jsonutil.py   — robust JSON parsing from model output
  schema.py     — strict response schema and document normalization
sample_data/    — example files (with duplicates and one timeline conflict: 8 vs 10 weeks)
tests/          — offline tests
run_cli.py      — run pipeline over a directory
```

## Possible Improvements

- Fact cache keyed by file hash (saves tokens on repeated runs).
- Token counting via `client.messages.count_tokens` before calling (budget management).
- Support for more formats (`.csv`, `.yaml`) and multipart file upload.
- Return source attribution alongside each document item (full traceability to file).
