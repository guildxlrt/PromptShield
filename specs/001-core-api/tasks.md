# ⚠️ SUPERSEDED – ARCHITECTURAL PIVOT (2025)

**This specification describes the original cloud-hosted SaaS plan.**  
**It was abandoned in favor of a local-first Python library (see spec-002).**  
**Most functional requirements listed here were never implemented.**

---

# Task Plan: PromptShield API Core Endpoints (HISTORICAL)

**Feature Branch**: `001-core-api`  
**Created**: 2026-03-01  
**Status**: SUPERSEDED (see spec-002 for current implementation)

**ARCHITECTURAL NOTE**: This task plan originally outlined a multi-tenant cloud API with Stripe billing, SQLite user accounts, and HMAC-hashed email storage. The project pivoted in early 2025 to a self-hosted, single-machine Python library. Most phases below were not completed as planned; see spec-002 for the actual implementation.

## Phase 1: Setup (Partially Completed)
- [x] T001 Initialize Python project with `venv`, `requirements.txt`, and FastAPI setup in `src/api/main.py` — **REFRAMED**: Completed as `promptshield/` directory instead of `src/api/`
- [x] T002 [P] Configure Pydantic settings in `src/core/config.py` for environment variables — **REFRAMED**: Completed as `promptshield/config.py` with YAML + env var support
- [x] T003 [P] Set up basic pytest configuration — **PARTIAL**: `pytest.ini` exists; full test suite was deprioritized

## Phase 2: Foundational (Blocking) (Partially Completed)
- [x] T004 Create Pydantic schemas (`ScanRequest`, `ScanResponse`) — **REFRAMED**: Completed in `promptshield/schemas/scan.py`; `api_key` field removed
- [ ] T005 [P] Implement API Key validation dependency — **ABANDONED**: No authentication in local-first architecture
- [ ] T006 [P] Implement in-memory token-bucket rate limiter — **ABANDONED**: No rate limiting needed for single-machine usage

## Phase 3: User Story 1 - Scan API Integration (P1) (Completed with Modifications)
**Goal**: Core scan endpoint with tiered detection.
- [x] T007 [US1] Implement Regex/Pattern matching engine — **COMPLETED**: `promptshield/detection/regex_engine.py`
- [x] T008 [P] [US1] Implement vector engine — **REFRAMED**: Replaced ChromaDB (spec-003) with NumPy brute-force; located in `promptshield/detection/vector_engine.py`
- [x] T009 [P] [US1] Implement OpenRouter LLM fallback engine — **COMPLETED**: `promptshield/detection/llm_engine.py`
- [x] T010 [US1] Orchestrate the detection engines — **COMPLETED**: `promptshield/detection/pipeline.py`
- [x] T011 [US1] Create the POST `/v1/scan` route — **REFRAMED**: Implemented as `promptshield/server/app.py` (FastAPI) and Python library (`Shield.scan()`)
- [x] T012 [P] [US1] Write unit tests — **PARTIAL**: Limited test coverage
- [x] T013 [US1] Write integration tests — **PARTIAL**: Limited test coverage

## Phase 4: User Story 2 - API Access Control and Rate Limiting (P2) (Abandoned)
**Goal**: Enforce rate limits based on free/paid tiers.
- [ ] T014 [US2] Update API dependencies for rate limiting — **ABANDONED**: No authentication or rate limiting in local-first architecture
- [ ] T015 [US2] Write unit tests for rate limiting — **ABANDONED**: Not applicable
- [ ] T016 [US2] Write integration tests for rate limits — **ABANDONED**: Not applicable

## Phase 5: Polish & Cross-Cutting (Partially Completed)
- [ ] T017 Implement request/response logging — **DEFERRED**: Audit logging not implemented; caller manages logging via `scan_id`
- [x] T018 Refine error handling — **COMPLETED**: Basic error handling in `promptshield/server/app.py`
- [x] T019 Implement API dogfooding — **COMPLETED**: Server mode uses the same detection pipeline for incoming requests
- [x] T020 Write performance tests — **PARTIAL**: Benchmark module exists (specs/005-benchmarks); latency SLOs are aspirational
- [x] T021 Finalize documentation — **COMPLETED**: README.md and CLI help text; `quickstart.md` was rewritten

## Phase 6: Billing (US3) (Abandoned)
**Goal**: Minimal Stripe integration for tier upgrades.
- [ ] T022 [US3] Create billing endpoints — **ABANDONED**: No billing in local-first architecture
- [ ] T023 [US3] Add Stripe environment variables — **ABANDONED**: Not applicable
- [ ] T024 [US3] Register `/billing` router — **ABANDONED**: Not applicable
- [ ] T025 [P] [US3] Write integration tests for billing — **ABANDONED**: Not applicable

## Phase 7: Auth & Registration (US4) (Abandoned)
**Goal**: Self-serve API key generation.
- [ ] T026 [US4] Add database dependencies — **ABANDONED**: No user database in local-first architecture
- [ ] T027 [US4] Create SQLite database module — **ABANDONED**: Not applicable
- [ ] T028 [US4] Create `/auth/register` endpoint — **ABANDONED**: Not applicable
- [ ] T029 [US4] Update security module for database calls — **ABANDONED**: Not applicable
- [ ] T030 [US4] Update routes for usage tracking — **ABANDONED**: Not applicable
- [ ] T031 [US4] Write auth integration tests — **ABANDONED**: Not applicable

## Dependencies & Strategy (HISTORICAL)

The original plan assumed sequential phases with clear dependencies:
- Phase 1 & 2 → Phase 3 (MVP delivery)
- Phase 4 (access control) → Phase 5 (polish) → Phase 6–7 (billing & auth)

**In practice** (2025 pivot):
- Phases 1–3 were reframed and completed with a local-first architecture (no auth, no billing)
- Phases 4–7 were abandoned entirely
- A new spec-002 plan superseded this one, focused on CLI + library interfaces instead of cloud API

See [spec-002 tasks.md](../002-cli-tool/tasks.md) for the actual, implemented task breakdown.
