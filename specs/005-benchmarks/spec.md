# Feature Specification: Benchmarks Module

**Feature Branch**: `005-benchmarks`
**Created**: 2026-03-07
**Status**: ✅ **Implemented**

⚠️ **NOTE (2025)**: The committed output files `benchmark_results.csv` and `benchmark_summary.json` in the repository root are stale artefacts from a prior 87-prompt benchmark run and reflect a dataset version no longer present in `benchmarks/dataset.py` (which now defines 80 prompts). These files violate spec requirement FR-005 (must not be committed). To generate fresh, accurate results, run `python -m benchmarks.run` locally.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detection Accuracy Measurement (Priority: P1)

A maintainer runs the benchmark suite to measure the pipeline's recall on known attacks and its false positive rate on legitimate prompts.

**Why this priority**: Recall and false positive rate are the primary quality signals for the detection pipeline. Without a repeatable accuracy benchmark, regressions introduced by dataset or threshold changes go undetected.

**Independent Test**: Can be fully tested by running `python -m benchmarks.run` from the project root and verifying that `benchmark_summary.json` is written and contains `recall_attacks` and `false_positive_rate` keys with valid float values.

**Acceptance Scenarios**:

1. **Given** a configured PromptShield environment, **When** `python -m benchmarks.run` is executed, **Then** the runner scans all 80 prompts sequentially and prints one progress line per prompt showing its label, verdict, pipeline layer, latency, and correctness symbol.
2. **Given** the run completes, **When** `benchmark_summary.json` is read, **Then** `recall_attacks` reflects the fraction of the 40 attack-labelled prompts that received a `blocked` verdict.
3. **Given** the run completes, **When** `benchmark_summary.json` is read, **Then** `false_positive_rate` reflects the fraction of the 30 safe-labelled prompts that did **not** receive a `pass` verdict.
4. **Given** the run completes, **When** `benchmark_summary.json` is read, **Then** the 10 ambiguous-labelled prompts are excluded from both recall and FP calculations and appear only in `ambiguous_distribution`.

---

### User Story 2 - Per-Layer Latency Profiling (Priority: P2)

A maintainer uses the benchmark output to profile per-layer latency and detect performance regressions against the pipeline's SLOs.

**Why this priority**: The pipeline has explicit latency SLOs (< 500ms for regex/embedding, < 2s for LLM fallback). A quantitative latency report makes regressions visible before they reach production.

**Independent Test**: Can be fully tested by reading the `latency_by_layer` key in `benchmark_summary.json` and verifying it contains p50/p95/p99/mean entries for each layer that handled at least one prompt.

**Acceptance Scenarios**:

1. **Given** the benchmark has run, **When** reading `latency_by_layer` in the summary, **Then** each active layer entry contains `count`, `p50_ms`, `p95_ms`, `p99_ms`, and `mean_ms`.
2. **Given** the regex layer handled prompts, **When** checking its `p95_ms` value, **Then** it is below 500ms on a standard developer machine.
3. **Given** the benchmark has run, **When** reading `layer_distribution`, **Then** each layer entry shows the absolute count and percentage of requests it terminated.
4. **Given** a scan is measured, **When** the latency is recorded, **Then** it is captured with nanosecond precision (via `time.perf_counter_ns()`) and reported in milliseconds to two decimal places.

---

### User Story 3 - Raw Results Export (Priority: P2)

A maintainer saves the full per-prompt scan output to CSV for offline analysis, debugging, or charting in an external tool.

**Why this priority**: The console report is a summary. Individual false positives or missed attacks require row-level inspection that is impractical to do from the terminal output alone.

**Independent Test**: Can be fully tested by running the benchmark and verifying that `benchmark_results.csv` contains exactly 80 rows (one per prompt) with the correct column headers.

**Acceptance Scenarios**:

1. **Given** the benchmark completes, **When** `benchmark_results.csv` is opened, **Then** it contains exactly 80 data rows plus a header row.
2. **Given** a false positive exists, **When** filtering `benchmark_results.csv` for `expected=safe` and `verdict!=pass`, **Then** the offending prompt appears in the output.
3. **Given** the project root is inspected after a run, **When** checking git status, **Then** neither `benchmark_results.csv` nor `benchmark_summary.json` appears as an untracked file — both are covered by `.gitignore`.

---

### User Story 4 - Runtime Configuration Capture (Priority: P2)

A maintainer reviews the runtime configuration snapshot to verify which embedding model, LLM model, and confidence threshold were active during the benchmark run.

**Why this priority**: Latency and accuracy metrics are only meaningful when compared to the exact configuration that produced them. Capturing the config at startup ensures reproducibility and prevents confusion from silent config changes.

**Independent Test**: Can be fully tested by running the benchmark and verifying that `benchmark_summary.json` contains a `runtime_config` key with `promptshield_llm_model`, `promptshield_embedding_model`, and `confidence_threshold` entries.

**Acceptance Scenarios**:

1. **Given** the benchmark is running, **When** startup completes, **Then** the console prints a "Runtime Configuration" section showing the three captured values.
2. **Given** the benchmark completes, **When** `benchmark_summary.json` is read, **Then** `runtime_config` contains entries for `promptshield_llm_model`, `promptshield_embedding_model`, and `confidence_threshold`.
3. **Given** an environment variable is not set, **When** `get_runtime_config()` is called, **Then** it returns `"unknown"` (for model vars) or the documented default string (for threshold).

---

### Edge Cases

- **Missing API key**: If no API key is configured, all prompts that reach the LLM engine return `flag, 0.5`. The benchmark continues without error; `flag_rate` in the summary will reflect this.
- **Ambiguous prompts**: The 10 ambiguous prompts are never evaluated for correctness. `correct` is `None` for these rows in the CSV and they are reported only under `ambiguous_distribution` in the JSON summary.
- **Gitignored outputs**: `benchmark_results.csv` and `benchmark_summary.json` are listed in `.gitignore`. They are ephemeral artefacts of a local run and MUST NOT be committed.
- **Embedding index cold start**: The first prompt in a run triggers the NumPy index build, which embeds all 40 examples from `attack_patterns.json`. Its measured latency will be anomalously high and should not be read as representative of steady-state embedding performance.
- **Unset config variables**: If environment variables are not set, the benchmark does not fail — `get_runtime_config()` returns sentinel values (`"unknown"` or `"0.42"`) and the user is expected to check the startup console output or the JSON to identify the actual config.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The benchmark MUST be runnable as `python -m benchmarks.run` from the project root with no additional arguments required.
- **FR-002**: The benchmark MUST scan every prompt in `DATASET` sequentially using the same `Shield` instance and print one progress line per prompt to stdout.
- **FR-003**: The benchmark MUST write a `benchmark_results.csv` file to the project root containing one row per prompt with columns: `prompt`, `expected`, `verdict`, `pipeline_layer`, `confidence`, `latency_ms`, `correct`.
- **FR-004**: The benchmark MUST write a `benchmark_summary.json` file to the project root containing all aggregated metrics from `compute_metrics()` and a `runtime_config` object.
- **FR-005**: Both `benchmark_results.csv` and `benchmark_summary.json` MUST be listed in `.gitignore` and never committed to the repository.
- **FR-006**: `DATASET` MUST contain exactly **40 attack** prompts, **10 ambiguous** prompts, and **30 safe** prompts (80 total). Attack prompts are split across two sub-groups: 16 syntactically explicit (Layer 1 targets) and 24 semantically paraphrased (Layer 2 targets).
- **FR-007**: Recall MUST be computed exclusively on prompts labelled `"attack"`. A `blocked` verdict is the only correct outcome for an attack.
- **FR-008**: False positive rate MUST be computed exclusively on prompts labelled `"safe"`. Any verdict other than `pass` counts as a false positive.
- **FR-009**: Prompts labelled `"ambiguous"` MUST be excluded from both recall and FP calculations and MUST appear in `ambiguous_distribution` in the summary.
- **FR-010**: The module MUST be structured as a Python package under `benchmarks/` and split across five source files: `dataset.py`, `runner.py`, `metrics.py`, `report.py`, and `run.py`.
- **FR-011**: All scan calls MUST inject `DEFAULT_CONTEXT` as the `context` argument to `shield.scan()` to ensure the LLM fallback layer has consistent context across every prompt in the run.
- **FR-012**: `compute_metrics()` MUST report per-layer latency at p50, p95, and p99 percentiles in addition to the mean.
- **FR-013**: Latency MUST be measured using `time.perf_counter_ns()` for nanosecond precision and converted to milliseconds via division by `1_000_000`.
- **FR-014**: At benchmark startup, `get_runtime_config()` MUST snapshot the following environment variables and include them in the console output and the JSON summary: `PROMPTSHIELD_LLM_MODEL` & `PROMPTSHIELD_EMBEDDING_MODEL`.
- **FR-015**: The console output MUST include a "Runtime Configuration" section printed immediately after the "PROMPTSHIELD BENCHMARK" header, before any benchmark runs begin.

### Key Entities

- **`DATASET`** (`dataset.py`): List of `(prompt: str, label: str)` tuples. Valid labels: `"attack"`, `"safe"`, `"ambiguous"`.
- **`DEFAULT_CONTEXT`** (`dataset.py`): The fixed system context string injected into every `shield.scan()` call to simulate a realistic deployment scenario.
- **`BenchmarkResult`** (`runner.py`): Dataclass holding a single prompt's scan output — `prompt`, `expected`, `verdict`, `pipeline_layer`, `confidence`, `latency_ms`, `correct`.
- **`get_runtime_config()`** (`runner.py`): Function that returns a dict of environment variable snapshots: `promptshield_llm_model`, `promptshield_embedding_model`, `confidence_threshold`.
- **`benchmark_results.csv`**: Ephemeral raw output — one row per prompt, written to the project root, gitignored.
- **`benchmark_summary.json`**: Ephemeral aggregated metrics — one JSON object for the full run, written to the project root, gitignored. Includes `runtime_config` as a top-level key.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 80 prompts are scanned and logged without an unhandled exception when the pipeline is fully configured with a valid API key.
- **SC-002**: `benchmark_results.csv` contains exactly 80 data rows with all required columns populated.
- **SC-003**: `benchmark_summary.json` is valid JSON and contains all of the following top-level keys: `total_prompts`, `recall_attacks`, `false_positive_rate`, `flag_rate`, `layer_distribution`, `latency_by_layer`, `attacks_terminated_by_layer`, `false_positive_prompts`, `ambiguous_distribution`, `runtime_config`.
- **SC-004**: The console report renders the layer distribution table, latency table, and overall accuracy metrics without error.
- **SC-005**: Neither output file appears in `git status` after a completed run.
- **SC-006**: The runtime configuration is printed to the console with all three values visible before the benchmark begins.
- **SC-007**: Measured latencies differ by at most 1µs when the same prompt is scanned twice (demonstrating nanosecond precision is captured and not rounded).
