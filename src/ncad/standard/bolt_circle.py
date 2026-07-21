"""Compute evenly-spaced bolt-circle hole positions. Shared by the flange + gasket generators.

A bolt circle is ``count`` holes equally spaced on a circle of ``bolt_circle_diameter``, starting
at the +X axis. Returned as ``[x, y]`` pairs for a ``hole`` feature's ``positions``. Pure function;
no class (this is a tiny geometric helper reused across generators, not a responsibility).
"""

import math


def bolt_circle_positions(bolt_circle_diameter: float, count: int) -> list[list[float]]:
    """The ``[x, y]`` centres of ``count`` holes on a circle of ``bolt_circle_diameter``.

    The first hole is on +X; the rest are spaced by ``2*pi/count``. ``count`` must be positive.
    """
    if count <= 0:
        raise ValueError(f"bolt count must be positive; got {count}")
    radius = float(bolt_circle_diameter) / 2.0
    return [[radius * math.cos(2.0 * math.pi * i / count),
             radius * math.sin(2.0 * math.pi * i / count)] for i in range(count)]
