"""An ordered collection of bodies - the multibody form of a part's running shape.

A single-body part never needs a BodySet (the running shape stays a plain kernel handle);
a BodySet appears only when an op keeps bodies separate (a ``boolean merge=false``). Kernel
shape-consuming methods detect a BodySet and handle it per body.
"""

from typing import Any

from ncad.kernel.body import Body


class BodySet:
    """An ordered list of bodies with id-keyed lookup."""

    def __init__(self, bodies: list[Body]) -> None:
        self._bodies = list(bodies)

    @property
    def bodies(self) -> list[Body]:
        """The bodies in stable order."""
        return list(self._bodies)

    def ids(self) -> list[str]:
        """Body ids in order."""
        return [b.id for b in self._bodies]

    def by_id(self, body_id: str) -> Body:
        """The body with ``body_id``.

        :raises KeyError: if no body has that id.
        """
        for body in self._bodies:
            if body.id == body_id:
                return body
        raise KeyError(f"no body with id {body_id!r}")

    def shapes(self) -> list[Any]:
        """The kernel shape handle of each body, in order."""
        return [b.shape for b in self._bodies]

    def __len__(self) -> int:
        return len(self._bodies)


def union_bodies(shapes: list, origin: str) -> "BodySet":
    """Collect ``shapes`` into one BodySet as separate bodies (a keep-separate union).

    A plain shape becomes a new body ``<origin>/body/<n>`` (id minted at BIRTH); a shape that
    is already a BodySet contributes its bodies WITH THEIR EXISTING ids (a body is born once,
    not re-minted per feature - the persistent-identity rule).
    """
    bodies: list[Body] = []
    for shape in shapes:
        if isinstance(shape, BodySet):
            bodies.extend(shape.bodies)
        else:
            bodies.append(Body(id=f"{origin}/body/{len(bodies)}", kind="solid",
                               shape=shape, created_by=origin))
    return BodySet(bodies)
