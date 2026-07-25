from ncad.service.service_config import ServiceConfig


def test_defaults_when_env_unset(monkeypatch):
    for key in ("NCAD_HOST", "NCAD_PORT", "NCAD_DEV", "NCAD_MAX_WORKERS",
                "NCAD_MAX_CONCURRENT_BUILDS", "NCAD_JOB_QUEUE_MAX", "NCAD_JOB_TTL",
                "NCAD_JOB_POLL_MS", "NCAD_SHUTDOWN_TIMEOUT", "NCAD_JOBS_DIR"):
        monkeypatch.delenv(key, raising=False)
    cfg = ServiceConfig.from_env()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8000
    assert cfg.dev is False
    assert cfg.max_workers == ServiceConfig.worker_default()
    assert cfg.max_concurrent_builds == cfg.max_workers   # blank -> mirrors max_workers
    assert cfg.job_queue_max == 32
    assert cfg.job_ttl_s == 300.0
    assert cfg.job_poll_ms == 400
    assert cfg.shutdown_timeout_s == 30.0
    assert cfg.jobs_dir is None


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("NCAD_HOST", "0.0.0.0")
    monkeypatch.setenv("NCAD_PORT", "9000")
    monkeypatch.setenv("NCAD_DEV", "1")
    monkeypatch.setenv("NCAD_MAX_WORKERS", "3")
    monkeypatch.setenv("NCAD_JOB_QUEUE_MAX", "8")
    monkeypatch.setenv("NCAD_JOB_TTL", "60")
    monkeypatch.setenv("NCAD_JOB_POLL_MS", "250")
    monkeypatch.setenv("NCAD_SHUTDOWN_TIMEOUT", "5")
    monkeypatch.setenv("NCAD_JOBS_DIR", "/tmp/jobs")
    monkeypatch.delenv("NCAD_MAX_CONCURRENT_BUILDS", raising=False)
    cfg = ServiceConfig.from_env()
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 9000
    assert cfg.dev is True
    assert cfg.max_workers == 3
    assert cfg.max_concurrent_builds == 3   # blank concurrency -> mirrors max_workers=3
    assert cfg.job_queue_max == 8
    assert cfg.job_ttl_s == 60.0
    assert cfg.job_poll_ms == 250
    assert cfg.shutdown_timeout_s == 5.0
    assert cfg.jobs_dir == "/tmp/jobs"


def test_dev_truthy_variants(monkeypatch):
    for raw, expected in [("0", False), ("false", False), ("", False),
                          ("1", True), ("true", True), ("TRUE", True), ("yes", True)]:
        monkeypatch.setenv("NCAD_DEV", raw)
        assert ServiceConfig.from_env().dev is expected


def test_worker_default_is_at_least_one():
    assert ServiceConfig.worker_default() >= 1
