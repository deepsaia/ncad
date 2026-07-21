"""Render a built model to a review packet: a framed PNG plus an orbit GIF.

The agent-facing visual gate. After any geometry change an agent (or a human) needs to *see* the
result, not just trust that it built; this renders a mesh artifact (GLB/STL/OBJ/PLY/3MF, anything
trimesh loads) offscreen via pyrender so no browser or display is required. The camera is framed on
the model's bounding box, so the packet is unit- and scale-agnostic and always centers the part.

Single responsibility: turn one model file into image sidecars. The render is deterministic for a
given model + settings (fixed light, fixed orbit start), so a snapshot diff is a stable review
signal. Emits ``<model>.png`` (a representative 3/4 view) and ``<model>.gif`` (a full orbit) beside
the model unless another output directory is given.
"""

import logging
import math
import os
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Framing + look constants. A 45-degree vertical FOV with the eye pulled back so the bounding
# sphere fits with margin; the orbit rings the model at a fixed elevation for a readable 3/4 view.
_YFOV = math.pi / 4.0
_FIT_MARGIN = 1.4
_ELEVATION = 0.35          # fraction of the fit distance the eye sits below/above center
_BG_COLOR = (0.10, 0.10, 0.12, 1.0)
_AMBIENT = (0.30, 0.30, 0.30)
_PNG_AZIMUTH = math.pi / 4.0   # the still is a 3/4 view, not a face-on one


class SnapshotRenderer:
    """Renders a model file to a framed still + an orbit GIF (offscreen, no display)."""

    def __init__(self, width: int = 800, height: int = 600, frames: int = 24) -> None:
        self._width = width
        self._height = height
        self._frames = frames

    def render(self, model_path: str, out_dir: str | None = None,
               frame_duration: float = 0.08) -> dict[str, str]:
        """Render ``model_path`` to ``<stem>.png`` + ``<stem>.gif``; return the written paths.

        ``out_dir`` defaults to the model's own directory. ``frame_duration`` is the GIF frame time
        in seconds. Raises ValueError when the model has no renderable geometry.
        """
        import imageio.v2 as imageio
        import pyrender
        import trimesh

        # force="scene" always yields a trimesh.Scene, so .geometry is present at runtime; the
        # trimesh stub types load() as a union, so this reads as a missing attribute to pyrefly.
        loaded = trimesh.load(model_path, force="scene")
        geometries = list(loaded.geometry.values())  # pyrefly: ignore[missing-attribute]
        if not geometries:
            raise ValueError(f"no renderable geometry in {model_path!r}")
        center, radius = _bounds_center_radius(loaded.bounds)

        scene = pyrender.Scene(bg_color=list(_BG_COLOR), ambient_light=list(_AMBIENT))
        for geometry in geometries:
            scene.add(pyrender.Mesh.from_trimesh(geometry, smooth=True))
        camera = pyrender.PerspectiveCamera(yfov=_YFOV)
        distance = _fit_distance(radius)
        camera_node = scene.add(camera, pose=_orbit_pose(center, distance, _PNG_AZIMUTH))
        # A key light rides with the camera's opening angle so the part is lit from the front-side
        # regardless of orbit; ambient fills the shadows so no face reads as pure black.
        light = pyrender.DirectionalLight(intensity=3.0)
        scene.add(light, pose=_orbit_pose(center, distance, _PNG_AZIMUTH + 0.6))

        renderer = pyrender.OffscreenRenderer(self._width, self._height)
        try:
            still = self._render_at(renderer, scene, camera_node, center, distance, _PNG_AZIMUTH)
            frames = [self._render_at(renderer, scene, camera_node, center, distance,
                                      i / self._frames * 2.0 * math.pi)
                      for i in range(self._frames)]
        finally:
            renderer.delete()

        base = os.path.join(out_dir or os.path.dirname(model_path) or ".",
                            os.path.splitext(os.path.basename(model_path))[0])
        png_path, gif_path = f"{base}.png", f"{base}.gif"
        imageio.imwrite(png_path, still)
        # imageio's stub does not model a list[ndarray] of frames for the GIF writer; correct at
        # runtime (see the tests). Boundary-only ignore, per the third-party-stub policy.
        imageio.mimsave(  # pyrefly: ignore[no-matching-overload]
            gif_path, frames, duration=frame_duration, loop=0)
        logger.info("snapshot: wrote %s + %s (%d frames)", png_path, gif_path, self._frames)
        return {"png": png_path, "gif": gif_path}

    def _render_at(self, renderer: Any, scene: Any, camera_node: Any, center: np.ndarray,
                   distance: float, azimuth: float) -> np.ndarray:
        """Pose the camera at ``azimuth`` around ``center`` and return the rendered RGB frame."""
        scene.set_pose(camera_node, _orbit_pose(center, distance, azimuth))
        color, _ = renderer.render(scene)
        return color


def _bounds_center_radius(bounds: np.ndarray) -> tuple[np.ndarray, float]:
    """Center point and bounding-sphere radius from a trimesh ``(2, 3)`` bounds array."""
    low, high = np.asarray(bounds[0]), np.asarray(bounds[1])
    center = (low + high) / 2.0
    radius = float(np.linalg.norm(high - low)) / 2.0
    return center, max(radius, 1e-6)


def _fit_distance(radius: float) -> float:
    """Eye distance that fits a sphere of ``radius`` in the vertical FOV with margin."""
    return radius / math.tan(_YFOV / 2.0) * _FIT_MARGIN


def _orbit_pose(center: np.ndarray, distance: float, azimuth: float) -> np.ndarray:
    """A 4x4 camera pose orbiting ``center`` at ``azimuth`` (radians) and a fixed elevation.

    The camera looks at ``center`` with world +Z up; the eye rings the model in the XY-ish plane
    dropped below center by ``_ELEVATION`` of the distance, giving a readable 3/4 view.
    """
    eye = center + np.array([distance * math.cos(azimuth),
                             -distance * _ELEVATION,
                             distance * math.sin(azimuth)])
    forward = center - eye
    forward = forward / np.linalg.norm(forward)
    world_up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    right = right / np.linalg.norm(right)
    up = np.cross(right, forward)
    pose = np.eye(4)
    pose[:3, 0] = right
    pose[:3, 1] = up
    pose[:3, 2] = -forward
    pose[:3, 3] = eye
    return pose
