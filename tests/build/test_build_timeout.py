"""BuildTimeout: SIGALRM wall-clock guard raises on a slow block, no-ops when safe or disabled."""

import threading
import time

import pytest

from ncad.build.build_timeout import BuildTimeout, BuildTimeoutError


def test_fast_block_does_not_raise():
    with BuildTimeout(2.0, label="fast"):
        time.sleep(0.05)  # well under the bound


def test_slow_block_raises_build_timeout():
    t0 = time.time()
    with pytest.raises(BuildTimeoutError, match="build timeout"):
        with BuildTimeout(0.3, label="slow"):
            # a Python-level busy wait so SIGALRM can fire between iterations (like the op loop)
            while time.time() - t0 < 5.0:
                pass
    assert time.time() - t0 < 2.0  # interrupted near the bound, not after the full 5s


def test_zero_disables_the_guard():
    t0 = time.time()
    with BuildTimeout(0.0, label="unbounded"):
        time.sleep(0.1)
    assert time.time() - t0 >= 0.1  # ran to completion, no alarm


def test_timer_is_cleared_on_exit():
    # after a guarded block completes, a later sleep past the old bound must NOT be interrupted
    with BuildTimeout(0.3, label="first"):
        pass
    time.sleep(0.4)  # would have fired the 0.3s alarm if it were not cleared; no raise = cleared


def test_off_main_thread_degrades_without_raising():
    # signals only arm on the main thread; a worker thread must build unguarded, not crash
    errors = []

    def _work():
        try:
            with BuildTimeout(0.2, label="threaded"):
                time.sleep(0.4)  # exceeds the bound, but no alarm can arm off-main-thread
        except BaseException as exc:  # noqa: BLE001 - the test asserts nothing propagates
            errors.append(exc)

    t = threading.Thread(target=_work)
    t.start()
    t.join()
    assert errors == []


def test_error_message_names_the_label_and_env_var():
    with pytest.raises(BuildTimeoutError) as info:
        with BuildTimeout(0.2, label="part 'gear'"):
            while True:
                pass
    msg = str(info.value)
    assert "part 'gear'" in msg
    assert "NCAD_BUILD_TIMEOUT" in msg
