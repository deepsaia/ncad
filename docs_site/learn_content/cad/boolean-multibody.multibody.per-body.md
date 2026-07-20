**Per-body operations** apply a feature or property to specific bodies of a multibody part rather
than to all of them. This is how multibody modeling stays controlled: dress up one body, assign a
different material to another, boolean two together, leave the rest alone.

## What is applied per body

- **Features**: a fillet, chamfer, or shell scoped to one body's topology.
- **Booleans**: union/cut/intersect between named bodies, leaving others untouched.
- **Materials**: each body can carry its own material (a bimetal part, an over-molded insert), so
  mass and appearance differ per body.
- **Analysis**: mass properties and interference are computed per body and rolled up.

## Scope as the mechanism

Per-body behavior is expressed through a **scope** field naming the target body id(s). Because
bodies have stable identities, a scoped op reliably hits the same body across rebuilds. This turns a
multibody part into a small assembly-within-a-part: independent lumps, each editable and
characterizable on its own, that can be combined when the design calls for it. It is the bridge
between single-solid modeling and full assemblies, multiple solids in one file, related by
construction rather than by mates.
