from ncad.assembly.interference_classifier import InterferenceClassifier


def test_clearance_when_distance_positive() -> None:
    assert InterferenceClassifier().classify(4.0, 0.0) == ("clearance", 4.0)


def test_interfering_when_touching_with_shared_volume() -> None:
    assert InterferenceClassifier().classify(0.0, 500.0) == ("interfering", 500.0)


def test_touching_when_zero_distance_no_shared_volume() -> None:
    assert InterferenceClassifier().classify(0.0, 0.0) == ("touching", 0.0)


def test_tolerances_are_respected() -> None:
    c = InterferenceClassifier()
    # A hair of distance under tol still counts as contact, not clearance.
    assert c.classify(1e-9, 0.0)[0] == "touching"
    # A hair of shared volume under tol is not a real interference.
    assert c.classify(0.0, 1e-9)[0] == "touching"
