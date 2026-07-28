"""Pure helpers for motion-frame snapshots: frame sampling + the row-major->column pose flip."""

import numpy as np

from ncad.viewer.snapshot_renderer import _pose_matrix, _sample_indices


def test_sample_indices_spans_first_and_last():
    idx = _sample_indices(36, 4)
    assert idx[0] == 0 and idx[-1] == 35
    assert len(idx) == 4
    assert idx == sorted(idx)


def test_sample_indices_clamps_to_frame_count():
    # asking for more samples than frames yields at most one per frame
    assert _sample_indices(3, 10) == [0, 1, 2]


def test_sample_indices_single_and_empty():
    assert _sample_indices(10, 1) == [0]
    assert _sample_indices(0, 4) == []


def test_pose_matrix_identity_when_absent():
    assert np.allclose(_pose_matrix(None), np.eye(4))


def test_pose_matrix_transposes_rotation_and_keeps_translation():
    # ncad row-major row-vector: rotation rows are basis images; renderer wants columns (transpose).
    # a 90deg rotation about Z, translation (5, 6, 7) mm-in-metres.
    import math
    c, s = math.cos(math.radians(90)), math.sin(math.radians(90))
    row_major = [[c, s, 0, 0], [-s, c, 0, 0], [0, 0, 1, 0], [5.0, 6.0, 7.0, 1.0]]
    m = _pose_matrix(row_major)
    # the renderer matrix's 3x3 must be the TRANSPOSE of the row-major 3x3
    assert np.allclose(m[:3, :3], np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]))
    # translation lands in the 4th column
    assert np.allclose(m[:3, 3], [5.0, 6.0, 7.0])
    assert np.allclose(m[3], [0, 0, 0, 1])
