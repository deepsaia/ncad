"""Machine-readable diagnostic codes: a closed, stable set an agent can branch on.

Each constant's value is its wire code (snake_case). Grouped by stage for readability; the value is
what appears in a Diagnostic and in the JSON an agent consumes. Add a code here (never inline a bare
string) so the taxonomy stays enumerable.
"""

# schema stage - one code for the whole layer; the jsonschema message + location carry the detail
# (a malformed-field fix is the same regardless of the failing keyword, so no type/enum split).
SCHEMA = "schema"

# semantic stage (references, ids, dependencies)
DUPLICATE_ID = "duplicate_id"
UNKNOWN_REFERENCE = "unknown_reference"
FORWARD_REFERENCE = "forward_reference"
DEPENDENCY_CYCLE = "dependency_cycle"
UNRESOLVED_CONNECTOR = "unresolved_connector"
MISSING_INSTANCE_PART = "missing_instance_part"
UNKNOWN_JOINT_TYPE = "unknown_joint_type"
DRIVER_JOINT_MISSING = "driver_joint_missing"
DRIVER_JOINT_NOT_DRIVABLE = "driver_joint_not_drivable"
MOTION_ASSEMBLY_MISSING = "motion_assembly_missing"
COUPLING_PRIMARY_MISMATCH = "coupling_primary_mismatch"

# build / motion stages (geometry + solve, mapped from BuildIssue / motion dicts)
GEOMETRY_FAILED = "geometry_failed"
SKETCH_UNDERCONSTRAINED = "sketch_underconstrained"
MOTION_SOLVE_FAILED = "motion_solve_failed"
# a part built as multiple DISJOINT solids (floating pieces). Info-only: often the "floating bodies"
# authoring bug, but legitimate for a multibody part - the diagnostic reports, makes no judgment.
DISCONNECTED_SOLID = "disconnected_solid"
# a body's mass-moment-of-inertia tensor is not physically realizable (non-positive mass/diagonal,
# fails the triangle inequality, or is not positive-semidefinite) - flags a bad density/geometry.
INVALID_INERTIA = "invalid_inertia"
# a manufacturability (DFM) preflight rule was violated (warning) or could not be evaluated for lack
# of a fact (info/need-more-info). The Diagnostic message names the cited rule + the process.
DFM_VIOLATION = "dfm_violation"
