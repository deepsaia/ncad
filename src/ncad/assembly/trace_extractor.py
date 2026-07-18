"""Extract trace curves (the world path a point sweeps over a motion) from a solved trajectory.

A trace names a fixed local point on a moving instance; its trace curve is that point's world
position at each frame. Pure post-processing over the trajectory (no re-solve, no kernel): resolve
the local point, apply each frame's placement (via motion_point_sampler), and collect the polyline.

The polyline is emitted in METRES (world), one vertex per frame in frame order, so the viewer (which
works in metres) draws it directly. A frame missing the instance is skipped (no vertex). One class.
"""

from ncad.assembly.motion_point_sampler import sample_world_points


class TraceExtractor:
    """Turns trace specs + a trajectory into per-trace world polylines (metres)."""

    def extract(self, trace_specs: list[dict], frames: list[dict], local_frames: dict,
                to_metres: float) -> list[dict]:
        """Return [{id, instance, polyline}] where polyline is world [x,y,z] metres per frame."""
        traces: list[dict] = []
        for spec in trace_specs:
            mm_points = sample_world_points(spec, frames, local_frames, to_metres)
            polyline = [[p[0] * to_metres, p[1] * to_metres, p[2] * to_metres]
                        for p in mm_points if p is not None]
            traces.append({"id": spec["id"], "instance": spec["instance"], "polyline": polyline})
        return traces
