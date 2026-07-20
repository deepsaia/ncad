"""Report a mechanism's mobility: the planar Gruebler/Kutzbach count + the solver's actual free DoF.

A legibility layer (the 3D analogue of the sketch-DoF status): the nominal Gruebler mobility count
from the joint graph next to the STATIC solve's rest-pose free DoF.

The mechanisms here are PLANAR, so the count is the planar Gruebler mobility
M = 3(n-1) - sum(constraints_per_joint), where n counts links INCLUDING ground. A lower pair
(revolute, slider - one planar freedom) removes 2 planar DoF; a higher pair (slot / point-on-line -
line contact) removes 1.

``gruebler`` is the mechanism's MOBILITY (how many independent motions it has); a value of 1 is the
classic single-DoF mechanism a lone driver animates. ``solver`` is the static assembly solve's free
DoF at the REST pose, which is 0 for a well-constrained rest (the mate network consumes every joint
freedom to fix one pose) - that is expected and is NOT the mechanism's mobility. So ``status`` is
"mobile" when ``gruebler`` >= 1 (the mechanism can move), else "locked". Both counts are reported;
a gruebler-vs-(solver + driven-DoF) discrepancy would flag an over/under-constrained mechanism.
One class.
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

    def report(self, joints: list[dict], instance_count: int, solver_dof: int,
               coupling_count: int = 0) -> dict:
        """Return {gruebler, solver, status} for a planar mechanism.

        :param joints: the assembly joints (each a dict with a ``type``).
        :param instance_count: number of links INCLUDING ground.
        :param solver_dof: the static assembly solve's rest-pose free DoF (0 for a well-constrained
            rest; reported for context, NOT the mobility).
        :param coupling_count: number of couplings (gear/belt/rack_pinion/cam). Each is a HIGHER
            pair / one scalar constraint relating two joints' DoF, so it removes 1 planar DoF (a cam
            contact, a gear ratio). Without this a coupled 2-joint chain reads as 2-DoF, not 1.
        """
        removed = sum(_PLANAR_CONSTRAINTS.get(j.get("type") or "", _DEFAULT_CONSTRAINT)
                      for j in joints)
        gruebler = 3 * max(instance_count - 1, 0) - removed - coupling_count
        status = "mobile" if gruebler >= 1 else "locked"
        return {"gruebler": gruebler, "solver": solver_dof, "status": status}
