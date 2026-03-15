# Implementation Plan: Benchmark Sweep & Multi-Interface Support

**Branch**: `006-benchmark-sweep` | **Date**: 2026-03-08 | **Spec**: [specs/006-benchmark-sweep/spec.md]

## Summary

Extend the `benchmarks/` package in two complementary directions:

1. **Injectable `scan_fn`** — Refactor `runner.py` so `run_single()` and
   `run_benchmark()` accept a `scan_fn` callable instead of a hardcoded
   `Shield()` instance.  This single change unlocks all three remaining
   deliverables without touching any core library code.

2. **Three interface modules** — Concrete `scan_fn` implementations for
   each PromptShield surface: the Python library (`run_lib.py`), the CLI
   subprocess (`run_cli.py`), and the local HTTP server (`run_http.py`).
   `run.py` gains an `--interface` flag that selects between them.

3. **Sweep runner** (`sweep.py`) — Iterates over a grid of
   `(embedding_model, threshold)` combinations, resets the in-memory
   vector index between model changes, collects per-combination metrics,
   and prints a ranked comparison table ordered by the composite score
   `recall − (2 × fpr)`.

All changes are confined to the `benchmarks/` package and `src.detection.vector_engine`
(index reset only).  Zero changes to the core detection pipeline or public library API.

---

## Technical Context

| Item | Value |
|------|-------|
| Language / Version | Python 3.11+ |
| Primary Dependencies | `httpx`, `tabulate`, `pandas`, `numpy` (already in dev deps) |
| New files | `benchmarks/sweep.py`, `benchmarks/interfaces/{__init__,run_lib,run_cli,run_http}.py` |
| Modified files | `benchmarks/runner.py`, `benchmarks/run.py`, `.gitignore` |
| Storage | `benchmarks/sweep_results.json` (ephemeral, gitignored) |
| Infrastructure | None — sweep uses the same zero-infra profile as `run.py` |
| Performance Goals | None — benchmark tooling is not latency-sensitive |
| Constraints | Must not modify `src/` except to reset the vector index globals |

---

## Module Structure

```text
benchmarks/
├── __init__.py              (unchanged — empty package marker)
├── dataset.py               (unchanged)
├── metrics.py               (unchanged)
├── report.py                ← MODIFIED: Added print_ranked_table and save_sweep_results
├── runner.py                ← MODIFIED: scan_fn injectable, quiet flag added
├── scanner.py               ← NEW: make_cli_scan_fn shells out to promptshield scan
└── cli.py                   ← NEW: single entry point for run and sweep (replaces run.py/sweep.py)
```

### Dependency graph

```text
sweep.py
 ├── benchmarks.dataset          (DATASET)
 ├── benchmarks.runner           (run_benchmark)
 ├── benchmarks.metrics          (compute_metrics)
 ├── src.detection.vector_engine (_index, _metadata — reset only)
 └── _build_scan_fn()
      ├── interfaces.run_lib      (lib path)
      ├── _make_cli_scan_fn()     (cli path — inline factory)
      └── interfaces.run_http     (http path)

run.py
 ├── benchmarks.dataset          (DATASET)
 ├── benchmarks.runner           (run_benchmark, get_runtime_config)
 ├── benchmarks.metrics          (compute_metrics)
 ├── benchmarks.report           (print_report, save_csv, save_json)
 └── _load_scan_fn(interface)
      ├── interfaces.run_lib
      ├── interfaces.run_cli
      └── interfaces.run_http

interfaces/run_lib.py  ──► src.Shield
interfaces/run_cli.py  ──► subprocess → promptshield CLI → JSON → ScanResponse
interfaces/run_http.py ──► httpx → POST /v1/scan → JSON → ScanResponse
```

---

## runner.py Changes

### Before

```python
async def run_single(shield: Shield, prompt: str, expected: str) -> BenchmarkResult:
    result = shield.scan(prompt=prompt, context=DEFAULT_CONTEXT)
    ...

async def run_benchmark(dataset: list) -> list[BenchmarkResult]:
    shield = Shield()
    for i, (prompt, expected) in enumerate(dataset, 1):
        result = await run_single(shield, prompt, expected)
        print(f"  [{i:03d}] ...")
```

### After

```python
async def run_single(
    scan_fn: Callable[..., Any],
    prompt: str,
    expected: str,
) -> BenchmarkResult:
    result = scan_fn(prompt=prompt, context=DEFAULT_CONTEXT)
    ...

async def run_benchmark(
    dataset: list,
    scan_fn: Callable[..., Any],
    *,
    quiet: bool = False,
) -> list[BenchmarkResult]:
    for i, (prompt, expected) in enumerate(dataset, 1):
        result = await run_single(scan_fn, prompt, expected)
        if not quiet:
            print(f"  [{i:03d}] ...")
```

Key decisions:
- `scan_fn` signature: `(prompt: str, context: str | None) → object` where
  the returned object must expose `.verdict`, `.pipeline_layer`,
  `.confidence`, and `.reason`.  Both `ScanResponse` (Pydantic) and plain
  dicts-turned-into-models satisfy this.
- `quiet=True` is used by the sweep runner to suppress per-prompt lines
  when many combinations are running in sequence and stdout verbosity
  would be overwhelming.  The sweep's outer loop already prints a
  `[n/total] model | threshold` header line.
- `Shield` is no longer imported in `runner.py` at all — that import now
  lives exclusively in `interfaces/run_lib.py`.

---

## Interface Modules

### run_lib.py

Simplest possible wrapper.  A single shared `Shield()` instance is
constructed at import time using the config loaded from `.promptshield.yaml`
/ environment variables.  The module-level `scan_fn` is a bound method:

```python
_shield = Shield()

def scan_fn(prompt: str, context: str | None = None):
    return _shield.scan(prompt=prompt, context=context)
```

This matches the original `run_benchmark` behaviour exactly — same
instance, same config resolution, same result contract.

### run_cli.py

Delegates every scan call to `promptshield scan <prompt> [--context <ctx>]`
via `subprocess.run`.  Key implementation notes:

- **Exit code**: The CLI exits 1 for `blocked` / `flag` verdicts.  This is
  documented, intentional behaviour.  `run_cli.scan_fn` does **not** check
  `proc.returncode` — the verdict is determined solely by parsing the JSON
  stdout.
- **Error handling**: Two failure modes get distinct, actionable errors:
  1. `FileNotFoundError` → `promptshield` not in PATH → install instruction.
  2. `json.JSONDecodeError` → CLI crashed and printed a traceback → raw
     stdout and stderr attached to the error message.
- **No `--json` flag needed**: The CLI defaults to JSON output when
  `--pretty` is not passed.
- **ScanResponse construction**: `ScanResponse(**data)` from the parsed
  dict.  Pydantic handles UUID coercion for `scan_id`.

### run_http.py

Uses the synchronous `httpx` client (already a project dependency) to POST
to `http://localhost:8765/v1/scan`.  Two notes:

- **`_check_reachable()`**: A best-effort GET to `/health` at import/startup
  time.  Failure is non-fatal — it only prints a warning.  The actual scan
  calls will surface a hard `RuntimeError` if the server is truly down.
- **Timeout**: 30 seconds per request, to accommodate the LLM fallback layer
  which can take several seconds on slow API paths.
- **Server config immutability**: The server uses its own baked-in config.
  Sweep combinations with different models/thresholds produce identical
  results when using this interface.  A warning is printed at sweep startup.

---

## sweep.py Design

### Grid iteration order

```
for model in models:          # outer — model changes trigger index reset
    reset_vector_index()      # once per model, not per threshold
    for threshold in thresholds:
        scan_fn = _build_scan_fn(interface, model, threshold, llm_model)
        results = await run_benchmark(DATASET, scan_fn, quiet=False)
        metrics = compute_metrics(results)
        composite = metrics["recall_attacks"] - 2.0 * metrics["false_positive_rate"]
        all_results.append(entry)
```

The index reset is skipped for the `cli` and `http` interfaces because
those don't share the in-process `vector_engine` state.

### Vector index reset

```python
import src.detection.vector_engine as _ve
_ve._index = None
_ve._metadata = []
```

This directly nulls the module-level globals that `_get_index()` checks.
The next scan call that reaches the embedding layer will trigger a full
rebuild for the new model.  No locks are needed in a single-threaded sweep.

### scan_fn factories

| Interface | Factory | Config injection |
|-----------|---------|------------------|
| `lib` | `_make_lib_scan_fn(model, threshold, llm_model)` | `ShieldConfig` mutated before `Shield()` construction |
| `cli` | `_make_cli_scan_fn(model, threshold, llm_model)` | `PROMPTSHIELD_*` env vars passed to subprocess |
| `http` | `_make_http_scan_fn(...)` | Returns `run_http.scan_fn` unchanged (server config is external) |

### Composite score

```
composite = recall − (2 × fpr)
```

Range: `[−2.0, 1.0]`

| Configuration | Recall | FPR | Composite |
|---------------|--------|-----|-----------|
| Perfect       | 1.00   | 0.00 | **+1.00** |
| High recall, 10 % FP | 1.00 | 0.10 | +0.80 |
| Balanced      | 0.95   | 0.00 | **+0.95** |
| Over-blocking | 1.00   | 0.20 | +0.60 |
| Failed run    | 0.00   | 1.00 | **−2.00** |

Ranking by composite ensures a balanced configuration with zero false
positives ranks above an over-blocking one that catches every attack.

### Comparison table columns

```
#  │ Model                              │ Thresh │ Recall │  FPR  │ FlagRate │ Reg% │ Emb% │ LLM% │ p95 Reg │ p95 Emb │ p95 LLM │ Composite ↓
```

Long model names are truncated to 36 characters with a leading `…` to keep
the table readable in an 80-column terminal.

### Failure resilience

If a combination throws any exception (API error, rate limit, network
timeout), the sweep records:

```json
{
  "model": "...",
  "threshold": 0.60,
  "composite": -2.0,
  "full_metrics": { "error": "<exception message>" }
}
```

…and continues with the next combination.  This ensures that a single
flaky API call during a 10-combination sweep does not discard all results.

---

## Output Files

| File | Format | Written by | Contents |
|------|--------|-----------|----------|
| `benchmark_results.csv` | CSV | `run.py` | Unchanged — one row per prompt (80 rows) |
| `benchmark_summary.json` | JSON | `run.py` | Unchanged + new `"interface"` top-level key |
| `benchmarks/sweep_results.json` | JSON | `sweep.py` | `sweep_config` + ranked `results` array |

### sweep_results.json schema

```json
{
  "sweep_config": {
    "models": ["baai/bge-large-en-v1.5", "google/gemini-embedding-001"],
    "thresholds": [0.40, 0.60],
    "llm_model": "(from config)",
    "interface": "lib"
  },
  "results": [
    {
      "rank": 1,
      "model": "baai/bge-large-en-v1.5",
      "threshold": 0.60,
      "recall": 0.9750,
      "fpr": 0.0000,
      "flag_rate": 0.0375,
      "composite": 0.9750,
      "layer_distribution": {
        "regex":     { "count": 16, "pct": 20.0 },
        "embedding": { "count": 24, "pct": 30.0 },
        "llm":       { "count": 10, "pct": 12.5 },
        "none":      { "count": 30, "pct": 37.5 }
      },
      "latency_p95_ms": {
        "regex": 1.2,
        "embedding": 312.5,
        "llm": 1840.0
      },
      "full_metrics": { "...": "complete metrics dict from compute_metrics()" }
    }
  ]
}
```

---

## run.py Changes

`run.py` gains an `argparse`-based `--interface` flag.  The module-level
`_load_scan_fn(interface)` helper performs the conditional import and, for
the HTTP interface, calls `_check_reachable()` before returning.

The `benchmark_summary.json` output gains one new top-level key:
`"interface": "lib" | "cli" | "http"`.  All existing keys are unchanged.

```bash
# All equivalent for lib interface:
promptshield-benchmark run
promptshield-benchmark run --interface lib

# CLI interface:
promptshield-benchmark run --interface cli

# HTTP interface (server must be running):
promptshield server &
promptshield-benchmark run --interface http
```

---

## How to Run

```bash
# Default sweep (2 models × 5 thresholds = 10 runs, lib interface):
promptshield-benchmark sweep

# Custom models:
promptshield-benchmark sweep --models "baai/bge-large-en-v1.5,google/gemini-embedding-001"

# Custom thresholds:
promptshield-benchmark sweep --thresholds "0.40,0.60"

# Custom LLM for fallback layer:
promptshield-benchmark sweep --llm "meta-llama/llama-3-8b-instruct"

# Full custom sweep:
promptshield-benchmark sweep \
  --models "baai/bge-large-en-v1.5,google/gemini-embedding-001" \
  --thresholds "0.40,0.60" \
  --llm "meta-llama/llama-3-8b-instruct"

# Using the CLI interface:
promptshield-benchmark sweep --interface cli

# Using the HTTP interface (server must be running in another terminal):
promptshield server
promptshield-benchmark sweep --interface http
```

The runner prints for each combination:
1. `[n/total] model=... threshold=...` header line
2. Per-prompt progress lines (same format as `run.py`)
3. After all combinations: ranked comparison table + best config callout
4. Saves `benchmarks/sweep_results.json`

---

## Constitution Check

- [x] III. Budget & Infrastructure Pragmatism: Zero infrastructure — no cloud services, no DB, no server process (except for the optional HTTP interface test).
- [x] IV. Lean Integration: All changes are confined to `benchmarks/`; the core library (`src/`) is not modified except for a direct global reset in the vector engine.
- [x] V. No Hardcoded Secrets: API keys flow from `.promptshield.yaml` / environment variables, never hardcoded.
