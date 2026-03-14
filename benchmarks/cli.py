import asyncio
import sys
from typing import Any, Optional

import typer

from benchmarks.dataset import DATASET
from benchmarks.metrics import compute_metrics
from benchmarks.report import (
    print_ranked_table,
    print_report,
    save_csv,
    save_json,
    save_sweep_results,
)
from benchmarks.runner import get_runtime_config, run_benchmark
from benchmarks.scanner import make_cli_scan_fn

app = typer.Typer(help="PromptShield Benchmark CLI")

DEFAULT_MODELS: list[str] = [
    "baai/bge-large-en-v1.5",
    "baai/bge-large-en-v1.5",
]
DEFAULT_THRESHOLDS: list[float] = [0.40, 0.50, 0.60]


async def _run_main() -> None:
    runtime_config = get_runtime_config()

    print("=" * 70)
    print("PROMPTSHIELD BENCHMARK")
    print("=" * 70)
    print("\n🔧 Runtime Configuration  [interface: cli]")
    for key, value in runtime_config.items():
        print(f"   {key:35s} : {value}")
    print()

    scan_fn = make_cli_scan_fn()
    results = await run_benchmark(DATASET, scan_fn)

    save_csv(results)

    metrics = compute_metrics(results)
    metrics["runtime_config"] = runtime_config
    metrics["interface"] = "cli"
    save_json(metrics)

    print_report(metrics, results)


async def _run_combination(
    model: str,
    threshold: float,
    llm_model: Optional[str],
    combo_index: int,
    total_combos: int,
    dataset: list,
) -> dict[str, Any]:
    _header = f"[{combo_index}/{total_combos}]"
    print(f"\n{_header} model={model!r}  llm={llm_model!r}  threshold={threshold}")
    print(f"{'─' * 72}")

    scan_fn = make_cli_scan_fn(model=model, threshold=threshold, llm_model=llm_model)

    results = await run_benchmark(dataset, scan_fn, quiet=False)
    metrics = compute_metrics(results)

    recall = metrics["recall_attacks"]
    fpr = metrics["false_positive_rate"]
    composite = round(recall - 2.0 * fpr, 4)

    latency_p95: dict[str, float] = {
        layer: round(d["p95_ms"], 1) for layer, d in metrics["latency_by_layer"].items()
    }

    return {
        "model": model,
        "llm_model": llm_model or "(default)",
        "threshold": threshold,
        "recall": recall,
        "fpr": fpr,
        "flag_rate": metrics["flag_rate"],
        "composite": composite,
        "layer_distribution": metrics["layer_distribution"],
        "latency_p95_ms": latency_p95,
        "full_metrics": metrics,
    }


async def _run_sweep(
    models: list[str],
    thresholds: list[float],
    llm_models: list[Optional[str]],
) -> list[dict[str, Any]]:
    total_combos = len(models) * len(thresholds) * len(llm_models)

    print("=" * 72)
    print("PROMPTSHIELD BENCHMARK SWEEP")
    print("=" * 72)
    print(f"\n  Models     : {', '.join(models)}")
    print(f"  Thresholds : {', '.join(str(t) for t in thresholds)}")
    print(f"  LLMs       : {', '.join(m or '(default)' for m in llm_models)}")
    print("  Interface  : cli")
    print(f"  Total runs : {total_combos}")

    combo_index = 0
    all_results: list[dict[str, Any]] = []

    for model in models:
        for llm_model in llm_models:
            for threshold in thresholds:
                combo_index += 1
                try:
                    entry = await _run_combination(
                        model=model,
                        threshold=threshold,
                        llm_model=llm_model,
                        combo_index=combo_index,
                        total_combos=total_combos,
                        dataset=DATASET,
                    )
                    all_results.append(entry)
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"\n  ✗ Combination model={model!r} llm={llm_model!r} threshold={threshold} FAILED: {exc}",
                        file=sys.stderr,
                    )
                    all_results.append(
                        {
                            "model": model,
                            "llm_model": llm_model or "(default)",
                            "threshold": threshold,
                            "recall": 0.0,
                            "fpr": 1.0,
                            "flag_rate": 0.0,
                            "composite": -2.0,
                            "layer_distribution": {},
                            "latency_p95_ms": {},
                            "full_metrics": {"error": str(exc)},
                        }
                    )

    ranked = sorted(all_results, key=lambda x: x["composite"], reverse=True)
    return ranked


@app.command()
def run():
    """Run a single benchmark against current config."""
    asyncio.run(_run_main())


@app.command()
def sweep(
    models_embedding: str = typer.Option(
        ",".join(DEFAULT_MODELS), help="Comma-separated embedding models"
    ),
    thresholds: str = typer.Option(
        ",".join(str(t) for t in DEFAULT_THRESHOLDS),
        help="Comma-separated confidence thresholds",
    ),
    models_llm: Optional[str] = typer.Option(
        None, help="Comma-separated LLM models to test"
    ),
):
    """Sweep multiple (embedding_model, llm_model, threshold) combinations."""
    models_list = (
        [m.strip() for m in models_embedding.split(",") if m.strip()]
        if models_embedding
        else DEFAULT_MODELS
    )
    thresholds_list = (
        [float(t.strip()) for t in thresholds.split(",") if t.strip()]
        if thresholds
        else DEFAULT_THRESHOLDS
    )

    if models_llm:
        llms_list = [m.strip() for m in models_llm.split(",") if m.strip()]
    else:
        llms_list = [None]

    sweep_config = {
        "models": models_list,
        "thresholds": thresholds_list,
        "llm_models": llms_list,
        "interface": "cli",
    }

    ranked = asyncio.run(
        _run_sweep(
            models=models_list,
            thresholds=thresholds_list,
            llm_models=llms_list,
        )
    )

    print_ranked_table(ranked)
    save_sweep_results(ranked, sweep_config)


if __name__ == "__main__":
    app()
