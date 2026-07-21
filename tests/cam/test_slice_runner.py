"""SliceRunner delegates to a slicer and reports generated/skipped/failed (subprocess mocked)."""

import subprocess

from ncad.cam.slice_runner import SliceRunner
from ncad.cam.slicer_locator import SlicerLocator
from ncad.cam.slicer_profile import SlicerProfile

_GOOD_GCODE = "; g\nG21\n;LAYER:0\nG1 X10 Y10 Z0.2 E1.5\n"


class _FakeLocator(SlicerLocator):
    """A locator that pretends a given slicer is (or is not) installed."""

    def __init__(self, located):
        self._located = located

    def locate(self, preference):
        return self._located


def _profile(tmp_path, with_config=True):
    if with_config:
        (tmp_path / "cfg.ini").write_text("; slicer config\n")
    return SlicerProfile({"config": "cfg.ini", "slicers": ["prusa"]}, tmp_path)


def test_skipped_when_no_slicer(tmp_path):
    runner = SliceRunner(locator=_FakeLocator(None))
    report = runner.slice("m.stl", _profile(tmp_path), str(tmp_path / "out.gcode"))
    assert report["status"] == "skipped"
    assert report["skipped"] and "no slicer installed" in report["skipped"][0]


def test_generated_on_success(tmp_path, monkeypatch):
    located = {"slicer": "prusa", "binary": "/bin/prusa-slicer", "dialect": "slic3r"}
    runner = SliceRunner(locator=_FakeLocator(located))
    out = tmp_path / "out.gcode"

    def fake_run(argv):
        # Emulate the slicer: write valid g-code to the --output path, succeed.
        out.write_text(_GOOD_GCODE)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(runner, "_run", fake_run)
    report = runner.slice("m.stl", _profile(tmp_path), str(out))
    assert report["status"] == "generated"
    assert report["slicer"] == "prusa"
    assert report["stats"]["layers"] == 1
    assert report["checks"]


def test_failed_on_nonzero_exit(tmp_path, monkeypatch):
    located = {"slicer": "prusa", "binary": "/bin/prusa-slicer", "dialect": "slic3r"}
    runner = SliceRunner(locator=_FakeLocator(located))
    monkeypatch.setattr(
        runner, "_run",
        lambda argv: subprocess.CompletedProcess(argv, 1, "", "config parse error"))
    report = runner.slice("m.stl", _profile(tmp_path), str(tmp_path / "out.gcode"))
    assert report["status"] == "failed"
    assert any("exited 1" in r for r in report["reasons"])


def test_failed_when_output_is_not_gcode(tmp_path, monkeypatch):
    located = {"slicer": "prusa", "binary": "/bin/prusa-slicer", "dialect": "slic3r"}
    runner = SliceRunner(locator=_FakeLocator(located))
    out = tmp_path / "out.gcode"

    def fake_run(argv):
        out.write_text("this is not gcode\n")   # slicer succeeded but wrote garbage
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(runner, "_run", fake_run)
    report = runner.slice("m.stl", _profile(tmp_path), str(out))
    assert report["status"] == "failed"
    assert any("motion" in r for r in report["reasons"])


def test_failed_when_config_missing(tmp_path):
    located = {"slicer": "prusa", "binary": "/bin/prusa-slicer", "dialect": "slic3r"}
    runner = SliceRunner(locator=_FakeLocator(located))
    profile = _profile(tmp_path, with_config=False)   # no cfg.ini on disk
    report = runner.slice("m.stl", profile, str(tmp_path / "out.gcode"))
    assert report["status"] == "failed"
    assert any("config not found" in r for r in report["reasons"])


def test_failed_when_slicer_invocation_errors(tmp_path, monkeypatch):
    located = {"slicer": "prusa", "binary": "/bin/prusa-slicer", "dialect": "slic3r"}
    runner = SliceRunner(locator=_FakeLocator(located))

    def boom(argv):
        raise OSError("binary vanished")

    monkeypatch.setattr(runner, "_run", boom)
    report = runner.slice("m.stl", _profile(tmp_path), str(tmp_path / "out.gcode"))
    assert report["status"] == "failed"
    assert any("invocation failed" in r for r in report["reasons"])
