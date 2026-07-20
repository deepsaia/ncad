Two operations bring *existing* model geometry into a sketch: **project** and **offset**.

**Projection** casts an edge, face boundary, or vertex from the 3D model onto the sketch plane,
creating sketch entities that reference the original. Project the top edge of a boss to sketch a
feature aligned to it. The projected geometry is **associative**: if the source moves, the
projection, and everything built on it, follows.

**Offset** creates a new sketch curve a fixed distance from an existing one (a source sketch entity
or a projected edge). Offset a profile inward to sketch a wall of constant thickness, or outward for
a clearance boundary. The offset distance is a driving dimension.

## Why associativity is the point

Both operations create *dependent* geometry, references, not copies. This is how a sketch stays
tied to the part it is built on: a pocket sketched from a projected face boundary keeps matching
that face through edits, and an offset wall keeps its thickness when the source profile changes.
The dependency is exactly the persistent-reference machinery (see the naming and reference
concepts): a projected edge must survive rebuilds by *identity*, not by position, or the sketch
would silently detach when the model changes.
