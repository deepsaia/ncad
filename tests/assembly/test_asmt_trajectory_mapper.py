"""Unit tests for AsmtTrajectoryMapper: pyondsel Trajectory -> ncad per-frame placements."""

import math
from dataclasses import dataclass, field

from ncad.assembly.asmt_trajectory_mapper import AsmtTrajectoryMapper


@dataclass
class _FakePart:
    positions: list = field(default_factory=list)
    bryant_angles: list = field(default_factory=list)

    def frame_count(self):
        return min(len(self.positions), len(self.bryant_angles))


@dataclass
class _FakeTrajectory:
    times: list = field(default_factory=list)
    parts: dict = field(default_factory=dict)


_IDENTITY = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def test_frames_align_to_driver_values_and_bake_translation():
    # A part translating in metres; the mapper should surface the translation in the last row.
    traj = _FakeTrajectory(
        times=[0.0, 0.5, 1.0],
        parts={"/Rig/slider": _FakePart(
            positions=[(0.0, 0.0, 0.0), (0.01, 0.0, 0.0), (0.02, 0.0, 0.0)],
            bryant_angles=[(0.0, 0.0, 0.0)] * 3)})
    frames = AsmtTrajectoryMapper().to_frames(
        traj, "Rig", [{"id": "slider"}], {"slider": _IDENTITY},
        values=[0.0, 6.0, 12.0], to_metres=0.001)
    assert len(frames) == 3
    assert frames[1]["driver_value"] == 6.0
    assert math.isclose(frames[2]["placements"]["slider"][3][0], 0.02, abs_tol=1e-9)


def test_bryant_z_rotation_reconstructs_heading():
    # A 90deg Bryant-Z rotation maps the part's local +X to world +Y.
    traj = _FakeTrajectory(
        times=[0.0], parts={"/Rig/arm": _FakePart(
            positions=[(0.0, 0.0, 0.0)], bryant_angles=[(0.0, 0.0, math.pi / 2)])})
    frames = AsmtTrajectoryMapper().to_frames(
        traj, "Rig", [{"id": "arm"}], {"arm": _IDENTITY}, values=[90.0], to_metres=0.001)
    row0 = frames[0]["placements"]["arm"][0]  # image of local +X
    assert math.isclose(row0[0], 0.0, abs_tol=1e-9)
    assert math.isclose(row0[1], 1.0, abs_tol=1e-9)


def test_instance_missing_from_trajectory_keeps_rest_placement():
    traj = _FakeTrajectory(
        times=[0.0], parts={"/Rig/arm": _FakePart(
            positions=[(0.0, 0.0, 0.0)], bryant_angles=[(0.0, 0.0, 0.0)])})
    rest = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0], [7000.0, 0.0, 0.0, 1.0]]
    frames = AsmtTrajectoryMapper().to_frames(
        traj, "Rig", [{"id": "arm"}, {"id": "ground"}],
        {"arm": _IDENTITY, "ground": rest}, values=[0.0], to_metres=0.001)
    # ground is not in the trajectory -> keeps its rest pose, baked to metres (7 m).
    assert math.isclose(frames[0]["placements"]["ground"][3][0], 7.0, abs_tol=1e-9)
