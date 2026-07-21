"""GeometryFacts collects a part's bbox / counts / per-body volume+centroid (+ optional mass)."""

import pytest

from ncad.build.geometry_facts import GeometryFacts
from ncad.kernel.build123d_kernel import Build123dKernel

pytestmark = pytest.mark.slow


def _box(w=20.0, d=10.0, h=6.0):
    import build123d as b3d
    return b3d.Solid.make_box(w, d, h)


def test_bbox_and_size_and_center():
    facts = GeometryFacts(Build123dKernel()).collect(_box())
    bbox = facts["bbox"]
    assert bbox["min"] == [0.0, 0.0, 0.0]
    assert bbox["max"] == [20.0, 10.0, 6.0]
    assert bbox["size"] == [20.0, 10.0, 6.0]
    assert bbox["center"] == [10.0, 5.0, 3.0]


def test_topology_counts():
    facts = GeometryFacts(Build123dKernel()).collect(_box())
    assert facts["counts"] == {"solids": 1, "faces": 6, "edges": 12}


def test_body_volume_and_centroid():
    facts = GeometryFacts(Build123dKernel()).collect(_box())
    bodies = facts["bodies"]
    assert len(bodies) == 1
    assert round(bodies[0]["volume"], 3) == 1200.0
    assert bodies[0]["centroid"] == [10.0, 5.0, 3.0]
    # No mass_properties passed -> no mass/inertia keys.
    assert "mass" not in bodies[0]


def test_mass_properties_are_merged_when_supplied():
    # Caller supplies a MassCalculator-shaped dict; the facts merge it per body + expose totals.
    mp = {"bodies": [{"id": "body/0", "material": "steel", "density": 7850,
                      "mass": 0.00942, "inertia": {"matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                                                   "principal": [1, 1, 1]}}],
          "total": {"mass": 0.00942, "volume": 1200.0, "cog": (10.0, 5.0, 3.0)}}
    facts = GeometryFacts(Build123dKernel()).collect(_box(), mass_properties=mp)
    body = facts["bodies"][0]
    assert body["material"] == "steel"
    assert body["mass"] == 0.00942
    assert body["inertia"]["principal"] == [1, 1, 1]
    assert facts["totals"]["mass"] == 0.00942
