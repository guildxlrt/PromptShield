# Implementation Plan: Benchmarks Module

**Branch**: `005-benchmarks` | **Date**: 2026-03-07 | **Spec**: [specs/005-benchmarks/spec.md]

## Summary

Introduce a `benchmarks/` package for measuring PromptShield's detection accuracy and
per-layer latency. The feature consists of: (1) a structural refactor splitting the original
monolithic `benchmarks/benchmark.py` into five focused modules (all logic identical —
pure reorganisation), (2) nanosecond-precision latency measurement via `time.perf_counter_ns()`,
(3) runtime environment snapshots captured at startup, and (4) this documentation. 
The package runs entirely outside the core `promptshield/` library and has no impact on 
the runtime dependency graph.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `pandas`, `numpy`, `tabulate`, `promptshield` (local)
**Storage**: Two ephemeral output files written to the project root — both gitignored, never committed
**Testing**: Manual execution (`python -m benchmarks.run`) — no automated test suite for the benchmark itself
**Target Platform**: Local developer machine
**Project Type**: Internal developer tooling (not shipped as part of the library)
**Performance Goals**: None — the benchmark is a measurement tool, not a latency-sensitive path
**Constraints**: Must not import from or modify anything inside `promptshield/`; zero infrastructure required

## Module Structure

```text
benchmarks/
├── __init__.py   empty — marks the directory as a Python package
├── run.py        entry point: imports DATASET, run_benchmark, get_runtime_config,
│                 compute_metrics, print_report, save_csv, save_json;
│                 calls asyncio.run(main())
├── dataset.py    DATASET list (80 prompts with labels) and DEFAULT_CONTEXT constant
├── runner.py     BenchmarkResult dataclass, get_runtime_config(), run_single(), 
│                 run_benchmark() — uses time.perf_counter_ns() for latency
├── metrics.py    compute_metrics() — pandas / numpy aggregation over BenchmarkResult list
└── report.py     print_report(), save_csv(), save_json()
```

### Dependency graph between modules

```text
run.py
 ├── dataset.py        (DATASET, DEFAULT_CONTEXT)
 ├── runner.py         (run_benchmark, get_runtime_config)  ──► dataset.py (DEFAULT_CONTEXT)
 ├── metrics.py        (compute_metrics) ──► runner.py (BenchmarkResult)
 └── report.py         (print_report, save_csv, save_json) ──► runner.py (BenchmarkResult)
```

No module imports from any other module except as shown above. `run.py` is the only
file that imports from all four siblings.

## Output Files

Both files are written to the project root by `save_csv()` and `save_json()` in `report.py`.
Both are covered by `.gitignore` and must never be committed.

| File                     | Format | Contents                                                                                                                                  |
|--------------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `benchmark_results.csv`  | CSV    | One row per prompt: `prompt`, `expected`, `verdict`, `pipeline_layer`, `confidence`, `latency_ms`, `reason`, `correct`                   |
| `benchmark_summary.json` | JSON   | Aggregated metrics: `total_prompts`, `recall_attacks`, `false_positive_rate`, `flag_rate`, `layer_distribution`, `latency_by_layer`, `attacks_blocked_by_layer`, `false_positive_prompts`, `ambiguous_distribution`, `runtime_config` |

## Dataset Composition

| Label       | Count | Purpose                                                                 |
|-------------|-------|-------------------------------------------------------------------------|
| `attack`    | 40    | 16 syntactically explicit (Layer 1 targets) + 24 semantic / paraphrased (Layer 2 targets) |
| `ambiguous` | 10    | Borderline prompts — excluded from recall and FP metrics                |
| `safe`      | 30    | Legitimate prompts — false positives are tracked here                   |
| **Total**   | **80** |                                                                        |

## Latency Measurement

Latency is captured with nanosecond precision using `time.perf_counter_ns()` in `run_single()`:

```python
start = time.perf_counter_ns()
result = shield.scan(prompt=prompt, context=DEFAULT_CONTEXT)
elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
```

This approach provides microsecond-level granularity in the reported milliseconds, eliminating
rounding errors from lower-precision timing methods and enabling detection of sub-millisecond
performance variations.

## Runtime Configuration Snapshot

At startup, `run.py` calls `get_runtime_config()` from `runner.py`, which snapshots the
following environment variables:

| Variable                          | Fallback Value | Purpose                                   |
|-----------------------------------|----------------|-------------------------------------------|
| `PROMPTSHIELD_LLM_MODEL`          | `"unknown"`    | Records which LLM was active during the run |
| `PROMPTSHIELD_EMBEDDING_MODEL`    | `"unknown"`    | Records which embedding model was active |
| `PROMPTSHIELD_CONFIDENCE_THRESHOLD` | `"0.65"`        | Records the detection threshold          |

The snapshot is printed to the console in a "Runtime Configuration" section at startup
and included in `benchmark_summary.json` under the `runtime_config` key. This ensures
all latency and accuracy measurements can be traced back to the exact configuration
that produced them, enabling reproducible benchmarking across time and across environments.

## How to Run

```bash
# From the project root, with PromptShield configured via .promptshield.yaml or env vars:
python -m benchmarks.run
```

The runner prints:
1. Banner and runtime configuration snapshot
2. One progress line per prompt (80 total)
3. Saves `benchmark_results.csv` and `benchmark_summary.json` to the project root
4. Prints the formatted console report with accuracy metrics, latency tables, and any false positives

## Debug Instrumentation

**Removed in final implementation:**
- Removed debug print statements from `benchmarks/runner.py` (e.g., `print(f"[DEBUG] raw reason: {repr(result.reason)}")`)
- Removed debug print statements from `promptshield/detection/llm_engine.py` (e.g., `print(f"[DEBUG] LLM raw reason: ...")`)

The codebase is production-clean with no debug output. All instrumentation is clean and focused on core functionality.

## Constitution Check

- [x] III. Budget & Infrastructure Pragmatism: Zero infrastructure — no cloud services, no DB, no server process.
- [x] IV. Lean Integration: The package is entirely opt-in developer tooling; importing `promptshield` is the only coupling to the core library.
