# Task Plan: Replace ChromaDB with NumPy

**Feature Branch**: `003-vector-engine-refactor`

## Phase 1: TDD setup
- [x] T001 Write unit tests in `tests/unit/test_vector_engine.py` checking the new constraints (no fail-open, correct normalization, correct blocking).

## Phase 2: Implementation
- [x] T002 Refactor `promptshield/vector_engine.py` to use NumPy and httpx, removing ChromaDB entirely.
