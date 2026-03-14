import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ScanResponseProxy:
    verdict: str
    pipeline_layer: str
    confidence: float
    reason: str


def make_cli_scan_fn(
    model: Optional[str] = None,
    threshold: Optional[float] = None,
    llm_model: Optional[str] = None,
) -> Callable:
    """
    Returns a scan_fn that shells out to the CLI.
    Injects overrides via environment variables if provided.
    """
    env_overrides: dict[str, str] = {}
    if model:
        env_overrides["PROMPTSHIELD_EMBEDDING_MODEL"] = model
    if threshold is not None:
        env_overrides["PROMPTSHIELD_CONFIDENCE_THRESHOLD"] = str(threshold)
    if llm_model:
        env_overrides["PROMPTSHIELD_LLM_MODEL"] = llm_model

    def scan_fn(prompt: str, context: Optional[str] = None) -> ScanResponseProxy:
        if env_overrides:
            env = {**os.environ, **env_overrides}
        else:
            env = None

        cmd: list[str] = [sys.executable, "-m", "promptshield.cli.main", "scan", prompt]
        if context:
            cmd += ["--context", context]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "The 'promptshield' command was not found in PATH.\n"
                "Install the package with:  pip install -e .  (from project root)"
            ) from exc

        raw = proc.stdout.strip()
        if not raw:
            raise RuntimeError(
                f"'promptshield scan' produced no stdout.\n"
                f"Exit code : {proc.returncode}\n"
                f"stderr    : {proc.stderr.strip() or '(empty)'}"
            )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Failed to parse CLI output as JSON.\n"
                f"Raw stdout: {raw!r}\n"
                f"stderr    : {proc.stderr.strip() or '(empty)'}"
            ) from exc

        return ScanResponseProxy(
            verdict=data.get("verdict", "flag"),
            pipeline_layer=data.get("pipeline_layer", "none"),
            confidence=float(data.get("confidence", 0.0)),
            reason=data.get("reason", ""),
        )

    return scan_fn
