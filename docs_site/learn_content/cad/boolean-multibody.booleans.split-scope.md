**Split** divides a solid with a tool (a plane, face, or surface) into multiple bodies, the inverse
of a union. Splitting a block by a plane yields two half-bodies you can keep, discard, or feature
independently, used for section models, symmetric-half modeling, and separating a molded part along
its parting line.

## Keep options and scope

A split typically offers **keep** options: keep both halves (a multibody result), keep only the top
or bottom, or keep a named side. The result changes the body count, so downstream operations must be
prepared to act on several bodies.

That is where **scope** comes in: in a multibody part, an operation can be scoped to specific bodies
rather than the whole set. A boolean can union just two named bodies; a fillet can target one body's
edges. Scope is how per-body intent is expressed after a split or a multibody pattern, so an op
touches exactly the bodies meant, leaving the rest untouched. Split plus scope give controlled,
multibody workflows: divide, operate per-body, and recombine as needed.
