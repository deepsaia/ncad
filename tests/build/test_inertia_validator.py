"""InertiaValidator flags physically-impossible inertia tensors; passes valid ones."""

from ncad.build.inertia_validator import InertiaValidator
from ncad.diagnostics import codes


def _valid_box():
    # Centroidal tensor of a solid box (any positive, triangle-satisfying, diagonal PSD matrix).
    return {"matrix": [[13600.0, 0, 0], [0, 43600.0, 0], [0, 0, 50000.0]],
            "principal": [50000.0, 43600.0, 13600.0]}


def test_valid_tensor_passes():
    assert InertiaValidator().check("blk", "body/0", 0.0094, _valid_box()) == []


def test_absent_inertia_is_skipped():
    assert InertiaValidator().check("blk", "body/0", None, None) == []


def test_non_positive_mass_flagged():
    diags = InertiaValidator().check("blk", "body/0", 0.0, _valid_box())
    assert len(diags) == 1
    assert diags[0].code == codes.INVALID_INERTIA
    assert diags[0].severity == "warning"
    assert "mass" in diags[0].message


def test_negative_diagonal_flagged():
    bad = {"matrix": [[-1.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]], "principal": [10, 10, -1]}
    diags = InertiaValidator().check("blk", "body/0", 1.0, bad)
    assert diags and diags[0].code == codes.INVALID_INERTIA
    assert "positive" in diags[0].message


def test_triangle_inequality_violation_flagged():
    # Ixx (100) > Iyy + Izz (10 + 10): impossible for a real mass distribution.
    bad = {"matrix": [[100.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]], "principal": [100, 10, 10]}
    diags = InertiaValidator().check("blk", "body/0", 1.0, bad)
    assert diags and "triangle" in diags[0].message


def test_non_psd_offdiagonal_flagged():
    # Positive diagonal + triangle OK, but a huge product-of-inertia term makes it indefinite.
    bad = {"matrix": [[10.0, 100.0, 0], [100.0, 10.0, 0], [0, 0, 10.0]],
           "principal": [110, 10, -90]}
    diags = InertiaValidator().check("blk", "body/0", 1.0, bad)
    assert diags and "positive-semidefinite" in diags[0].message


def test_malformed_matrix_flagged():
    diags = InertiaValidator().check("blk", "body/0", 1.0, {"matrix": [[1, 2], [3, 4]]})
    assert diags and "3x3" in diags[0].message
