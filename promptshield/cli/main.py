from pathlib import Path
from typing import Optional

import typer
import yaml

from promptshield import Shield, ShieldConfig

app = typer.Typer(help="PromptShield CLI - Local security for LLM applications.")


@app.command()
def scan(
    prompt: str = typer.Argument(..., help="The prompt to scan for malicious content"),
    context: Optional[str] = typer.Option(
        None, "--context", "-c", help="System prompt or context"
    ),
    pretty: bool = typer.Option(
        False, "--pretty", "-p", help="Human-readable colored output"
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", help="Provider API key override"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Provider LLM model override"
    ),
):
    """Scan a prompt for injection or jailbreak attempts."""
    config = ShieldConfig.load()

    if api_key:
        config.provider.api_key = api_key
    if model:
        config.provider.llm_model = model

    shield = Shield(config=config)
    result = shield.scan(prompt=prompt, context=context)

    if pretty:
        # Pretty mode colored output
        color = typer.colors.GREEN if result.verdict == "pass" else typer.colors.RED
        icon = "✅" if result.verdict == "pass" else "🛡️"
        verdict_str = typer.style(
            result.verdict.upper() + f" {icon}", fg=color, bold=True
        )

        typer.echo("┌─ PromptShield Scan Result ──────────────────┐")
        # Padding adjustments for precise table
        verdict_pad = verdict_str + " " * max(0, 31 - len(result.verdict) - 3)
        typer.echo(f"│ Verdict:     {verdict_pad}│")
        typer.echo(f"│ Threat:      {result.threat_type:<31}│")
        conf_str = f"{int(result.confidence * 100)}%"
        typer.echo(f"│ Confidence:  {conf_str:<31}│")
        typer.echo(f"│ Layer:       {result.pipeline_layer:<31}│")
        reason_str = result.reason[:31]
        typer.echo(f"│ Reason:      {reason_str:<31}│")
        typer.echo("└──────────────────────────────────────────────┘")
    else:
        # Default JSON output
        typer.echo(result.model_dump_json())

    if result.verdict == "blocked" or result.verdict == "flag":
        raise typer.Exit(code=1)


@app.command()
def init():
    """Create a default .promptshield.yaml configuration file."""
    config_path = Path(".promptshield.yaml")
    if config_path.exists():
        typer.secho(
            "Configuration file .promptshield.yaml already exists.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=0)

    default_config = {
        "provider": {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "your_key_here",
            "llm_model": "meta-llama/llama-3-8b-instruct",
            "embedding_model": "baai/bge-large-en-v1.5",
        },
        "detection": {"confidence_threshold": 0.65, "max_prompt_length": 10000},
        "server": {"port": 8765, "host": "127.0.0.1"},
    }

    with open(config_path, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    typer.secho("Created default .promptshield.yaml.", fg=typer.colors.GREEN)


@app.command()
def server():
    """Start the local PromptShield HTTP server."""
    import uvicorn

    from promptshield.config import ShieldConfig

    config = ShieldConfig.load()
    typer.secho(
        f"Starting PromptShield Server on {config.server.host}:{config.server.port}...",
        fg=typer.colors.BLUE,
    )
    uvicorn.run(
        "promptshield.server.app:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
    )


if __name__ == "__main__":
    app()
