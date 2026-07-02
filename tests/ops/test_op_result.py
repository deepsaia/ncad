from ncad.build.build_issue import BuildIssue
from ncad.ops.op_result import OpResult


def test_op_result_holds_shape_provenance_issues() -> None:
    result = OpResult(shape="S", provenance={"f1": "sketch"}, issues=[])

    assert result.shape == "S"
    assert result.provenance == {"f1": "sketch"}
    assert result.issues == []


def test_op_result_carries_issues() -> None:
    issue = BuildIssue(node_id="pad", message="boom")
    result = OpResult(shape=None, provenance={}, issues=[issue])

    assert result.issues == [issue]
