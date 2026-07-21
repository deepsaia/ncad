"""Generate a pipe tee as a buildable ncad part document (a run + a branch, both bored).

A tee is a straight run with a branch at 90 degrees to its midpoint. The run is a cylinder along X
(centred on the origin) and the branch a cylinder along +Z; they union into the outer body, then the
matching inner cylinders are cut to bore both the run and the branch through. Emitting a part
document keeps it first-class + editable. Pure: same dimensions -> identical document. One class.

Dimensions (mm): ``outer_diameter``, ``wall_thickness``, ``run_length`` (full run along X),
``branch_length`` (branch height from the run centre along +Z).
"""


class TeeGenerator:
    """Emits a pipe-tee part document: a bored run cylinder unioned with a bored branch cylinder."""

    def generate(self, part_name: str, dimensions: dict) -> dict:
        """Return a one-part ncad document for the tee named ``part_name``."""
        outer_d = float(dimensions["outer_diameter"])
        wall = float(dimensions["wall_thickness"])
        run_length = float(dimensions["run_length"])
        branch_length = float(dimensions["branch_length"])
        bore_d = outer_d - 2.0 * wall
        run_offset = -run_length / 2.0   # centre the X-run on the origin
        return {
            "units": "mm",
            "parts": {
                part_name: {
                    "profile": "solid",
                    "features": [
                        # Outer body: run along X (plane YZ) + branch along Z (plane XY), unioned.
                        {"id": "run_outer", "op": "primitive", "kind": "cylinder", "plane": "YZ",
                         "plane_offset": run_offset, "d": outer_d, "h": run_length, "at": [0, 0]},
                        {"id": "branch_outer", "op": "primitive", "kind": "cylinder", "plane": "XY",
                         "plane_offset": 0.0, "d": outer_d, "h": branch_length, "at": [0, 0]},
                        {"id": "body", "op": "boolean", "operation": "union",
                         "target": "run_outer", "tool": "branch_outer"},
                        # Bore the run, then the branch.
                        {"id": "run_bore", "op": "primitive", "kind": "cylinder", "plane": "YZ",
                         "plane_offset": run_offset, "d": bore_d, "h": run_length, "at": [0, 0]},
                        {"id": "branch_bore", "op": "primitive", "kind": "cylinder", "plane": "XY",
                         "plane_offset": 0.0, "d": bore_d, "h": branch_length, "at": [0, 0]},
                        {"id": "bore_run", "op": "boolean", "operation": "cut",
                         "target": "body", "tool": "run_bore"},
                        {"id": "bore_branch", "op": "boolean", "operation": "cut",
                         "target": "bore_run", "tool": "branch_bore"},
                    ],
                }
            },
        }
