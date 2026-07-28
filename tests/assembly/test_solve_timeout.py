"""_solve_timeout_s: the motion-solve wall-clock bound reads NCAD_BUILD_TIMEOUT, safe default."""

from ncad.assembly.assembly_builder import _DEFAULT_SOLVE_TIMEOUT_S, _solve_timeout_s


def test_default_when_unset(monkeypatch):
    monkeypatch.delenv("NCAD_BUILD_TIMEOUT", raising=False)
    assert _solve_timeout_s() == _DEFAULT_SOLVE_TIMEOUT_S


def test_env_override(monkeypatch):
    monkeypatch.setenv("NCAD_BUILD_TIMEOUT", "300")
    assert _solve_timeout_s() == 300.0


def test_non_numeric_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("NCAD_BUILD_TIMEOUT", "soon")
    assert _solve_timeout_s() == _DEFAULT_SOLVE_TIMEOUT_S


def test_non_positive_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("NCAD_BUILD_TIMEOUT", "0")
    assert _solve_timeout_s() == _DEFAULT_SOLVE_TIMEOUT_S
    monkeypatch.setenv("NCAD_BUILD_TIMEOUT", "-5")
    assert _solve_timeout_s() == _DEFAULT_SOLVE_TIMEOUT_S


def test_default_is_generous():
    # a genuinely complex mechanism must have room; the default is minutes, not seconds
    assert _DEFAULT_SOLVE_TIMEOUT_S >= 600.0
