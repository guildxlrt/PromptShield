# Implementation Tasks: Benchmarks Module

**Feature Branch**: `005-benchmarks`

## Dependencies

- Phase 1 (Structural Refactor) must be completed before Phase 2 (Precision & Config).
- Phase 2 must be completed before Phase 3 (Documentation).
- All tasks in Phase 1 are independent of each other except T007, which depends on T001–T006.

## Phase 1: Structural Refactor

- [x] T001 Create `benchmarks/__init__.py` (empty) to mark the directory as a Python package.
- [x] T002 Create `benchmarks/dataset.py` with the `DATASET` list (80 prompts: 40 attack, 10 ambiguous, 30 safe) and the `DEFAULT_CONTEXT` constant.
- [x] T003 Create `benchmarks/runner.py` with the `BenchmarkResult` dataclass, `run_single()`, and `run_benchmark()`. Import `DEFAULT_CONTEXT` from `dataset.py`.
- [x] T004 Create `benchmarks/metrics.py` with `compute_metrics()`. Import `BenchmarkResult` from `runner.py`.
- [x] T005 Create `benchmarks/report.py` with `print_report()`, `save_csv()`, and `save_json()`. Import `BenchmarkResult` from `runner.py`.
- [x] T006 Create `benchmarks/run.py` as the entry point. Import `DATASET` from `dataset.py`, `run_benchmark` from `runner.py`, `compute_metrics` from `metrics.py`, and `print_report`, `save_csv`, `save_json` from `report.py`. Define `async def main()` and call `asyncio.run(main())` under `if __name__ == "__main__"`.
- [x] T007 Delete `benchmarks/benchmark.py` once all five module files are verified to parse without syntax errors.

## Phase 2: Precision & Runtime Config

- [x] T008 Update `benchmarks/runner.py` to use `time.perf_counter_ns()` for nanosecond precision latency measurement. Replace `time.perf_counter()` calls with `time.perf_counter_ns()` and convert elapsed nanoseconds to milliseconds via division by `1_000_000`.
- [x] T009 Add `get_runtime_config()` function to `benchmarks/runner.py`. The function returns a dict with keys `promptshield_llm_model`, `promptshield_embedding_model`, and `confidence_threshold`, reading from environment variables with documented fallback values (`"unknown"` or `"0.60"`).
- [x] T010 Update `benchmarks/run.py` to import `get_runtime_config` from `runner.py`, call it at the start of `main()`, print the result to the console in a "Runtime Configuration" section before any benchmark runs, and inject the captured config into the metrics dict under the key `runtime_config` before calling `save_json()`.
- [x] T011 Verify that `benchmark_summary.json` now includes a `runtime_config` key with all three environment variable snapshots at the top level of the JSON object.

## Phase 3: Documentation

- [x] T012 Update `specs/005-benchmarks/spec.md` to add a fourth user story (Runtime Configuration Capture) documenting why capturing config at startup is important. Add three new FRs (FR-013, FR-014, FR-015) covering nanosecond precision and runtime config snapshot requirements. Add two new SCs (SC-006, SC-007) for console output visibility and timing precision verification. Update FR-004 to mention the `runtime_config` key in the JSON output. Update the "Key Entities" section to document `get_runtime_config()`.
- [x] T013 Update `specs/005-benchmarks/plan.md` to document latency measurement with code example and nanosecond precision rationale. Add a "Runtime Configuration Snapshot" section with a table of captured variables and fallback values. Update the module structure diagram and dependency graph to show `get_runtime_config`. Update the output files table to include `runtime_config` in the JSON summary. Expand the "How to Run" section to list the four console output sections in order.
- [x] T014 Update `specs/005-benchmarks/tasks.md` (this file) to add Phase 2 with eight tasks covering precision and config features.
