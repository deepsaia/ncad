"""Op-dispatch registry: feature ``op`` name to builder callable.

Adding an operation is registering an op; this is the generalization of v1's
``roof_builders[kind]`` pattern. Each op is a class with a ``build``
method matching the uniform op signature; the registry stores the bound ``build``
methods so the executor can dispatch by op name.
"""

from collections.abc import Callable

from ncad.ops.boolean_op import BooleanOp
from ncad.ops.chamfer_op import ChamferOp
from ncad.ops.datum_axis_op import DatumAxisOp
from ncad.ops.datum_plane_op import DatumPlaneOp
from ncad.ops.defeature_op import DefeatureOp
from ncad.ops.draft_op import DraftOp
from ncad.ops.extrude_op import ExtrudeOp
from ncad.ops.feature_mirror_op import FeatureMirrorOp
from ncad.ops.feature_pattern_op import FeaturePatternOp
from ncad.ops.fillet_op import FilletOp
from ncad.ops.groove_op import GrooveOp
from ncad.ops.hole_op import HoleOp
from ncad.ops.import_op import ImportOp
from ncad.ops.loft_op import LoftOp
from ncad.ops.mirror_op import MirrorOp
from ncad.ops.move_face_op import MoveFaceOp
from ncad.ops.offset_face_op import OffsetFaceOp
from ncad.ops.pattern_op import PatternOp
from ncad.ops.pocket_op import PocketOp
from ncad.ops.primitive_op import PrimitiveOp
from ncad.ops.relational_edit_op import RelationalEditOp
from ncad.ops.reposition_hole_op import RepositionHoleOp
from ncad.ops.revolve_op import RevolveOp
from ncad.ops.rib_op import RibOp
from ncad.ops.shell_op import ShellOp
from ncad.ops.sketch_op import SketchOp
from ncad.ops.split_op import SplitOp
from ncad.ops.sweep_op import SweepOp
from ncad.ops.thread_op import ThreadOp
from ncad.ops.transform_op import TransformOp
from ncad.ops.wrap_op import WrapOp


class OpRegistry:
    """Maps feature op names to their builder callables."""

    def __init__(self) -> None:
        self._ops: dict[str, Callable] = {}

    def register(self, op: str, fn: Callable) -> None:
        """Register ``fn`` as the builder for feature op ``op``."""
        self._ops[op] = fn

    def get(self, op: str) -> Callable:
        """Return the builder for ``op``.

        :raises KeyError: If no builder is registered for ``op`` (a contract error;
            the schema should have caught an unknown op earlier).
        """
        return self._ops[op]

    def op_names(self) -> list[str]:
        """The names of every registered op (the authoritative op vocabulary)."""
        return list(self._ops)

    @classmethod
    def with_defaults(cls) -> "OpRegistry":
        """A registry with the built-in feature ops registered."""
        registry = cls()
        registry.register("sketch", SketchOp().build)
        registry.register("extrude", ExtrudeOp().build)
        registry.register("pocket", PocketOp().build)
        registry.register("primitive", PrimitiveOp().build)
        registry.register("hole", HoleOp().build)
        registry.register("import", ImportOp().build)
        registry.register("defeature", DefeatureOp().build)
        registry.register("offset", OffsetFaceOp().build)
        registry.register("move_face", MoveFaceOp().build)
        registry.register("relate", RelationalEditOp().build)
        registry.register("reposition_hole", RepositionHoleOp().build)
        registry.register("fillet", FilletOp().build)
        registry.register("chamfer", ChamferOp().build)
        registry.register("boolean", BooleanOp().build)
        registry.register("revolve", RevolveOp().build)
        registry.register("groove", GrooveOp().build)
        registry.register("sweep", SweepOp().build)
        registry.register("loft", LoftOp().build)
        registry.register("mirror", MirrorOp().build)
        registry.register("pattern", PatternOp().build)
        registry.register("split", SplitOp().build)
        registry.register("rib", RibOp().build)
        registry.register("shell", ShellOp().build)
        registry.register("draft", DraftOp().build)
        registry.register("wrap", WrapOp().build)
        registry.register("transform", TransformOp().build)
        registry.register("datum_plane", DatumPlaneOp().build)
        registry.register("datum_axis", DatumAxisOp().build)
        registry.register("thread", ThreadOp().build)
        registry.register("feature_pattern", FeaturePatternOp().build)
        registry.register("feature_mirror", FeatureMirrorOp().build)
        return registry
