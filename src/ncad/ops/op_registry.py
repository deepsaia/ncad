"""Op-dispatch registry: feature ``op`` name to builder callable.

Adding an operation is registering an op; this is the generalization of v1's
``roof_builders[kind]`` pattern (design section 4). Each op is a class with a ``build``
method matching the uniform op signature; the registry stores the bound ``build``
methods so the executor can dispatch by op name.
"""

from collections.abc import Callable

from ncad.ops.extrude_op import ExtrudeOp
from ncad.ops.hole_op import HoleOp
from ncad.ops.pocket_op import PocketOp
from ncad.ops.sketch_op import SketchOp


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

    @classmethod
    def with_defaults(cls) -> "OpRegistry":
        """A registry with the built-in feature ops registered."""
        registry = cls()
        registry.register("sketch", SketchOp().build)
        registry.register("extrude", ExtrudeOp().build)
        registry.register("pocket", PocketOp().build)
        registry.register("hole", HoleOp().build)
        return registry
