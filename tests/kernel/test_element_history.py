from ncad.kernel.element_history import ElementHistory


def test_defaults_are_empty() -> None:
    hist = ElementHistory()
    assert hist.generated_from == {}
    assert hist.modified_from == {}
    assert hist.deleted == []


def test_fake_kernel_extrude_history_marks_caps_generated() -> None:
    from tests.kernel.fake_kernel import FakeKernel

    kernel = FakeKernel()
    face = kernel.polygon_face([(0, 0), (10, 0), (10, 10), (0, 10)], "XY")
    solid = kernel.extrude(face, 5.0)
    hist = kernel.history([face], solid)
    # The extrude output records lineage: at least one generated element from the input face,
    # and nothing deleted. (The Fake models a coarse but non-empty analytic lineage.)
    assert isinstance(hist, ElementHistory)
    assert hist.deleted == []
    assert len(hist.generated_from) >= 1
