**Orientation mates** fix the relative *direction* of two parts without fully locating them:
**parallel** (two faces or axes share a direction), **perpendicular** ($90^\circ$ apart), and
**angle** (a set angle between them). They constrain rotation while leaving translation (or other
rotations) free.

## Where they fit

Orientation mates pair with locating mates the way sketch orientation constraints pair with
dimensions: coincident/concentric pin *position*, parallel/perpendicular/angle pin *direction*.
Keeping a bracket's face parallel to a base, holding two shafts perpendicular, setting a strut at 30
degrees, these are orientation mates.

Each lowers to primitive directional constraints on the parts' connector frames (make these axes
parallel, hold this angle between these directions) and removes rotational degrees of freedom from
the assembly. Because they constrain direction only, they are often combined: a concentric mate
(axes collinear) plus a parallel mate (fix the roll) leaves a shaft free to slide but not spin, or
vice versa, which is how a specific joint behavior is composed from simple mates. The solver treats
them uniformly with the locating mates when solving the assembly configuration.
