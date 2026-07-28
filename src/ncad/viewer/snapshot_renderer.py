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
from pathlib import Path
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

# Named review angles for render_views: an author catches different defects from different sides
# (a frozen joint reads on iso, a mis-seated pin on front, a z-layer clash on top). Each is an
# (azimuth, elevation) around the model center; ``top`` is a straight-down view flagged separately.
# azimuth 0 looks along -X toward center (front); pi/2 looks along -Z; the eye elevation is a
# fraction of the fit distance above (+) or below (-) center.
_NAMED_VIEWS: dict[str, dict[str, float | bool]] = {
    "front": {"azimuth": 0.0, "elevation": 0.0},
    "right": {"azimuth": math.pi / 2.0, "elevation": 0.0},
    "iso": {"azimuth": math.pi / 4.0, "elevation": 0.5},
    "top": {"azimuth": 0.0, "elevation": 0.0, "top_down": True},
}


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

        # A bare model_path has parent Path("."), so this keeps the old "." fallback for that case.
        out_root = Path(out_dir) if out_dir else Path(model_path).parent
        base = out_root / Path(model_path).stem
        png_path, gif_path = f"{base}.png", f"{base}.gif"
        imageio.imwrite(png_path, still)
        # imageio's stub does not model a list[ndarray] of frames for the GIF writer; correct at
        # runtime (see the tests). Boundary-only ignore, per the third-party-stub policy.
        imageio.mimsave(  # pyrefly: ignore[no-matching-overload]
            gif_path, frames, duration=frame_duration, loop=0)
        logger.info("snapshot: wrote %s + %s (%d frames)", png_path, gif_path, self._frames)
        return {"png": png_path, "gif": gif_path}

    def render_views(self, model_path: str, out_dir: str | None = None,
                     views: tuple[str, ...] | None = None) -> dict[str, str]:
        """Render one framed still per named view; return ``{view: png_path}``.

        The multi-angle review packet for authoring: an author sees the model from several sides in
        one build so different defects (a frozen joint on iso, a mis-seated pin on front, a z-layer
        clash on top) are each catchable. Writes ``<stem>.<view>.png`` per view. ``views`` defaults
        to every entry in ``_NAMED_VIEWS``. Raises ValueError when the model has no geometry or a
        view name is unknown.
        """
        import imageio.v2 as imageio
        import pyrender
        import trimesh

        chosen = views or tuple(_NAMED_VIEWS)
        unknown = [v for v in chosen if v not in _NAMED_VIEWS]
        if unknown:
            raise ValueError(f"unknown view(s) {unknown}; known: {sorted(_NAMED_VIEWS)}")

        loaded = trimesh.load(model_path, force="scene")
        geometries = list(loaded.geometry.values())  # pyrefly: ignore[missing-attribute]
        if not geometries:
            raise ValueError(f"no renderable geometry in {model_path!r}")
        center, radius = _bounds_center_radius(loaded.bounds)
        distance = _fit_distance(radius)

        scene = pyrender.Scene(bg_color=list(_BG_COLOR), ambient_light=list(_AMBIENT))
        for geometry in geometries:
            scene.add(pyrender.Mesh.from_trimesh(geometry, smooth=True))
        camera = pyrender.PerspectiveCamera(yfov=_YFOV)
        camera_node = scene.add(camera, pose=_view_pose(center, distance, chosen[0]))
        light = pyrender.DirectionalLight(intensity=3.0)
        light_node = scene.add(light, pose=_view_pose(center, distance, chosen[0]))

        out_root = Path(out_dir) if out_dir else Path(model_path).parent
        out_root.mkdir(parents=True, exist_ok=True)
        base = out_root / Path(model_path).stem
        renderer = pyrender.OffscreenRenderer(self._width, self._height)
        out: dict[str, str] = {}
        try:
            for view in chosen:
                pose = _view_pose(center, distance, view)
                scene.set_pose(camera_node, pose)
                scene.set_pose(light_node, pose)  # key light rides the camera so no face goes black
                color, _ = renderer.render(scene)
                path = f"{base}.{view}.png"
                imageio.imwrite(path, color)
                out[view] = path
        finally:
            renderer.delete()
        logger.info("snapshot views: wrote %s", ", ".join(f"{v}={p}" for v, p in out.items()))
        return out

    def render_motion_frames(self, motion_path: str, assembly_path: str,
                             out_dir: str | None = None, samples: int = 4,
                             view: str = "iso") -> dict[int, str]:
        """Render posed stills at ``samples`` trajectory frames; return ``{frame_index: png_path}``.

        The observe->improve loop for MOTION: an author sees the mechanism mid-cycle (start,
        through, end), not just at rest, so a frozen joint or a mid-stroke clash is visible in a
        still. Loads each instance's glb (from ``assembly_path``'s instances[].part_glb, resolved
        beside it), applies that instance's per-frame placement from ``motion_path`` (row-major
        row-vector, metres - transposed for the column-vector renderer), and renders from a FIXED
        camera framed on the whole trajectory's extent so the frames are comparable. Writes
        ``<stem>.frameNNN.png``. Raises ValueError if the artifacts lack instances/frames/geometry.
        """
        import imageio.v2 as imageio
        import pyrender

        instances = _load_instances(assembly_path)      # {id: loaded trimesh scene of its glb}
        frames = _load_frames(motion_path)
        if not instances or not frames:
            raise ValueError(
                f"no posable geometry: {len(instances)} instances, {len(frames)} frames")
        indices = _sample_indices(len(frames), samples)
        center, radius = _trajectory_bounds(instances, frames, indices)
        distance = _fit_distance(radius)

        camera = pyrender.PerspectiveCamera(yfov=_YFOV)
        cam_pose = _view_pose(center, distance, view)
        out_root = Path(out_dir) if out_dir else Path(motion_path).parent
        out_root.mkdir(parents=True, exist_ok=True)
        base = out_root / Path(motion_path).stem.replace(".motion", "")
        renderer = pyrender.OffscreenRenderer(self._width, self._height)
        out: dict[int, str] = {}
        try:
            for idx in indices:
                scene = pyrender.Scene(bg_color=list(_BG_COLOR), ambient_light=list(_AMBIENT))
                placements = frames[idx].get("placements", {})
                for iid, geometries in instances.items():
                    pose = _pose_matrix(placements.get(iid))
                    for geometry in geometries:
                        scene.add(pyrender.Mesh.from_trimesh(geometry, smooth=True), pose=pose)
                scene.add(camera, pose=cam_pose)
                scene.add(pyrender.DirectionalLight(intensity=3.0), pose=cam_pose)
                color, _ = renderer.render(scene)
                path = f"{base}.frame{idx:03d}.png"
                imageio.imwrite(path, color)
                out[idx] = path
        finally:
            renderer.delete()
        logger.info("snapshot motion: wrote %d frame stills (%s)", len(out), base.name)
        return out

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


def _load_instances(assembly_path: str) -> dict:
    """{instance_id: [trimesh geometries]} for each instance's part glb, beside the json."""
    import json

    import trimesh

    with open(assembly_path, encoding="utf-8") as handle:
        assembly = json.load(handle)
    asm_dir = Path(assembly_path).parent
    out: dict[str, list] = {}
    for inst in assembly.get("instances", []):
        glb = inst.get("part_glb")
        iid = inst.get("id")
        if not glb or not iid:
            continue
        glb_path = asm_dir / glb
        if not glb_path.is_file():
            continue
        loaded = trimesh.load(str(glb_path), force="scene")
        geoms = list(loaded.geometry.values())  # pyrefly: ignore[missing-attribute]
        if geoms:
            out[iid] = geoms
    return out


def _load_frames(motion_path: str) -> list:
    """The motion trajectory's frame records (each ``{placements: {id: 4x4}}``)."""
    import json

    with open(motion_path, encoding="utf-8") as handle:
        return json.load(handle).get("frames", [])


def _sample_indices(frame_count: int, samples: int) -> list[int]:
    """``samples`` evenly-spaced frame indices across ``[0, frame_count)`` incl. first and last."""
    if frame_count <= 0:
        return []
    n = max(1, min(samples, frame_count))
    if n == 1:
        return [0]
    return sorted({round(i * (frame_count - 1) / (n - 1)) for i in range(n)})


def _pose_matrix(placement: list | None) -> np.ndarray:
    """A column-vector 4x4 from an ncad row-major row-vector placement (transpose the 3x3).

    ncad placements are row-vector (p_world = p_local . M): the rotation rows are basis images, so
    the renderer (column-vector M . p) needs the transpose; the translation stays m[3]. Identity
    when an instance is absent from the frame (a body the solver did not move).
    """
    if placement is None:
        return np.eye(4)
    m = placement
    return np.array([
        [m[0][0], m[1][0], m[2][0], m[3][0]],
        [m[0][1], m[1][1], m[2][1], m[3][1]],
        [m[0][2], m[1][2], m[2][2], m[3][2]],
        [0.0, 0.0, 0.0, 1.0]])


def _trajectory_bounds(instances: dict, frames: list,
                       indices: list[int]) -> tuple[np.ndarray, float]:
    """Center + radius over every sampled posed frame, so the fixed camera frames the sweep."""
    lows: list[np.ndarray] = []
    highs: list[np.ndarray] = []
    for idx in indices:
        placements = frames[idx].get("placements", {})
        for iid, geometries in instances.items():
            pose = _pose_matrix(placements.get(iid))
            for geometry in geometries:
                posed = geometry.bounds @ pose[:3, :3].T + pose[:3, 3]
                lows.append(posed.min(axis=0))
                highs.append(posed.max(axis=0))
    if not lows:
        return np.zeros(3), 1.0
    low = np.min(lows, axis=0)
    high = np.max(highs, axis=0)
    return _bounds_center_radius(np.array([low, high]))


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
    return _look_at(eye, center)


def _view_pose(center: np.ndarray, distance: float, view: str) -> np.ndarray:
    """A 4x4 camera pose for a named view (front/right/iso/top) looking at ``center``.

    Non-top views place the eye on a horizontal ring at ``azimuth`` (about +Z) raised by the view's
    ``elevation`` fraction of the distance; ``top`` looks straight down the -Z axis. All look at the
    model center, so the framing matches _orbit_pose's fit.
    """
    spec = _NAMED_VIEWS[view]
    if spec.get("top_down"):
        eye = center + np.array([0.0, 0.0, distance])
        return _look_at(eye, center, up=np.array([0.0, 1.0, 0.0]))
    azimuth = float(spec["azimuth"])
    elevation = float(spec["elevation"])
    eye = center + np.array([distance * math.cos(azimuth),
                             distance * math.sin(azimuth),
                             distance * elevation])
    return _look_at(eye, center)


def _look_at(eye: np.ndarray, center: np.ndarray,
             up: np.ndarray | None = None) -> np.ndarray:
    """A 4x4 camera pose whose -Z looks from ``eye`` to ``center`` (pyrender/OpenGL convention)."""
    world_up = up if up is not None else np.array([0.0, 0.0, 1.0])
    forward = center - eye
    forward = forward / np.linalg.norm(forward)
    right = np.cross(forward, world_up)
    right = right / np.linalg.norm(right)
    cam_up = np.cross(right, forward)
    pose = np.eye(4)
    pose[:3, 0] = right
    pose[:3, 1] = cam_up
    pose[:3, 2] = -forward
    pose[:3, 3] = eye
    return pose
