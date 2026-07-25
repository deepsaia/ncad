from ncad.service.build_pool import BuildPool


def test_lazy_start(tmp_path):
    pool = BuildPool(max_workers=1)
    assert pool.is_started() is False
    try:
        fut = pool.submit("build", {"spec": "/no/such.hocon"}, str(tmp_path), "",
                          str(tmp_path / "p.json"))
        assert pool.is_started() is True
        out = fut.result(timeout=120)     # a disallowed spec resolves fast (no geometry)
        assert out["ok"] is False
    finally:
        pool.shutdown(wait=True, timeout_s=10.0)


def test_active_count_zero_when_idle(tmp_path):
    pool = BuildPool(max_workers=1)
    assert pool.active_count() == 0
    try:
        fut = pool.submit("build", {"spec": "/no/such.hocon"}, str(tmp_path), "",
                          str(tmp_path / "p.json"))
        fut.result(timeout=120)
        # After completion the done-callback discards it.
        assert pool.active_count() == 0
    finally:
        pool.shutdown(wait=True, timeout_s=10.0)


def test_shutdown_before_start_is_safe():
    pool = BuildPool(max_workers=1)
    pool.shutdown(wait=True, timeout_s=1.0)   # never started; must not raise
    assert pool.is_started() is False
