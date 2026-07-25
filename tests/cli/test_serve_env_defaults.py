from ncad.service.service_config import ServiceConfig


def test_config_supplies_serve_defaults(monkeypatch):
    monkeypatch.setenv("NCAD_PORT", "9100")
    monkeypatch.setenv("NCAD_HOST", "0.0.0.0")
    cfg = ServiceConfig.from_env()

    # Emulate the serve resolution: an unset (None) flag falls back to the env-config value.
    def resolve(flag, cfg_value):
        return flag if flag is not None else cfg_value

    assert resolve(None, cfg.port) == 9100
    assert resolve(8000, cfg.port) == 8000        # explicit flag wins
    assert resolve(None, cfg.host) == "0.0.0.0"
