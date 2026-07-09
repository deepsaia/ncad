from ncad.build.builder import Builder
from ncad.ops.op_registry import OpRegistry
from tests.kernel.fake_kernel import FakeKernel


def test_scope_field_is_accepted_and_defaults_all():
    # A feature carrying an explicit scope builds without error; absence means all bodies.
    part = {"profile": "solid", "features": [
        {"id": "sk", "op": "sketch", "plane": "XY",
         "elements": [{"id": "r", "type": "rectangle", "w": 10, "h": 10}]},
        {"id": "pad", "op": "extrude", "profile": "sk", "distance": 5, "scope": "all"},
    ]}
    result = Builder(FakeKernel(), OpRegistry.with_defaults()).build_part(part)
    assert result.shape is not None
    assert not any(i.level == "error" for i in result.issues)
