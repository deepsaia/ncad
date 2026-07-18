"""Report a mechanism's mobility: the planar Gruebler/Kutzbach count + the solver's actual free DoF.

A legibility layer (the 3D analogue of the sketch-DoF status): the nominal Gruebler count from the
joint graph next to the constraint solver's authoritative free DoF. When they disagree that is
itself informative (a special-geometry overconstraint or a redundant loop).

The gates here are PLANAR mechanisms, so the count is the planar Gruebler mobility
M = 3(n-1) - sum(constraints_per_joint), where n counts links INCLUDING ground. A lower pair
(revolute, slider - one planar freedom) removes 2 planar DoF; a higher pair (slot / point-on-line -
line contact) removes 1. ``solver`` is the assembly solve's free DoF (authoritative); ``status`` is
"mobile" when solver >= 1 else "locked". One class.
"""

# Planar DoF each joint type removes. Lower pairs remove 2 (leave 1 planar freedom); higher pairs
# (line/slot contact) remove 1; a fixed joint removes all 3. Unknown types default to a lower pair.
_PLANAR_CONSTRAINTS = {
    "revolute": 2, "slider": 2, "cylindrical": 2, "screw": 2,
    "slot": 1, "point_on_line": 1,
    "fixed": 3,
}
_DEFAULT_CONSTRAINT = 2


class MotionMobility:
    """Computes the planar Gruebler mobility and pairs it with the solver's free DoF."""

    def report(self, joints: list[dict], instance_count: int, solver_dof: int) -> dict:
        """Return {gruebler, solver, status} for a planar mechanism.

        :param joints: the assembly joints (each a dict with a ``type``).
        :param instance_count: number of links INCLUDING ground.
        :param solver_dof: the constraint solver's actual free DoF (authoritative).
        """
        removed = sum(_PLANAR_CONSTRAINTS.get(j.get("type") or "", _DEFAULT_CONSTRAINT)
                      for j in joints)
        gruebler = 3 * max(instance_count - 1, 0) - removed
        status = "mobile" if solver_dof >= 1 else "locked"
        return {"gruebler": gruebler, "solver": solver_dof, "status": status}
