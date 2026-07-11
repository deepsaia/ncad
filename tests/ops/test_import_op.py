from ncad.ops.import_op import ImportOp
from tests.kernel.fake_kernel import FakeKernel


def test_import_op_returns_solid() -> None:
    result = ImportOp().build(None, {"file": "unused-by-fake.step"}, {}, FakeKernel())
    assert result.shape is not None
    assert not [i for i in result.issues if i.level == "error"]


def test_import_op_missing_file_field_errors() -> None:
    result = ImportOp().build(None, {}, {}, FakeKernel())
    assert [i for i in result.issues if i.level == "error"]
