"""Day 12 tests for Typer-based CLI commands."""

from typer.testing import CliRunner

from neurobridge.cli import app
from neurobridge.core.profile import Profile, get_profile_config
from neurobridge.core.quiz import QuizResult

runner = CliRunner()


def test_info_command_happy_path(monkeypatch) -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Memory backend" in result.output


def test_adapt_command_happy_path() -> None:
    result = runner.invoke(
        app, ["adapt", "This is critical and must be fixed ASAP.", "--profile", "anxiety"]
    )
    assert result.exit_code == 0
    assert "asap" not in result.output.lower()


def test_adapt_command_stdin_pipe() -> None:
    result = runner.invoke(
        app, ["adapt", "--profile", "adhd"], input="Sentence one. Sentence two. Sentence three."
    )
    assert result.exit_code == 0
    assert "Sentence" in result.output


def test_adapt_error_message_human_readable() -> None:
    result = runner.invoke(app, ["adapt", "hello", "--profile", "invalid"])
    assert result.exit_code != 0
    assert "Unsupported profile" in result.output


def test_profile_get_set_delete_round_trip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("NEUROBRIDGE_MEMORY_BACKEND", "sqlite")
    monkeypatch.setenv("NEUROBRIDGE_MEMORY_PATH", str(tmp_path / "cli-memory.db"))

    set_result = runner.invoke(app, ["profile", "set", "user-1", "--profile", "dyslexia"])
    assert set_result.exit_code == 0

    get_result = runner.invoke(app, ["profile", "get", "user-1"])
    assert get_result.exit_code == 0
    assert "max_sentence_words" in get_result.output

    delete_result = runner.invoke(app, ["profile", "delete", "user-1"])
    assert delete_result.exit_code == 0

    missing_result = runner.invoke(app, ["profile", "get", "user-1"])
    assert missing_result.exit_code != 0


def test_quiz_command_with_save(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("NEUROBRIDGE_MEMORY_BACKEND", "sqlite")
    monkeypatch.setenv("NEUROBRIDGE_MEMORY_PATH", str(tmp_path / "quiz-memory.db"))

    def fake_run_cli(self):
        return QuizResult(
            primary_profile=Profile.ADHD,
            secondary_profile=None,
            confidence=0.9,
            scores={
                "ADHD": 10.0,
                "AUTISM": 1.0,
                "DYSLEXIA": 1.0,
                "ANXIETY": 1.0,
                "DYSCALCULIA": 1.0,
            },
            recommended_config=get_profile_config(Profile.ADHD),
        )

    monkeypatch.setattr("neurobridge.cli.QuizEngine.run_cli", fake_run_cli)

    result = runner.invoke(app, ["quiz", "--user-id", "u-quiz", "--save"])
    assert result.exit_code == 0
    assert "Saved recommended profile config" in result.output


def test_serve_command_happy_path(monkeypatch) -> None:
    called = {}

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        called["args"] = args
        called["kwargs"] = kwargs

    monkeypatch.setattr("uvicorn.run", fake_run)
    result = runner.invoke(
        app, ["serve", "--port", "9000", "--host", "127.0.0.1", "--workers", "2"]
    )
    assert result.exit_code == 0
    assert called["kwargs"]["port"] == 9000
    assert called["kwargs"]["host"] == "127.0.0.1"
