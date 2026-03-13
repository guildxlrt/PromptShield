# Implementation Plan: Replace ChromaDB with NumPy

**Branch**: `003-vector-engine-refactor`  
**Status**: ✅ **IMPLEMENTED** — ChromaDB removed, NumPy brute-force in place

## Summary
Replace ChromaDB with a lightweight NumPy brute-force implementation to reduce dependency footprint.

Removes ~400MB of dependencies by replacing ChromaDB ephemeral client
with in-memory cosine similarity over a numpy index built from
attack_patterns.json. Public API unchanged.

## Technical Context
- Language: Python 3.11+
- Dependencies: remove `chromadb`, use `numpy` and `httpx`.
- Target: `promptshield/vector_engine.py`

## Constitution Check
- [x] III. Budget & Infrastructure Pragmatism: Zero Infrastructure & Local Execution, minimal dependencies.

## Implementation Status

✅ **Complete** — The NumPy vector engine is fully implemented in `promptshield/detection/vector_engine.py` and replaces ChromaDB entirely. ChromaDB is not in the codebase, `pyproject.toml`, or `uv.lock`.
