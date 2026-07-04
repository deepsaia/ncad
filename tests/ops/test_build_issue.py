from ncad.ops.build_issue import BuildIssue


def test_build_issue_is_frozen_and_carries_node_id() -> None:
    issue = BuildIssue(node_id="soften", message="cannot find edges")

    assert issue.node_id == "soften"
    assert issue.message == "cannot find edges"


def test_build_issue_defaults_to_error_level() -> None:
    assert BuildIssue(node_id="x", message="m").level == "error"


def test_build_issue_accepts_warning_level() -> None:
    assert BuildIssue(node_id="x", message="m", level="warning").level == "warning"
