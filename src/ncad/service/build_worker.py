"""The picklable build entrypoint that runs INSIDE a spawn pool worker, plus its progress writer.

A ProcessPoolExecutor pickles the callable + args, so this MUST be a module-level function (the
old ``BuildServiceFactory._make_builder`` bound method could not pickle). The worker constructs a
fresh BuildService (which imports the kernel lazily, per-process, sidestepping OCCT/gmsh global
state), dispatches by ``kind``, and reports stage progress to a per-job JSON file the parent polls.
Build failures are RETURNED as data, never raised, so the pool Future always resolves cleanly.
"""

import base64
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

STAGES: dict[str, list[str]] = {
    "build": ["building", "publishing"],
    "assemble": ["building parts", "solving mates", "interference/BOM/mass", "publishing"],
    "motion": ["building assembly", "solving motion", "interference", "publishing"],
    "physics": ["building assembly", "deriving robot", "exporting meshes", "publishing"],
    "analyze": ["meshing", "writing deck", "solving (CalculiX)", "reading results"],
}


class ProgressWriter:
    """Writes a per-job progress JSON file atomically as the worker advances through stages."""

    def __init__(self, progress_path: str, kind: str) -> None:
        """:param progress_path: file the parent's status handler reads.
        :param kind: build kind, selecting the stage list (empty list for job-less kinds).
        """
        self._path = progress_path
        self._stages = STAGES.get(kind, [])

    def stage(self, name: str, message: str) -> None:
        """Record advancing to stage ``name`` (1-based done count) with a human ``message``."""
        done = (self._stages.index(name) + 1) if name in self._stages else 0
        payload = {"stage": name, "stages_done": done,
                   "stages_total": len(self._stages), "message": message}
        tmp = f"{self._path}.tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        os.replace(tmp, self._path)


def run_build(kind: str, payload: dict, models_dir: str, examples_dir: str,
              progress_path: str) -> dict:
    """Run one build of ``kind`` in this worker process; return a result/failure dict (never raise).

    :return: ``{"ok": True, "result": <dict>}`` on success, else ``{"ok": False, "error": <str>}``.
    """
    from ncad.viewer.build_service import BuildError
    from ncad.viewer.viewer_server import BuildServiceFactory

    try:
        service = BuildServiceFactory().create(examples_dir, models_dir)
        result = _dispatch(service, kind, payload, ProgressWriter(progress_path, kind))
        return {"ok": True, "result": result}
    except BuildError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - cross-process boundary: return, never raise
        logger.exception("build worker failed for kind=%s", kind)
        return {"ok": False, "error": f"internal build error: {exc}"}


def _dispatch(service: Any, kind: str, payload: dict, progress: ProgressWriter) -> dict:
    """Call the right BuildService method for ``kind``; emit a leading + trailing stage."""
    if kind == "build":
        progress.stage("building", f"{payload['spec']} - building")
        result = service.build(payload["spec"])
        progress.stage("publishing", f"{payload['spec']} - publishing")
        return result
    if kind == "assemble":
        progress.stage("building parts", f"{payload['spec']} - building parts")
        return service.assemble(payload["spec"])
    if kind == "motion":
        progress.stage("building assembly", f"{payload['spec']} - building assembly")
        return service.build_motion(payload["spec"])
    if kind == "physics":
        progress.stage("building assembly", f"{payload['spec']} - building assembly")
        return service.build_physics(payload["spec"])
    if kind == "analyze":
        progress.stage("meshing", f"{payload['spec']} - meshing")
        return service.analyze(payload["spec"])
    if kind == "validate":
        return service.validate(payload["spec"])
    if kind == "robot-collide":
        return service.check_robot_collision(payload["name"], payload.get("pose", {}))
    if kind == "export":
        download_name, content_type, data = service.export_model(
            payload["name"], payload["kind"], payload["format"])
        return {"download_name": download_name, "content_type": content_type,
                "data_b64": base64.b64encode(data).decode("ascii")}
    raise ValueError(f"unknown build kind {kind!r}")
