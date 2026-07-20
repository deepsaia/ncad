**Measurement queries** interrogate the model for geometric and physical quantities: the distance
between two entities, an angle, a length or area, a bounding box, and the mass properties (volume,
mass, centre of gravity, inertia). They are read-only questions answered from the exact geometry.

## Kinds of query

- **Geometric**: distance (point-point, point-face, face-face minimum), angle between faces or
  axes, edge length, face area, overall bounding box.
- **Physical**: volume, mass, centre of gravity, inertia, for a body, a part, or a rolled-up
  assembly.
- **Over time** (in motion): a measured quantity sampled at each frame becomes a time series (a
  stroke length, a clearance, a swept volume).

## Why measurements are first-class

Because queries run against the exact B-rep, they are precise, not mesh-estimated, and because they
read the same model everything else does, they stay consistent with the geometry through edits.
Measurements are how a design is *verified*: check a wall thickness, confirm a clearance, read the
mass before manufacture. In assemblies and motion they extend to interference (do these parts
collide?) and to time-varying measures that turn a mechanism's behavior into inspectable data. They
are the inspection layer over a model that is otherwise defined entirely by its construction.
