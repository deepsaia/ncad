"""Op-dispatch registry: feature ``op`` name to builder function.

Adding an operation is registering a function; this is the generalization of v1's
``roof_builders[kind]`` pattern (design §4).
"""

from collections.abc import Callable

from ncad.ops.extrude_op import build_extrude
from ncad.ops.sketch_op import build_sketch


class OpRegistry:
    """Maps feature op names to their builder functions."""

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


def default_registry() -> OpRegistry:
    """A registry with Bucket 0.1's ops (``sketch``, ``extrude``) registered."""
    registry = OpRegistry()
    registry.register("sketch", build_sketch)
    registry.register("extrude", build_extrude)
    return registry
