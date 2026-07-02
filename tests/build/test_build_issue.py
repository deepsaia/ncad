from ncad.build.build_issue import BuildIssue


def test_build_issue_is_frozen_and_carries_node_id() -> None:
    issue = BuildIssue(node_id="soften", message="cannot find edges")

    assert issue.node_id == "soften"
    assert issue.message == "cannot find edges"
