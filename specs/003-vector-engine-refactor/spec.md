# Feature Specification: Replace ChromaDB with NumPy

**Feature Branch**: `003-vector-engine-refactor`
**Created**: 2026-03-06
**Status**: Draft
**Input**: Replace ChromaDB vector store with NumPy brute-force implementation to reduce dependency footprint from ~400MB to under 100MB.

## User Scenarios & Testing

### User Story 1 - Lightweight Vector Search
The system needs to perform vector search without the heavy ChromaDB dependency.
**Acceptance Scenarios**:
1. **Given** a prompt, **When** it is scanned, **Then** it uses NumPy for vector similarity and returns the correct verdict.
2. **Given** the system is initializing, **When** the index is built, **Then** it reads from `data/attack_patterns.json` and builds a normalized NumPy array.
3. **Given** an error from the embedding API, **When** an embed request fails, **Then** it raises an exception and does not fail-open.

## Requirements
- **FR-001**: Remove all ChromaDB dependencies and usage.
- **FR-002**: Implement `_embed`, `_build_index`, `_get_index`, and `scan_vector` in `vector_engine.py` using NumPy.
- **FR-003**: Do not catch broad exceptions and return "pass". Let exceptions propagate.
