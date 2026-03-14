# Feature Specification: Benchmark Sweep & Multi-Interface Support

**Feature Branch**: `006-benchmark-sweep`
**Created**: 2026-03-08
**Status**: ✅ **Implemented**

## Overview

This feature extends the benchmarks module in two orthogonal directions:

1. **Sweep runner** (`benchmarks/sweep.py`): Tests every `(embedding_model, threshold)` combination in a single invocation and prints a ranked comparison table so maintainers can quickly identify the best configuration balance between recall and false positive rate.

2. **Multi-interface support**: Refactors the benchmark runner so the scan function is injectable, then adds three concrete interface modules (`run_lib`, `run_cli`, `run_http`) that allow the benchmark to exercise all three PromptShield surfaces — the Python library, the CLI subprocess, and the local HTTP server — verifying that all three produce identical results.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Configuration Grid Search (Priority: P1)

A maintainer wants to find the threshold that maximises recall while keeping false positives at zero before shipping a new embedding model, without manually re-running the benchmark for each threshold value.

**Why this priority**: Threshold selection directly affects the security/UX trade-off. Running ten separate benchmark invocations manually is error-prone and slow. A single automated sweep with a ranked output table removes that friction.

**Independent Test**: Run `promptshield-benchmark sweep --thresholds "0.40,0.65,0.45"` and verify that (a) three benchmark runs execute, (b) a ranked table is printed to stdout, and (c) `benchmarks/sweep_results.json` is written with exactly three entries in `results`.

**Acceptance Scenarios**:

1. **Given** default invocation `promptshield-benchmark sweep`, **When** it completes, **Then** exactly 10 benchmark runs execute (2 default models × 5 default thresholds) and a ranked table is printed.
2. **Given** `--models` and `--thresholds` flags, **When** the sweep runs, **Then** exactly `len(models) × len(thresholds)` combinations are tested in model-outer / threshold-inner order.
3. **Given** a sweep completes, **When** `benchmarks/sweep_results.json` is read, **Then** it contains a `sweep_config` object (models, thresholds, llm_model, interface) and a `results` array with one entry per combination, sorted by `composite` descending.
4. **Given** two combinations with the same model but different thresholds, **When** sweep iterates them, **Then** the embedding index is **not** rebuilt between those two combinations (only threshold affects the query step, not the index).
5. **Given** two combinations with different models, **When** sweep transitions to the next model, **Then** the in-memory embedding index is reset before the first scan of that model so the new model's vectors are used.
6. **Given** one combination fails (e.g. API error), **When** the failure is caught, **Then** the sweep continues with the remaining combinations and marks the failed entry with `composite: -2.0` rather than aborting.

---

### User Story 2 — Composite Score Ranking (Priority: P1)

A maintainer wants an objective ranking metric that penalises false positives more heavily than missed attacks, reflecting the real-world cost of blocking legitimate users.

**Why this priority**: Raw recall alone would always rank the highest threshold first. The composite formula `recall − (2 × fpr)` encodes the product requirement that a 1 % FPR increase is twice as costly as a 1 % recall decrease.

**Independent Test**: Given a result with `recall=0.95` and `fpr=0.03`, verify that `composite = 0.95 − (2 × 0.03) = 0.89`.

**Acceptance Scenarios**:

1. **Given** a completed sweep, **When** the ranked table is printed, **Then** rows are ordered by `composite` descending with the highest-composite configuration shown first.
2. **Given** two configurations A (recall=1.0, fpr=0.10) and B (recall=0.95, fpr=0.0), **When** ranked, **Then** B ranks above A because `0.95 − 0 = 0.95 > 1.0 − 0.20 = 0.80`.
3. **Given** a ranked table, **When** printed, **Then** the best configuration is highlighted in a "🏆 Best configuration" callout showing model, threshold, composite score, recall, and fpr.

---

### User Story 3 — Python Library Interface (Priority: P1)

A maintainer benchmarks the Python library interface to establish baseline accuracy and latency figures.

**Why this priority**: The library interface is the primary integration point; it must be the default and must produce numerically consistent results across runs.

**Independent Test**: Run `promptshield-benchmark run --interface lib` and verify it completes without error and the output is identical in structure to the original `promptshield-benchmark run` (no `--interface` flag).

**Acceptance Scenarios**:

1. **Given** `promptshield-benchmark run --interface lib`, **When** it runs, **Then** it produces the same CSV/JSON output format as the unmodified benchmark.
2. **Given** `benchmarks/interfaces/run_lib.py` is imported, **When** `scan_fn` is called with a prompt and context, **Then** it returns a `ScanResponse` with all required fields populated.
3. **Given** the lib interface is used, **When** the benchmark is invoked multiple times with the same config, **Then** verdict and threat_type are deterministic for the regex and embedding layers (LLM layer may vary).

---

### User Story 4 — CLI Interface (Priority: P2)

A maintainer benchmarks the CLI subprocess interface to confirm that the CLI entry point parses arguments correctly and returns the same JSON contract as the library.

**Why this priority**: CI/CD pipelines consume the CLI. A benchmark that exercises the subprocess path catches CLI argument parsing bugs and exit-code regressions that unit tests on the library alone would miss.

**Independent Test**: Run `promptshield-benchmark run --interface cli` and verify that `benchmark_summary.json` contains `"interface": "cli"` and that `recall_attacks` and `false_positive_rate` match the lib interface run within ±2 % (accounting for any timing non-determinism at the LLM layer).

**Acceptance Scenarios**:

1. **Given** `promptshield-benchmark run --interface cli`, **When** it runs, **Then** each scan shells out to `sys.executable -m src.cli.main scan <prompt> [--context <ctx>]` and parses the stdout JSON into a `ScanResponse`.
2. **Given** the `promptshield` executable is not in PATH, **When** the CLI scan_fn is called, **Then** it raises a `RuntimeError` with an actionable install instruction rather than a raw `FileNotFoundError`.
3. **Given** the CLI returns exit code 1 (blocked/flag verdict), **When** the scan_fn parses the output, **Then** it does **not** treat the non-zero exit code as an error — the verdict is read from stdout JSON instead.
4. **Given** the CLI produces non-JSON stdout (e.g. a crash traceback), **When** the scan_fn tries to parse it, **Then** it raises a `RuntimeError` that includes the raw stdout and stderr for diagnosis.

---

### User Story 5 — HTTP Interface (Priority: P2)

A maintainer benchmarks the HTTP server interface to verify that the FastAPI endpoint returns the same results as the library and CLI interfaces.

**Why this priority**: Non-Python integrations (Node.js, Go, Rust) consume PromptShield exclusively via HTTP. The HTTP interface benchmark proves the server deserialization/serialization chain is correct and that latency overhead is within acceptable bounds.

**Independent Test**: With `promptshield server` running in a separate terminal, run `promptshield-benchmark run --interface http` and verify that `benchmark_summary.json` contains `"interface": "http"` and verdict distributions match the lib interface.

**Acceptance Scenarios**:

1. **Given** `promptshield-benchmark run --interface http` with the server running, **When** it runs, **Then** each scan POSTs `{"prompt": ..., "context": ...}` to `http://localhost:8765/v1/scan` and parses the JSON response into a `ScanResponse`.
2. **Given** the server is not running, **When** the HTTP scan_fn is called, **Then** it raises a `RuntimeError` with a human-readable message instructing the user to run `promptshield server`.
3. **Given** the HTTP interface is selected in `run.py`, **When** the module loads, **Then** a `_check_reachable()` ping is sent to `/health` and a warning is printed if the server is not responding — before any benchmark prompts are scanned.
4. **Given** the server is running and the lib interface is also available, **When** both benchmark runs complete, **Then** verdict distributions across all 80 prompts are identical (same model and threshold configuration assumed).

---

### User Story 6 — Injectable scan_fn Refactor (Priority: P1)

A developer extends the benchmark runner with a new scan interface without modifying `runner.py`.

**Why this priority**: The original `runner.py` hardcoded `Shield().scan()`, making it impossible to test alternative interfaces without forking the module. Injectability is required by all other user stories in this feature.

**Independent Test**: Call `run_benchmark(dataset, my_custom_scan_fn)` where `my_custom_scan_fn` is a trivial stub returning a fixed `ScanResponse`, and verify that `BenchmarkResult` objects are produced for every dataset entry without importing `Shield`.

**Acceptance Scenarios**:

1. **Given** the refactored `runner.py`, **When** `run_benchmark(dataset, scan_fn)` is called, **Then** `scan_fn` is called once per dataset entry with `prompt` and `context` keyword arguments.
2. **Given** the refactored `runner.py`, **When** `run_single(scan_fn, prompt, expected)` is called, **Then** it does not import or instantiate `Shield` — all scanning is delegated to `scan_fn`.
3. **Given** `run_benchmark` is called with `quiet=True`, **When** it runs, **Then** per-prompt progress lines are suppressed (useful for sweep sub-runs where outer context is already printed).
4. **Given** `run_benchmark` is called with `quiet=False` (the default), **When** it runs, **Then** per-prompt progress lines are printed with the same format as the original implementation.

---

### Edge Cases

- **Index reset between models**: The global `_index` / `_metadata` in `src.detection.vector_engine` is reset only when the model changes between sweep combinations. Threshold changes with the same model do not trigger a rebuild.
- **HTTP server config immutability**: When using `--interface http`, the server's baked-in model and threshold cannot be overridden per-combination. The sweep still iterates all combinations but produces identical results for each one. A warning is printed before the sweep starts.
- **CLI env var injection**: The CLI interface passes model/threshold overrides as environment variables to the subprocess so the spawned process uses the combination's config, not the parent process's config.
- **Partial sweep failure**: If one combination fails (API error, rate limit, network timeout), the entry is recorded with `composite: -2.0` and `full_metrics.error` set to the exception message. The sweep continues with remaining combinations.
- **sweep_results.json location**: Results are written to `benchmarks/sweep_results.json` (not the project root), keeping sweep artefacts co-located with the benchmark package. The file is gitignored.
- **Identical results across interfaces**: For any given model, threshold, and API key, the three interfaces should produce identical verdicts for regex and embedding layers. The LLM layer may produce slightly different results due to model temperature, but threat_type and verdict should be consistent across interfaces.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `benchmarks/sweep.py` MUST be runnable as `promptshield-benchmark sweep` from the project root with no required arguments.
- **FR-002**: `sweep.py` MUST accept `--models` (comma-separated string), `--thresholds` (comma-separated floats), `--llm` (model identifier string), and `--interface` (`lib` | `cli` | `http`) CLI flags.
- **FR-003**: Default models when `--models` is not specified: `baai/bge-large-en-v1.5`, `google/gemini-embedding-001`.
- **FR-004**: Default thresholds when `--thresholds` is not specified: `0.40`, `0.65`, `0.45`, `0.50`, `0.60`.
- **FR-005**: For each `(model, threshold)` combination, `sweep.py` MUST run the full benchmark pipeline (all 80 dataset prompts) and collect the same metrics that `run.py` produces.
- **FR-006**: The in-memory embedding index MUST be reset (via `src.detection.vector_engine._index = None`) when the model changes between sweep combinations. It MUST NOT be reset between threshold changes of the same model.
- **FR-007**: At the end of the sweep, `sweep.py` MUST print a ranked comparison table sorted by `composite = recall − (2 × fpr)`, descending.
- **FR-008**: The ranked table MUST include the following columns per combination: rank, model, threshold, recall, fpr, flag_rate, layer distribution % (regex / embedding / llm), p95 latency (ms) per layer, composite score.
- **FR-009**: `sweep.py` MUST write full results to `benchmarks/sweep_results.json`. The file MUST contain a `sweep_config` object and a `results` array with one entry per combination, ordered by rank.
- **FR-010**: `benchmarks/sweep_results.json` MUST be added to `.gitignore`.
- **FR-011**: `benchmarks/runner.py` MUST be refactored so that `run_single` and `run_benchmark` accept a `scan_fn: Callable` parameter instead of a `Shield` instance.
- **FR-012**: `run_benchmark` MUST accept a `quiet: bool = False` keyword argument. When `quiet=True`, per-prompt progress lines MUST be suppressed.
- **FR-013**: `benchmarks/interfaces/run_lib.py` MUST expose a module-level `scan_fn` that wraps `Shield().scan()` and uses the configuration loaded from the environment / `.promptshield.yaml`.
- **FR-014**: `benchmarks/interfaces/run_cli.py` MUST expose a module-level `scan_fn` that calls `sys.executable -m src.cli.main scan <prompt> [--context <ctx>]` via `subprocess.run` and parses the JSON stdout into a `ScanResponse`.
- **FR-015**: `benchmarks/interfaces/run_http.py` MUST expose a module-level `scan_fn` that POSTs to `http://localhost:8765/v1/scan` using `httpx` and parses the JSON response into a `ScanResponse`.
- **FR-016**: `run_http.py` MUST also expose a `_check_reachable()` function that pings `/health` and prints a warning if the server is not running.
- **FR-017**: `benchmarks/run.py` MUST accept an `--interface` flag with choices `lib`, `cli`, `http` (default: `lib`). The interface name MUST be stored in `benchmark_summary.json` under the key `"interface"`.
- **FR-018**: If `--interface http` is selected, `run.py` MUST call `_check_reachable()` before any benchmark prompts are scanned.
- **FR-019**: `run_cli.py` MUST raise a `RuntimeError` with an actionable install message when `promptshield` is not found in PATH.
- **FR-020**: `run_http.py` MUST raise a `RuntimeError` with an instruction to run `promptshield server` when the server is unreachable.
- **FR-021**: If one sweep combination fails, `sweep.py` MUST record the failure (with `composite: -2.0` and the error message in `full_metrics.error`) and continue with remaining combinations.

### Key Entities

- **`cli.py`** (`benchmarks/cli.py`): Typer app entry point. Orchestrates single runs and sweeps, collects results, and triggers reporting.
- **`scanner.py`** (`benchmarks/scanner.py`): Contains `make_cli_scan_fn` to shell out to `promptshield scan` via subprocess.
- **`report.py`** (`benchmarks/report.py`): Handles all console and file formatting, including the sweep ranked table and JSON persistence.
- **`composite`**: Per-combination scalar `recall − (2 × fpr)`. Range: `[−2.0, 1.0]`. Higher is better.
- **`benchmarks/sweep_results.json`**: Ephemeral artefact written by `report.py`. Gitignored.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `promptshield-benchmark sweep` with default args runs exactly 10 combinations (2 models × 5 thresholds), prints a ranked 10-row table, and exits 0.
- **SC-002**: `benchmarks/sweep_results.json` is valid JSON containing `sweep_config` and a `results` array with `rank`, `model`, `threshold`, `recall`, `fpr`, `flag_rate`, `composite`, `layer_distribution`, `latency_p95_ms`, and `full_metrics` keys per entry.
- **SC-003**: The ranked table row order matches descending `composite` values.
- **SC-004**: `promptshield-benchmark run --interface lib` produces the same `recall_attacks` and `false_positive_rate` values as `promptshield-benchmark run` (no interface flag).
- **SC-005**: `promptshield-benchmark run --interface cli` completes all 80 prompts without error when `promptshield` is installed and configured.
- **SC-006**: `promptshield-benchmark run --interface http` completes all 80 prompts without error when `promptshield server` is running.
- **SC-007**: When `--interface http` is specified but the server is not running, `run.py` prints a warning before the first scan and `run_http.scan_fn` raises a `RuntimeError` with the instruction to start the server.
- **SC-008**: When `--interface cli` is specified but `promptshield` is not in PATH, `run_cli.scan_fn` raises a `RuntimeError` with an install instruction.
- **SC-009**: `benchmark_summary.json` contains `"interface"` as a top-level key reflecting the selected interface.
- **SC-010**: `benchmarks/sweep_results.json` does not appear in `git status` after a completed sweep run (it is covered by `.gitignore`).
- **SC-011**: The three interfaces produce identical `recall_attacks` and `false_positive_rate` values (within floating-point rounding) for the regex and embedding layers when run with the same model, threshold, and API key.
- **SC-012**: A custom stub `scan_fn` can be passed directly to `run_benchmark(dataset, stub_fn)` without importing `Shield`, confirming full decoupling.
