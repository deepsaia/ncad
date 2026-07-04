from ncad.build.cache_key import CacheKeyBuilder


def test_same_feature_same_key():
    b = CacheKeyBuilder("fake-1")
    f = {"id": "pad", "op": "extrude", "distance": 8}
    assert b.key(f, []) == b.key(dict(f), [])


def test_changed_param_changes_key():
    b = CacheKeyBuilder("fake-1")
    assert b.key({"id": "pad", "op": "extrude", "distance": 8}, []) != \
        b.key({"id": "pad", "op": "extrude", "distance": 10}, [])


def test_dep_key_change_propagates():
    b = CacheKeyBuilder("fake-1")
    f = {"id": "hole", "op": "hole", "diameter": 6}
    assert b.key(f, ["depA"]) != b.key(f, ["depB"])


def test_dep_key_order_does_not_matter():
    b = CacheKeyBuilder("fake-1")
    f = {"id": "bool", "op": "boolean"}
    assert b.key(f, ["a", "b"]) == b.key(f, ["b", "a"])


def test_kernel_version_changes_key():
    f = {"id": "pad", "op": "extrude", "distance": 8}
    assert CacheKeyBuilder("fake-1").key(f, []) != CacheKeyBuilder("b123d=0.10").key(f, [])


def test_reserved_keys_excluded():
    b = CacheKeyBuilder("fake-1")
    bare = {"id": "pad", "op": "extrude", "distance": 8}
    withrefs = {**bare, "__refs__": {"profile": "x"}, "__shapes__": {"x": 1}}
    assert b.key(bare, []) == b.key(withrefs, [])
