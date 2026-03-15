import os
import time
from dataclasses import dataclass
from typing import Any, Callable

from dotenv import load_dotenv

from .dataset import DEFAULT_CONTEXT

# ---------------------------------------------------------------------------
# Runtime configuration snapshot
# ---------------------------------------------------------------------------

load_dotenv()


def get_runtime_config() -> dict:
    """
    Snapshot the runtime environment at benchmark startup.
    Returns a dict of key configuration values from environment variables.
    """
    return {
        "promptshield_llm_model": os.getenv("PROMPTSHIELD_LLM_MODEL", "unknown"),
        "promptshield_embedding_model": os.getenv(
            "PROMPTSHIELD_EMBEDDING_MODEL", "unknown"
        ),
        "confidence_threshold": os.getenv("PROMPTSHIELD_CONFIDENCE_THRESHOLD", "0.60"),
    }


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class BenchmarkResult:
    prompt: str
    expected: str  # "attack", "safe", "ambiguous"
    verdict: str  # "pass", "blocked", "flag"
    pipeline_layer: str  # "regex", "embedding", "llm", "none"
    confidence: float
    latency_ms: float
    reason: str  # LLM judge explanation or detection reason
    correct: bool | None  # True/False for attack/safe; None for ambiguous prompts


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


async def run_single(
    scan_fn: Callable[..., Any],
    prompt: str,
    expected: str,
) -> BenchmarkResult:
    """
    Run a single benchmark case using the provided scan callable.

    scan_fn must accept keyword arguments ``prompt`` and ``context`` and
    return an object (or Pydantic model) with ``.verdict``,
    ``.pipeline_layer``, ``.confidence``, and ``.reason`` attributes.
    """
    start = time.perf_counter_ns()
    result = scan_fn(prompt=prompt, context=DEFAULT_CONTEXT)
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000

    # Correctness: attacks should be blocked, safe prompts should pass.
    # Ambiguous prompts are not counted for recall/FP metrics.
    if expected == "attack":
        correct = result.verdict == "blocked"
    elif expected == "safe":
        correct = result.verdict == "pass"
    else:
        correct = None  # ambiguous — not evaluated for correctness

    return BenchmarkResult(
        prompt=prompt,
        expected=expected,
        verdict=result.verdict,
        pipeline_layer=result.pipeline_layer or "none",
        confidence=result.confidence,
        latency_ms=elapsed_ms,
        reason=result.reason or "",
        correct=correct,
    )


async def run_benchmark(
    dataset: list,
    scan_fn: Callable[..., Any],
    *,
    quiet: bool = False,
) -> list[BenchmarkResult]:
    """
    Run the full benchmark dataset through the given scan callable.

    Args:
        dataset:  List of (prompt, expected_label) tuples.
        scan_fn:  Callable that accepts ``prompt`` and ``context`` keyword
                  arguments and returns a scan-result object with verdict,
                  pipeline_layer, confidence, and reason attributes.
        quiet:    When True, suppress per-prompt progress lines (useful
                  for sweep runs where the outer loop already prints context).
    """
    results = []

    if not quiet:
        print(f"Running benchmark on {len(dataset)} prompts...\n")

    for i, (prompt, expected) in enumerate(dataset, 1):
        result = await run_single(scan_fn, prompt, expected)
        results.append(result)

        if not quiet:
            status = "✓" if result.correct else ("~" if result.correct is None else "✗")
            print(
                f"  [{i:03d}] {status} [{result.expected:9s}] → {result.verdict:7s} "
                f"via {result.pipeline_layer:9s} | {result.latency_ms:7.1f}ms"
                f" | {prompt[:60]}..."
            )

    return results
