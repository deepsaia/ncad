import os
import time

from ncad.kernel.guarded_runner import GuardedRunner

# These helpers are module-level so multiprocessing can pickle them (a nested/lambda
# callable would fail to pickle and never reach the child).


def _returns_value(x: int) -> int:
    return x + 1


def _sleeps_forever(_ignored: int) -> int:
    time.sleep(5.0)
    return 0


def _raises(_ignored: int) -> int:
    raise ValueError("boom")


def _crashes(_ignored: int) -> int:
    # Exit the child with a nonzero code WITHOUT raising a catchable exception; this stands
    # in for an OCCT segfault (which would kill the child the same way).
    os._exit(3)


def test_ok_returns_value() -> None:
    result = GuardedRunner(timeout_s=5.0).run(_returns_value, 41)
    assert result.outcome == "ok"
    assert result.value == 42
    assert result.error is None


def test_timeout_returns_fast() -> None:
    start = time.monotonic()
    result = GuardedRunner(timeout_s=0.5).run(_sleeps_forever, 0)
    elapsed = time.monotonic() - start
    assert result.outcome == "timeout"
    assert result.value is None
    # Returns near the timeout, not near the 5s sleep.
    assert elapsed < 3.0


def test_raise_is_captured() -> None:
    result = GuardedRunner(timeout_s=5.0).run(_raises, 0)
    assert result.outcome == "raised"
    assert result.error is not None
    assert "boom" in result.error


def test_crash_is_captured() -> None:
    result = GuardedRunner(timeout_s=5.0).run(_crashes, 0)
    assert result.outcome == "crashed"
    assert result.value is None
