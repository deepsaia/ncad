import math

import pytest

from ncad.build.builder import Builder
from ncad.ops.op_registry import OpRegistry
from tests.kernel.fake_kernel import FakeKernel


def test_revolve_resolves_profile_ref_not_adjacent_shape():
    # A base plate, an UNRELATED sketch, then a revolve whose profile points at the ring
    # sketch by id (NOT the immediately preceding feature). Before the fix, revolve would
    # revolve the wrong (adjacent) shape; with profile resolved it revolves the ring.
    part = {"profile": "solid", "features": [
        {"id": "ring_sk", "op": "sketch", "plane": "XY",
         "elements": [{"id": "r", "type": "polygon",
                       "points": [[8, 0], [12, 0], [12, 2], [8, 2]]}]},
        {"id": "base_sk", "op": "sketch", "plane": "XY",
         "elements": [{"id": "b", "type": "rectangle", "w": 40, "h": 40}]},
        {"id": "base", "op": "extrude", "profile": "base_sk", "distance": 4},
        {"id": "ring", "op": "revolve", "profile": "ring_sk", "axis": "Y"},
    ]}
    result = Builder(FakeKernel(), OpRegistry.with_defaults()).build_part(part)
    assert result.shape is not None
    assert not any(i.level == "error" for i in result.issues)
    # Pappus volume of the ring (area 8, centroid r=10 about Y): 8 * 2*pi*10.
    assert result.shape.volume_val == pytest.approx(8 * 2 * math.pi * 10, rel=1e-9)
