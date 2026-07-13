import pytest

pytestmark = pytest.mark.slow


def test_pairwise_touching_and_clearance() -> None:
    from build123d import Box, Pos

    from ncad.assembly.interference_checker import InterferenceChecker
    from ncad.kernel.build123d_kernel import Build123dKernel

    placed = [
        {"id": "a", "shape": Box(10, 10, 10)},
        {"id": "b", "shape": Pos(10, 0, 0) * Box(10, 10, 10)},   # flush-touching a
        {"id": "c", "shape": Pos(40, 0, 0) * Box(10, 10, 10)},   # clear of both
    ]
    findings = InterferenceChecker(Build123dKernel()).check(placed)
    by_pair = {(f["a"], f["b"]): f for f in findings}
    assert by_pair[("a", "b")]["status"] == "touching"
    assert by_pair[("a", "c")]["status"] == "clearance"
    # a spans x -5..5, c (at x=40) spans 35..45 -> gap = 35 - 5 = 30.
    assert by_pair[("a", "c")]["distance"] == pytest.approx(30.0, abs=1e-3)


def test_overlap_reports_interfering_with_volume() -> None:
    from build123d import Box, Pos

    from ncad.assembly.interference_checker import InterferenceChecker
    from ncad.kernel.build123d_kernel import Build123dKernel

    placed = [{"id": "a", "shape": Box(10, 10, 10)},
              {"id": "b", "shape": Pos(5, 0, 0) * Box(10, 10, 10)}]
    findings = InterferenceChecker(Build123dKernel()).check(placed)
    assert findings[0]["status"] == "interfering"
    assert findings[0]["volume"] == pytest.approx(500.0, rel=1e-3)
