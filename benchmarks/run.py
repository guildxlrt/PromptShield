"""
PromptShield Benchmark — entry point
-------------------------------------
Measures per-layer latency, recall, false positive rate,
and request distribution across the detection pipeline.

Usage:
    python -m benchmarks.run

Requirements:
    pip install promptshield pandas numpy tabulate
    (PromptShield must be configured via .env or env vars)

Output:
    - Console summary table
    - benchmark_results.csv  (full per-prompt results)
    - benchmark_summary.json (aggregated metrics + runtime config)
"""

import asyncio

from .dataset import DATASET
from .metrics import compute_metrics
from .report import print_report, save_csv, save_json
from .runner import get_runtime_config, run_benchmark


async def main() -> None:
    # Capture runtime configuration at startup
    runtime_config = get_runtime_config()

    print("=" * 70)
    print("PROMPTSHIELD BENCHMARK")
    print("=" * 70)
    print("\n🔧 Runtime Configuration")
    for key, value in runtime_config.items():
        print(f"   {key:35s} : {value}")
    print()

    results = await run_benchmark(DATASET)

    save_csv(results)

    metrics = compute_metrics(results)
    # Inject runtime config into metrics for JSON output
    metrics["runtime_config"] = runtime_config
    save_json(metrics)

    print_report(metrics, results)


if __name__ == "__main__":
    asyncio.run(main())
