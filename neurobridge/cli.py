"""Command-line entry point for NeuroBridge."""

from __future__ import annotations

from dataclasses import asdict
import importlib.util
import sys
from typing import Any, Dict, Optional

import typer
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table

from neurobridge import Config, NeuroBridge, Profile
from neurobridge.core.format_adapter import (
    HTMLAdapter,
    JSONAdapter,
    MarkdownAdapter,
    PlainTextAdapter,
    TTSAdapter,
)
from neurobridge.core.quiz import QuizEngine
from neurobridge.exceptions import NeuroBridgeError

app = typer.Typer(help="NeuroBridge CLI")
profile_app = typer.Typer(help="Manage stored user profiles")
app.add_typer(profile_app, name="profile")
console = Console()


def _parse_profile(name: str) -> Profile:
    try:
        return Profile[name.strip().upper()]
    except KeyError as exc:
        raise typer.BadParameter(f"Unsupported profile: {name}") from exc


def _format_yaml(data: Dict[str, Any], indent: int = 0) -> str:
    lines = []
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_format_yaml(value, indent + 1))
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)


def _create_bridge(debug: bool = False) -> NeuroBridge:
    config = Config.from_env()
    config.debug = config.debug or debug
    return NeuroBridge(config=config)


@app.command("serve")
def serve(
    port: int = typer.Option(8080, help="HTTP port"),
    host: str = typer.Option("127.0.0.1", help="Host interface"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
    workers: int = typer.Option(1, help="Uvicorn worker processes"),
) -> None:
    """Start the FastAPI server."""
    try:
        import uvicorn
    except ImportError as exc:
        raise typer.BadParameter(
            "uvicorn is required for serve command. Install neurobridge[server]."
        ) from exc

    bridge = _create_bridge()
    api_url = f"http://{host}:{port}/api/v1"
    banner = Panel.fit(
        f"[bold cyan]NeuroBridge v0.1.0[/bold cyan]\n"
        f"API: [green]{api_url}[/green]\n"
        f"Docs: [green]http://{host}:{port}/docs[/green]\n"
        f"Memory backend: [yellow]{bridge.config.memory_backend}[/yellow]",
        title="Server Startup",
    )
    console.print(banner)

    uvicorn.run(
        "neurobridge.server.app:app",
        host=host,
        port=port,
        reload=reload,
        workers=max(1, workers),
    )


@app.command("quiz")
def quiz(
    user_id: Optional[str] = typer.Option(
        None, "--user-id", help="Optional user id for persistence"
    ),
    save: bool = typer.Option(False, "--save", help="Persist recommended config for user_id"),
) -> None:
    """Run ProfileQuiz in terminal and optionally save result."""
    engine = QuizEngine()
    result = engine.run_cli()

    table = Table(title="Quiz Scores")
    table.add_column("Profile")
    table.add_column("Score", justify="right")
    for name, score in sorted(result.scores.items(), key=lambda item: item[1], reverse=True):
        table.add_row(name.lower(), f"{score:.2f}")
    console.print(table)

    config_yaml = _format_yaml(asdict(result.recommended_config))
    console.print(
        Panel(config_yaml, title="Recommended ProfileConfig (YAML)", border_style="green")
    )

    if save:
        if not user_id:
            raise typer.BadParameter("--save requires --user-id")
        bridge = _create_bridge()
        bridge.set_profile(result)
        if bridge.memory_store is None:
            raise typer.BadParameter("No memory backend configured; cannot save profile")
        bridge.memory_store.save_profile(user_id, result.recommended_config)
        console.print(f"Saved recommended profile config for [bold]{user_id}[/bold].")


@app.command("adapt")
def adapt(
    text: Optional[str] = typer.Argument(None, help="Input text (or pipe via stdin)"),
    profile: str = typer.Option(
        "adhd", "--profile", help="adhd|autism|dyslexia|anxiety|dyscalculia"
    ),
    fmt: str = typer.Option("markdown", "--format", help="markdown|html|plain|json|tts"),
    user_id: Optional[str] = typer.Option(None, "--user-id", help="Optional user id"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug output"),
) -> None:
    """Adapt text from argument or stdin and print formatted output."""
    source_text = text if text is not None else ""
    if not source_text.strip() and not sys.stdin.isatty():
        source_text = sys.stdin.read()
    if not source_text.strip():
        raise typer.BadParameter("No input text provided. Pass TEXT argument or pipe stdin.")

    bridge = _create_bridge(debug=debug)
    bridge.set_profile(_parse_profile(profile))

    spinner = Spinner("dots", text="Adapting output...")
    with console.status(spinner):
        result = bridge.chat(source_text, user_id=user_id)

    adapter_map = {
        "markdown": MarkdownAdapter(),
        "html": HTMLAdapter(),
        "plain": PlainTextAdapter(),
        "json": JSONAdapter(),
        "tts": TTSAdapter(),
    }
    if fmt not in adapter_map:
        raise typer.BadParameter(f"Unsupported format: {fmt}")
    rendered = adapter_map[fmt].format(result.adapted_text, bridge._profile_config)  # noqa: SLF001

    if console.width >= 120 and fmt == "markdown":
        left = Panel(source_text, title="Original", border_style="dim")
        right = Panel(rendered, title="Adapted", border_style="bright_green")
        console.print(Columns([left, right]))
    else:
        console.print(rendered)


@profile_app.command("get")
def profile_get(user_id: str) -> None:
    bridge = _create_bridge()
    if bridge.memory_store is None:
        raise typer.BadParameter("No memory backend configured")
    profile_config = bridge.memory_store.load_profile(user_id)
    if profile_config is None:
        raise typer.BadParameter(f"No profile found for user_id={user_id}")
    console.print(_format_yaml(asdict(profile_config)))


@profile_app.command("set")
def profile_set(user_id: str, profile: str = typer.Option(..., "--profile")) -> None:
    bridge = _create_bridge()
    parsed = _parse_profile(profile)
    bridge.set_profile(parsed)
    if bridge.memory_store is None:
        raise typer.BadParameter("No memory backend configured")
    bridge.memory_store.save_profile(user_id, bridge._profile_config)  # noqa: SLF001
    console.print(f"Saved profile [bold]{parsed.value}[/bold] for [bold]{user_id}[/bold].")


@profile_app.command("delete")
def profile_delete(user_id: str) -> None:
    bridge = _create_bridge()
    if bridge.memory_store is None:
        raise typer.BadParameter("No memory backend configured")
    bridge.memory_store.clear_user_data(user_id)
    console.print(f"Deleted stored data for [bold]{user_id}[/bold].")


@app.command("info")
def info() -> None:
    """Show runtime and dependency information."""
    bridge = _create_bridge()
    deps = ["openai", "anthropic", "langchain", "fastapi", "uvicorn", "transformers"]
    dep_table = Table(title="Optional Dependencies")
    dep_table.add_column("Package")
    dep_table.add_column("Installed")
    for dep in deps:
        installed = importlib.util.find_spec(dep) is not None
        dep_table.add_row(dep, "yes" if installed else "no")

    details = Table(title="NeuroBridge Info")
    details.add_column("Key")
    details.add_column("Value")
    details.add_row("Version", "0.1.0")
    details.add_row("Python", sys.version.split()[0])
    details.add_row("Memory backend", bridge.config.memory_backend)
    details.add_row("Data directory", "neurobridge/data")

    console.print(details)
    console.print(dep_table)


def main() -> None:
    try:
        app()
    except NeuroBridgeError as exc:
        message = f"{exc}\nSuggestion: {exc.suggestion}" if exc.suggestion else str(exc)
        console.print(Panel(message, title="NeuroBridge Error", border_style="red"))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()
