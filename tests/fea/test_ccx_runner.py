import os

from ncad.fea.ccx_locator import CcxLocator
from ncad.fea.ccx_runner import CcxRunner


class _NoCcx(CcxLocator):
    def locate(self):
        return None


class _FakeCcx(CcxLocator):
    def locate(self):
        return "/usr/bin/ccx"


def test_skipped_when_no_ccx(tmp_path):
    (tmp_path / "job.inp").write_text("*NODE\n")
    report = CcxRunner(locator=_NoCcx()).solve(str(tmp_path / "job.inp"), str(tmp_path))
    assert report["status"] == "skipped"
    assert report["skipped"] and "ccx" in report["skipped"][0].lower()


def test_failed_on_nonzero_exit(tmp_path, monkeypatch):
    (tmp_path / "job.inp").write_text("*NODE\n")
    runner = CcxRunner(locator=_FakeCcx())

    class _Completed:
        returncode = 1
        stderr = "ccx error: singular matrix"
        stdout = ""

    monkeypatch.setattr(runner, "_run", lambda argv, cwd: _Completed())
    report = runner.solve(str(tmp_path / "job.inp"), str(tmp_path))
    assert report["status"] == "failed" and report["reasons"]


def test_generated_when_frd_written(tmp_path, monkeypatch):
    (tmp_path / "job.inp").write_text("*NODE\n")
    runner = CcxRunner(locator=_FakeCcx())

    class _Completed:
        returncode = 0
        stderr = ""
        stdout = "Job finished"

    def _fake_run(argv, cwd):
        # ccx writes <job>.frd next to the .inp on success.
        with open(os.path.join(cwd, "job.frd"), "w") as handle:
            handle.write("    9999\n")
        return _Completed()

    monkeypatch.setattr(runner, "_run", _fake_run)
    report = runner.solve(str(tmp_path / "job.inp"), str(tmp_path))
    assert report["status"] == "generated"
    assert report["artifact"].endswith("job.frd")
