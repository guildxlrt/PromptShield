# Implementation Plan: PromptShield API Core Endpoints

**Branch**: `001-core-api` | **Date**: 2026-03-01 | **Spec**: [specs/001-core-api/spec.md]
**Input**: Feature specification from `specs/001-core-api/spec.md`

## Summary

PromptShield is a security checkpoint for LLM applications. Developers call the `POST /v1/scan` endpoint before sending user prompts to any LLM. It detects malicious inputs (prompt injection, jailbreaks) via a tiered detection pipeline (regex -> embedding similarity -> LLM fallback) and returns a structured verdict. It enforces free/paid rate limits using API keys.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, ChromaDB (local embedded), httpx (for OpenRouter), pydantic
**Storage**: ChromaDB (local vector storage for known attack patterns)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (Render or Railway free tier)
**Project Type**: Web Service (REST API)
**Performance Goals**: < 500ms for regex/embedding path, < 2s for LLM fallback path
**Constraints**: < $50 monthly budget (hosting + OpenRouter AI costs)
**Scale/Scope**: Free tier (1,000 scans/mo, 10 req/min), Paid tier (50,000 scans/mo, 100 req/min)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] I. API-First Security: Focus strictly on `POST /v1/scan` endpoint; no prompt forwarding.
- [x] II. Tiered Detection Pipeline: Implemented regex, ChromaDB embedding, and OpenRouter fallback.
- [x] III. Budget & Infrastructure Pragmatism: Python, FastAPI, local ChromaDB, minimal deps, targeted for Render/Railway.
- [x] IV. Lean Integration: Frictionless clear schemas, fast execution goals identified.
- [x] V. Dogfooding: Plan to route PromptShield API requests through the pipeline itself.

## Project Structure

### Documentation (this feature)

```text
specs/001-core-api/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated separately)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── main.py          # FastAPI application & routing
│   ├── dependencies.py  # Auth & Rate limiting deps
│   └── routes.py        # /v1/scan endpoint
├── core/
│   ├── config.py        # Settings (pydantic BaseSettings)
│   └── security.py      # Rate limiting logic & API key validation
├── detection/
│   ├── pipeline.py      # Tiered execution logic
│   ├── regex_engine.py  # Pattern matching
│   ├── vector_engine.py # ChromaDB similarity
│   └── llm_engine.py    # OpenRouter fallback integration
└── schemas/
    └── scan.py          # Pydantic models for Req/Res

tests/
├── integration/         # API endpoint tests
└── unit/                # Engine and pipeline tests
```

**Structure Decision**: Selected a modular single-project structure tailored for FastAPI, splitting API routing, core security/config, domain logic (detection engines), and data schemas.
