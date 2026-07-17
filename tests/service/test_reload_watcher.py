"""Unit tests for ReloadWatcher: server-side autoreload is wired only in dev.

ReloadWatcher.enable(autoreload) calls autoreload.start() when dev is True and does nothing when
dev is False. It does NOT watch() directories or the viewer HTML (autoreload already tracks every
imported .py; the HTML is re-read per request by ViewerPage(dev=True), and specs are re-scanned per
request by SpecCatalog). A fake autoreload records the calls so no real process re-exec happens.
"""

from ncad.service.reload_watcher import ReloadWatcher


class _FakeAutoreload:
    """Records autoreload API calls instead of re-exec'ing the process."""

    def __init__(self) -> None:
        self.started = 0
        self.watched: list[str] = []

    def start(self) -> None:
        self.started += 1

    def watch(self, path: str) -> None:
        self.watched.append(path)


def test_enable_starts_autoreload_when_dev():
    fake = _FakeAutoreload()
    ReloadWatcher(dev=True).enable(fake)
    assert fake.started == 1


def test_enable_is_noop_when_not_dev():
    fake = _FakeAutoreload()
    ReloadWatcher(dev=False).enable(fake)
    assert fake.started == 0


def test_enable_does_not_watch_directories_or_html():
    # The review nixed watch() on dirs/HTML (watch() polls a single file's mtime, not a tree, and
    # would re-exec on HTML edits that the per-request re-read already surfaces). Assert none added.
    fake = _FakeAutoreload()
    ReloadWatcher(dev=True).enable(fake)
    assert fake.watched == []
