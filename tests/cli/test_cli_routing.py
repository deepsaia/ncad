"""Bare ``ncad`` must behave like ``ncad view``, both routing to the launcher."""

from typer.testing import CliRunner

from ncad.cli import viewer_cli

runner = CliRunner()


def test_bare_ncad_launches_viewer(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        viewer_cli, "launch_viewer", lambda models_dir, host, port: calls.append((host, port))
    )

    result = runner.invoke(viewer_cli.app, [])

    assert result.exit_code == 0
    assert len(calls) == 1


def test_ncad_view_launches_viewer(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        viewer_cli, "launch_viewer", lambda models_dir, host, port: calls.append((host, port))
    )

    result = runner.invoke(viewer_cli.app, ["view"])

    assert result.exit_code == 0
    assert len(calls) == 1


def test_bare_ncad_passes_port_option(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        viewer_cli, "launch_viewer", lambda models_dir, host, port: calls.append((host, port))
    )

    result = runner.invoke(viewer_cli.app, ["--port", "0"])

    assert result.exit_code == 0
    assert calls == [("127.0.0.1", 0)]
