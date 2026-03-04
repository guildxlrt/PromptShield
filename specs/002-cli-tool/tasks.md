# Implementation Tasks: CLI Tool & SDK

## Dependencies

- Phase 1 (Setup) must be completed before anything else.
- Phase 2 (Foundational) provides core components for all user stories.
- Phases 3, 4, 5 (User Stories) can theoretically run in parallel once Phase 2 is done, but are ordered by priority.
- Phase 6 (Polish) is final.

## Phase 1: Setup

- [x] T001 Rename `src` directory to `promptshield` and remove `api/auth.py`, `api/billing.py`, `db/`, `core/security.py`, and related tests.
- [x] T002 Update `requirements.txt` / `pyproject.toml` to include CLI tools (`typer` or `click`, `pyyaml`) and remove SaaS tools if not needed.
- [x] T003 Ensure `promptshield/data/attack_patterns.json` exists for ChromaDB reseeding.

## Phase 2: Foundational

- [x] T004 Implement `promptshield/config.py` to parse `.promptshield.yaml`, env vars, and handle defaults.
- [x] T005 Refactor `promptshield/detection/` (regex_engine.py, vector_engine.py, llm_engine.py, pipeline.py) to use the local config instead of the old API context, and ensure `pipeline_layer` is added to results.
- [x] T006 Update `promptshield/schemas/scan.py` to reflect the new unified scan response contract.

## Phase 3: User Story 1 (Python Library) [US1]

- [x] T007 [US1] Implement `promptshield/shield.py` with a `Shield` class that acts as the primary API for programmatic usage.
- [x] T008 [US1] Expose `Shield` class in `promptshield/__init__.py`.
- [x] T009 [US1] Create unit tests in `tests/unit/test_shield.py` to verify programmatic scanning and config parsing.

## Phase 4: User Story 2 (CLI Command) [US2]

- [x] T010 [US2] Implement `promptshield/cli/main.py` using `typer` or `click` to handle `scan`, `init`, and `server` commands.
- [x] T011 [US2] Implement `--pretty` flag formatting in CLI output.
- [x] T012 [US2] Register CLI entry point in `pyproject.toml` / `setup.py` so that `promptshield` command is available.
- [x] T013 [US2] Create integration tests in `tests/integration/test_cli.py` to test CLI exit codes and output formats.

## Phase 5: User Story 3 (Local Server Mode) [US3]

- [x] T014 [US3] Implement `promptshield/server/app.py` with FastAPI to expose `POST /v1/scan`.
- [x] T015 [US3] Ensure dogfooding is active for the server mode (using the local detection pipeline).
- [x] T016 [US3] Connect `promptshield server` CLI command to launch the `uvicorn` server locally.
- [x] T017 [US3] Create integration tests in `tests/integration/test_server.py`.

## Phase 6: Polish & Cleanup

- [x] T018 Create `README.md` and `.promptshield.yaml.example` demonstrating how to use the library, CLI, and server.
- [x] T019 Final run of `pytest` and code linting (`ruff check .`) to ensure correctness.