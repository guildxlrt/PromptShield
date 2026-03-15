# Implementation Tasks: Benchmark Sweep & Multi-Interface Support

**Feature Branch**: `006-benchmark-sweep`

## Dependencies

- Phase 1 (Runner Refactor) must be completed before all other phases.
- Phase 2 (Interface Modules) depends on Phase 1.
- Phase 3 (Sweep Runner) depends on Phases 1 and 2.
- Phase 4 (run.py Update) depends on Phases 1 and 2.
- Phase 5 (Documentation) depends on Phases 1–4.

---

## Phase 1: Injectable scan_fn Refactor

- [x] T001 Refactor `benchmarks/runner.py`: replace the `shield: Shield` parameter in `run_single()` with `scan_fn: Callable[..., Any]`. Remove the `from src import Shield` import — `runner.py` must no longer import the library directly.
- [x] T002 Update `run_single()` to call `scan_fn(prompt=prompt, context=DEFAULT_CONTEXT)` instead of `shield.scan(...)`. The return value is duck-typed: any object with `.verdict`, `.pipeline_layer`, `.confidence`, and `.reason` attributes is accepted.
- [x] T003 Update `run_benchmark()` signature to accept `scan_fn: Callable[..., Any]` as its second positional argument and remove the internal `shield = Shield()` instantiation.
- [x] T004 Add a `quiet: bool = False` keyword argument to `run_benchmark()`. When `quiet=True`, suppress the per-prompt progress lines. When `quiet=False` (default), print them as before — preserving backwards-compatible console output for `run.py`.
- [x] T005 Verify that all existing callers of `run_benchmark()` and `run_single()` are updated to pass a `scan_fn` argument. Confirm the module passes `ruff check` with no errors.

---

## Phase 2: Interface Modules

- [x] T006 Create `benchmarks/interfaces/` directory and add an empty `benchmarks/interfaces/__init__.py` to mark it as a Python package.
- [x] T007 Create `benchmarks/interfaces/run_lib.py`. Expose a module-level `scan_fn` that wraps a lazily-instantiated `Shield()` using config loaded from the environment / `.promptshield.yaml`. This must reproduce the original `run.py` behaviour exactly.
- [x] T008 Create `benchmarks/interfaces/run_cli.py`. Expose a module-level `scan_fn` that calls `[sys.executable, "-m", "src.cli.main", "scan", prompt, "--context", context]` via `subprocess.run(capture_output=True)` and parses the JSON stdout into a `ScanResponse`. Handle the following failure modes with clear `RuntimeError` messages:
  - `FileNotFoundError` → `promptshield` not in PATH → print install instruction.
  - Empty stdout → print exit code and stderr.
  - `json.JSONDecodeError` → print raw stdout and stderr.
  - Non-zero exit code is **not** treated as an error (exit 1 = blocked/flag verdict).
- [x] T009 Create `benchmarks/interfaces/run_http.py`. Expose a module-level `scan_fn` that POSTs `{"prompt": ..., "context": ...}` to `http://localhost:8765/v1/scan` via `httpx.post()` with a 30-second timeout and parses the response into a `ScanResponse`. Handle:
  - `httpx.ConnectError` → raise `RuntimeError` instructing user to run `promptshield server`.
  - `httpx.TimeoutException` → raise `RuntimeError` with timeout details.
- [x] T010 Add `_check_reachable()` to `run_http.py`. The function pings `GET /health` with a 3-second timeout and prints a one-time warning to stdout if the server is unreachable. It must not raise — the actual error surfaces on the first scan call.

---

## Phase 3: Sweep Runner

- [x] T011 Create `benchmarks/sweep.py` with the `DEFAULT_MODELS` and `DEFAULT_THRESHOLDS` constants:
  - `DEFAULT_MODELS = ["baai/bge-large-en-v1.5", "google/gemini-embedding-001"]`
  - `DEFAULT_THRESHOLDS = [0.40, 0.60]`
- [x] T012 Implement `_reset_vector_index()` in `sweep.py`. It imports `src.detection.vector_engine` at call time (lazy import) and sets `_ve._index = None` and `_ve._metadata = []` to invalidate the in-process embedding cache.
- [x] T013 Implement the scan_fn factory trio in `sweep.py`:
  - `_make_lib_scan_fn(model, threshold, llm_model)` — creates a `Shield` with a mutated `ShieldConfig` and returns `shield.scan`.
  - `_make_cli_scan_fn(model, threshold, llm_model)` — returns a closure that merges `os.environ` with `PROMPTSHIELD_EMBEDDING_MODEL` / `PROMPTSHIELD_CONFIDENCE_THRESHOLD` overrides and passes them to the subprocess.
  - `_make_http_scan_fn(model, threshold, llm_model)` — re-uses `run_http.scan_fn` directly (server config is immutable per run).
- [x] T014 Implement `_build_scan_fn(interface, model, threshold, llm_model)` dispatcher in `sweep.py` that delegates to the three factories above.
- [x] T015 Implement `_run_combination(model, threshold, llm_model, interface, combo_index, total_combos, dataset)` as an `async` function. It must:
  - Print a header line `[combo_index/total_combos] model=... threshold=...`.
  - Call `_build_scan_fn()` to get the scan_fn.
  - Call `run_benchmark(dataset, scan_fn, quiet=False)`.
  - Call `compute_metrics()` on the results.
  - Compute `composite = round(recall - 2.0 * fpr, 4)`.
  - Return a result dict with keys: `model`, `threshold`, `recall`, `fpr`, `flag_rate`, `composite`, `layer_distribution`, `latency_p95_ms`, `full_metrics`.
- [x] T016 Implement `run_sweep(models, thresholds, llm_model, interface)` as an `async` function. It must:
  - Iterate models (outer) × thresholds (inner).
  - Call `_reset_vector_index()` only when the model changes (not between thresholds of the same model) — only for the `lib` interface where the global index is in-process.
  - Wrap each `_run_combination()` call in a `try/except` so a single failure records `composite: -2.0` and the sweep continues.
  - Sort final results by `composite` descending and return the ranked list.
- [x] T017 Implement `_print_ranked_table(ranked)` in `sweep.py`. The table must include columns: `#`, `Model`, `Thresh`, `Recall`, `FPR`, `FlagRate`, `Reg%`, `Emb%`, `LLM%`, `p95 Reg`, `p95 Emb`, `p95 LLM`, `Composite ↓`. Use `tabulate(..., tablefmt="rounded_outline")`. Abbreviate model names longer than 36 characters. Print a 🏆 best-configuration callout below the table.
- [x] T018 Implement `_save_results(ranked, sweep_config)` in `sweep.py`. Write a JSON file to `benchmarks/sweep_results.json` with `sweep_config` and `results` (ranked list, each entry includes `rank` and `full_metrics`).
- [x] T019 Implement `_parse_args()` and `async def main()` in `sweep.py`. `main()` parses models/thresholds from comma-separated strings, constructs `sweep_config`, calls `run_sweep()`, calls `_print_ranked_table()`, calls `_save_results()`. Guard the call with `if __name__ == "__main__": asyncio.run(main())`.
- [x] T020 Verify that `python -m benchmarks.sweep --help` prints the usage string including all four flags (`--models`, `--thresholds`, `--llm`, `--interface`) and their defaults.

---

## Phase 4: run.py Update

- [x] T021 Add `import argparse` to `benchmarks/run.py`. Replace the bare `asyncio.run(main())` call with an `argparse`-based CLI that accepts `--interface {lib,cli,http}` (default: `lib`).
- [x] T022 Add `_load_scan_fn(interface: str)` helper to `run.py`. It imports the `scan_fn` from the matching interface module, calls `_check_reachable()` if the HTTP interface is selected, and raises `SystemExit` for unknown interface names.
- [x] T023 Update `async def main(interface: str = "lib")` to accept the interface name, call `_load_scan_fn(interface)`, pass the resulting `scan_fn` to `run_benchmark()`, and store `interface` in the metrics dict before `save_json()`.
- [x] T024 Update the banner printed in `main()` to include the active interface: `"🔧 Runtime Configuration  [interface: {interface}]"`.
- [x] T025 Verify that `python -m benchmarks.run --help` shows the `--interface` flag with all three choices and a description of each mode.

---

## Phase 5: .gitignore & Documentation

- [x] T026 Add `sweep_results.json` and `benchmarks/sweep_results.json` to `.gitignore` so that sweep output artefacts are never committed.
- [x] T027 Create `specs/006-benchmark-sweep/spec.md` documenting six user stories, 21 functional requirements, key entities, and 12 success criteria covering the sweep runner and all three interface modes.
- [x] T028 Create `specs/006-benchmark-sweep/plan.md` documenting the module structure, dependency graph, composite score formula, scan_fn contract, index reset strategy, CLI env-var injection pattern, and how to run the sweep.
- [x] T029 Create `specs/006-benchmark-sweep/tasks.md` (this file) listing all implementation tasks grouped by phase with dependency ordering.
- [x] T030 Update `README.md`:
  - Add a "Benchmark Sweep" subsection under the Benchmarks section documenting `python -m benchmarks.sweep` usage with all flags.
  - Add an "Interface Modes" subsection documenting `--interface lib/cli/http` for both `run.py` and `sweep.py`.
  - Note that results should be identical across all three interfaces for the same configuration.

---

## Post-Implementation Fixes

- [x] Fix 1: Remove HTTP interface entirely from `benchmarks/run.py` and `benchmarks/sweep.py`.
- [x] Fix 2: Fix CLI interface `ModuleNotFoundError` by invoking via `sys.executable, "-m", "src.cli.main"`.
- [x] Fix 3: Fix LLM verdict normalization in `src/detection/llm_engine.py` (mapping "block" to "blocked").
- [x] Fix 4: Refactor benchmark tooling to expose a single CLI entry point `promptshield-benchmark` with `run` and `sweep` subcommands, completely remove `benchmarks/interfaces`, update README and speckit to document `promptshield-benchmark` as canonical usage.
- [x] Fix 5: Add `--rerun-failed` flag to `sweep` command to re-evaluate combinations that previously failed.
