# Implementation Plan: CLI Tool & SDK

**Branch**: `002-cli-tool` | **Date**: 2026-03-02
**Input**: Feature specification from `/specs/002-cli-tool/spec.md`

## Summary

Pivot PromptShield from a SaaS backend (001-core-api) to a self-hosted developer tool. The tool will provide three interfaces: a Python library, a CLI command, and a local HTTP server mode. All SaaS-specific infrastructure (billing, auth, DB persistence) will be removed. The core detection pipeline (Regex -> NumPy embedding similarity -> LLM) runs locally with optional sentence-transformers support.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `pydantic`, `numpy`, `httpx`, `fastapi`, `uvicorn`, `typer`, `pyyaml`. Optional: `sentence-transformers` for local embeddings.
**Storage**: Local JSON attack patterns (`src/data/attack_patterns.json`), ephemeral NumPy index in memory
**Testing**: `pytest`
**Target Platform**: Linux, macOS, Windows (local execution)
**Project Type**: Library / CLI / Local Server
**Performance Goals**: < 500ms regex/embedding, < 2s LLM fallback
**Constraints**: Zero infrastructure (no cloud deployment required), standalone execution.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
✅ Passes Principle I (Three Interfaces - One Shared Core)
✅ Passes Principle II (Tiered Local Detection Pipeline)
✅ Passes Principle III (Zero Infrastructure & Local Execution)
✅ Passes Principle IV (Frictionless Local Integration)
✅ Passes Principle V (Dogfooding)

## Project Structure

### Documentation

```text
specs/002-cli-tool/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
src/
├── __init__.py              # exposes Shield class as public API
├── shield.py                # core Shield class — main entry point
├── config.py                # config loading (file + env + flags)
├── detection/
│   ├── pipeline.py          # tiered orchestration
│   ├── regex_engine.py      # pattern matching
│   ├── vector_engine.py     # NumPy cosine similarity + optional local embeddings
│   └── llm_engine.py        # LLM fallback via httpx
├── data/
│   └── attack_patterns.json # bundled attack vector dataset
├── cli/
│   └── main.py              # Typer CLI entry point
└── server/
    └── app.py               # FastAPI local server mode

tests/
├── unit/
└── integration/

pyproject.toml               # package config, entry points, deps
README.md
.promptshield.yaml.example
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Restructuring | Pivot from SaaS to CLI | Old structure contained deep SaaS assumptions. |