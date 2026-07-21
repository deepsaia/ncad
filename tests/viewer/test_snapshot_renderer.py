"""SnapshotRenderer writes a framed PNG + orbit GIF with real model content (offscreen)."""

import numpy as np
import pytest

from ncad.kernel.build123d_kernel import Build123dKernel
from ncad.viewer.snapshot_renderer import (
    SnapshotRenderer,
    _bounds_center_radius,
    _fit_distance,
    _orbit_pose,
)

pytestmark = pytest.mark.slow


def _glb(tmp_path) -> str:
    kernel = Build123dKernel()
    cyl = kernel.cylinder((0, 0, 0), "Z", diameter=20.0, length=30.0)
    path = str(tmp_path / "part.glb")
    kernel.export(cyl, path)
    return path


def test_render_writes_png_and_gif(tmp_path) -> None:
    import imageio.v2 as imageio

    out = SnapshotRenderer(width=320, height=240, frames=6).render(_glb(tmp_path))

    assert out["png"].endswith("part.png") and out["gif"].endswith("part.gif")
    still = imageio.imread(out["png"])
    assert still.shape[:2] == (240, 320)
    # The framed part occupies a real fraction of the frame (not an empty background render).
    background = np.array([26, 26, 31])
    model_pixels = (np.abs(still[:, :, :3].astype(int) - background).sum(2) > 30).mean()
    assert model_pixels > 0.02


def test_render_defaults_beside_model(tmp_path) -> None:
    path = _glb(tmp_path)
    out = SnapshotRenderer(frames=4).render(path)
    assert out["png"] == str(tmp_path / "part.png")
    assert (tmp_path / "part.png").is_file() and (tmp_path / "part.gif").is_file()


def test_empty_scene_raises(tmp_path) -> None:
    empty = tmp_path / "empty.glb"
    empty.write_bytes(b"glTF\x02\x00\x00\x00")  # not a loadable model
    with pytest.raises((ValueError, Exception)):
        SnapshotRenderer(frames=2).render(str(empty))


def test_orbit_pose_looks_at_center() -> None:
    # The camera's -Z (view forward) must point from the eye toward the model center.
    center = np.array([1.0, 2.0, 3.0])
    pose = _orbit_pose(center, distance=10.0, azimuth=0.0)
    eye = pose[:3, 3]
    forward = -pose[:3, 2]
    to_center = center - eye
    to_center = to_center / np.linalg.norm(to_center)
    assert np.allclose(forward, to_center, atol=1e-6)


def test_fit_distance_scales_with_radius() -> None:
    assert _fit_distance(10.0) > _fit_distance(1.0)
    center, radius = _bounds_center_radius(np.array([[-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]]))
    assert np.allclose(center, [0.0, 0.0, 0.0])
    assert radius == pytest.approx(np.linalg.norm([2.0, 2.0, 2.0]) / 2.0)
