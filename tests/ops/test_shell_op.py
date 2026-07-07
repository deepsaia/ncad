from ncad.ops.shell_op import ShellOp
from tests.kernel.fake_kernel import FakeKernel


def _box(k):
    return k.extrude(k.polygon_face([(0, 0), (20, 0), (20, 20), (0, 20)], "XY"),
                     distance=20.0)


def test_shell_hollows_the_solid():
    k = FakeKernel()
    box = _box(k)
    result = ShellOp().build(box, {"id": "sh", "thickness": 2}, {}, k)
    assert result.shape is not None
    assert 0 < k.volume(result.shape) < k.volume(box)


def test_shell_missing_solid_reports_issue():
    k = FakeKernel()
    result = ShellOp().build(None, {"id": "sh", "thickness": 2}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)


def test_shell_bad_thickness_reports_issue():
    k = FakeKernel()
    box = _box(k)
    result = ShellOp().build(box, {"id": "sh", "thickness": 0}, {}, k)
    assert result.shape is None
    assert any(i.level == "error" for i in result.issues)
