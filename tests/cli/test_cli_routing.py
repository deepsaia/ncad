"""Bare ``ncad`` must behave like ``ncad view``, both routing to the launcher."""

from typer.testing import CliRunner

from ncad.cli import viewer_cli

runner = CliRunner()


def _patch_launch(monkeypatch):
    calls = []
    monkeypatch.setattr(
        viewer_cli.cli, "launch_viewer", lambda models_dir, host, port: calls.append((host, port))
    )
    return calls


def test_bare_ncad_launches_viewer(monkeypatch) -> None:
    calls = _patch_launch(monkeypatch)

    result = runner.invoke(viewer_cli.app, [])

    assert result.exit_code == 0
    assert len(calls) == 1


def test_ncad_view_launches_viewer(monkeypatch) -> None:
    calls = _patch_launch(monkeypatch)

    result = runner.invoke(viewer_cli.app, ["view"])

    assert result.exit_code == 0
    assert len(calls) == 1


def test_bare_ncad_passes_port_option(monkeypatch) -> None:
    calls = _patch_launch(monkeypatch)

    result = runner.invoke(viewer_cli.app, ["--port", "0"])

    assert result.exit_code == 0
    assert calls == [("127.0.0.1", 0)]


def test_build_requires_a_document_argument() -> None:
    result = runner.invoke(viewer_cli.app, ["build"])

    assert result.exit_code != 0


def test_build_is_a_registered_command() -> None:
    result = runner.invoke(viewer_cli.app, ["--help"])

    assert result.exit_code == 0
    assert "build" in result.output
