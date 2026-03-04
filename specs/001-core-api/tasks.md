# Task Plan: PromptShield API Core Endpoints

**Feature Branch**: `001-core-api`  
**Created**: 2026-03-01

## Phase 1: Setup
- [x] T001 Initialize Python project with `venv`, `requirements.txt`, and FastAPI setup in `src/api/main.py`
- [x] T002 [P] Configure Pydantic settings in `src/core/config.py` for environment variables (`OPENROUTER_API_KEY`, etc.)
- [x] T003 [P] Set up basic pytest configuration in `pytest.ini` and `tests/conftest.py`

## Phase 2: Foundational (Blocking)
- [x] T004 Create Pydantic schemas (`ScanRequest`, `ScanResponse`) in `src/schemas/scan.py`
- [x] T005 [P] Implement API Key validation dependency in `src/core/security.py`
- [x] T006 [P] Implement in-memory token-bucket rate limiter in `src/core/security.py`

## Phase 3: User Story 1 - Scan API Integration (P1)
**Goal**: Core `/v1/scan` endpoint with tiered detection.
- [x] T007 [US1] Implement Regex/Pattern matching engine in `src/detection/regex_engine.py`
- [x] T008 [P] [US1] Implement local ChromaDB vector engine in `src/detection/vector_engine.py` using a custom OpenRouter embedding API call via httpx. No local model. Add EMBEDDING_MODEL to config.
- [x] T009 [P] [US1] Implement OpenRouter LLM fallback engine in `src/detection/llm_engine.py` using `httpx`
- [x] T010 [US1] Orchestrate the detection engines in `src/detection/pipeline.py`
- [x] T011 [US1] Create the POST `/v1/scan` route in `src/api/routes.py` and integrate the pipeline
- [x] T012 [P] [US1] Write unit tests for detection engines in `tests/unit/test_engines.py`
- [x] T013 [US1] Write integration tests for `/v1/scan` in `tests/integration/test_scan_api.py`

## Phase 4: User Story 2 - API Access Control and Rate Limiting (P2)
**Goal**: Enforce rate limits based on free/paid tiers.
- [x] T014 [US2] Update `src/api/dependencies.py` to inject API Key tier checking and rate limit enforcement
- [x] T015 [US2] Write unit tests for rate limiting logic in `tests/unit/test_security.py`
- [x] T016 [US2] Write integration tests for rate limits (429 responses) in `tests/integration/test_rate_limits.py`

## Phase 5: Polish & Cross-Cutting
- [x] T017 Implement request/response logging (Audit Trail) in `src/api/main.py` middleware
- [x] T018 Refine error handling (401, 429, 422, 500) and standard JSON responses in `src/api/main.py`
- [x] T019 Implement API dogfooding logic (ensure API doesn't crash on malicious input / protects itself)
- [x] T020 Write performance tests in `tests/integration/test_performance.py` to verify <500ms and <2s latency constraints
- [x] T021 Finalize `quickstart.md` and inline documentation.

## Phase 6: Billing (US3)
**Goal**: Minimal Stripe integration for tier upgrades.
- [x] T022 [US3] Create `src/api/billing.py` with checkout, webhook, and status routes.
- [x] T023 [US3] Add Stripe environment variables to `src/core/config.py`.
- [x] T024 [US3] Register `/billing` router in `src/api/main.py`.
- [x] T025 [P] [US3] Write integration tests for billing logic in `tests/integration/test_billing.py`.

## Phase 7: Auth & Registration (US4)
**Goal**: Self-serve API key generation.
- [x] T026 [US4] Add `aiosqlite` and `email-validator` to `requirements.txt`.
- [x] T027 [US4] Create `src/db/database.py` with SQLite table schema and seed function.
- [x] T028 [US4] Create `src/api/auth.py` with `/auth/register` endpoint.
- [x] T029 [US4] Update `src/core/security.py` to intercept `COMPANY_DB` dictionary calls and route them synchronously to SQLite.
- [x] T030 [US4] Update `src/api/routes.py` to properly increment `usage_month` and manage reset dates in SQLite.
- [x] T031 [US4] Write integration tests in `tests/integration/test_auth.py` verifying registration and key usability.

## Dependencies & Strategy
- Phase 1 & 2 must be completed before Phase 3.
- Phase 3 delivers the MVP (Core functionality).
- Phase 4 layers access control on top.
- Parallel execution ([P] markers) can be done by different agents/threads.
