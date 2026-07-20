A **semantic reference** names a topological entity by *what it is* in the model's construction,
not by an opaque index. "The top cap of the `pad` extrude" or "the bore of the `hole` feature" are
semantic: they mean the same thing before and after an unrelated upstream edit.

## Why semantic beats positional

Positional references (face index, vertex order) are brittle because the kernel renumbers topology
whenever the model changes, that is the topological naming problem. A semantic reference is stable
because it is anchored to the operation and role that created the entity, which replay reproduces
identically.

Semantic references are the everyday way an author points at geometry: select "the top face" to
sketch on, "the outer edges" to fillet, "this cap" to place a hole. Under the surface each resolves
through the persistent-name layer to a concrete face on the current solid. When the reference cannot
resolve (the named entity no longer exists after an edit), a robust modeler reports it loudly with
the feature id, rather than silently attaching to the wrong face, because a silent misattachment is
the worst failure mode in parametric CAD.

Semantic naming is one of a few reference kinds. It handles the common, human-authored case; a
**selector** query handles rule-based selection, and **generative** tags handle entities an op mints
on the fly.
