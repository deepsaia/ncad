import pytest

from ncad.ops.op_registry import OpRegistry, default_registry


def test_register_and_get_roundtrip() -> None:
    registry = OpRegistry()
    sentinel = object()
    registry.register("noop", lambda *a: sentinel)

    assert registry.get("noop")() is sentinel


def test_unknown_op_raises_keyerror() -> None:
    with pytest.raises(KeyError):
        OpRegistry().get("nope")


def test_default_registry_has_sketch_and_extrude() -> None:
    registry = default_registry()

    assert registry.get("sketch") is not None
    assert registry.get("extrude") is not None
