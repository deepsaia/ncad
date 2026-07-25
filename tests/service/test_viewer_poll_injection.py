from ncad.service.viewer_handler import _bootstrap_script


def test_bootstrap_carries_poll_ms():
    script = _bootstrap_script(dev=True, boot_id="abc", poll_ms=250)
    assert "window.NCAD_JOB_POLL_MS=250;" in script
    assert 'window.NCAD_API_BASE="/api/v1";' in script
