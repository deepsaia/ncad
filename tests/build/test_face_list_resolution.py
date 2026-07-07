from ncad.build.builder import Builder
from ncad.ops.op_registry import OpRegistry
from tests.kernel.fake_kernel import FakeKernel


def test_keyword_faces_resolve_for_shell_openings():
    # A block then a shell with openings = top: the builder must resolve the face keyword
    # to a face-handle list without a reference error, and the shell must build.
    part = {"profile": "solid", "features": [
        {"id": "sk", "op": "sketch", "plane": "XY",
         "elements": [{"id": "r", "type": "rectangle", "w": 20, "h": 20}]},
        {"id": "block", "op": "extrude", "profile": "sk", "distance": 20},
        {"id": "hollow", "op": "shell", "thickness": 2, "openings": "top"},
    ]}
    result = Builder(FakeKernel(), OpRegistry.with_defaults()).build_part(part)
    assert result.shape is not None
    assert not any(i.level == "error" for i in result.issues)
