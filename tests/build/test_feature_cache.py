from ncad.build.feature_cache import CacheEntry, FeatureCache


def test_put_then_get_returns_entry():
    cache = FeatureCache()
    entry = CacheEntry(shape="S", descriptors=[{"kind": "face"}])
    cache.put("k1", entry)
    assert cache.get("k1") is entry


def test_get_missing_returns_none():
    assert FeatureCache().get("nope") is None


def test_stats_track_hits_and_misses():
    cache = FeatureCache()
    cache.record("sk", hit=True)
    cache.record("pad", hit=False)
    assert cache.stats() == {"sk": True, "pad": False}


def test_reset_stats_clears_them_but_keeps_entries():
    cache = FeatureCache()
    cache.put("k1", CacheEntry(shape="S", descriptors=None))
    cache.record("sk", hit=True)
    cache.reset_stats()
    assert cache.stats() == {}
    assert cache.get("k1") is not None
