A **relational axis** edit aligns geometry to an axis: make a face **coaxial** with a cylinder,
center a boss on a bore, or align a body's axis with a datum. It solves the transform that places
the moving entity on the target axis and applies it directly to the baked solid.

## Coaxial and axial relations

The common cases are **coaxial** (two cylindrical features share a centerline, a shaft in a bore, a
counterbore over a hole) and **axis alignment** (a body's principal axis onto a reference
direction). The edit computes the rotation that makes the axes parallel plus the translation that
makes them collinear, a rigid motion, and repositions the moving geometry.

Relational axis edits express coaxial *intent* on history-free geometry: rather than relying on two
features happening to be concentric, the edit asserts coaxiality and moves the part to satisfy it,
and re-asserts it if the model changes. As with the other direct/synchronous operations, it works on
the current B-rep, references entities by persistent name, and belongs to the class of edits that
capture relationships (parallel, perpendicular, coaxial, at-angle) without a parametric feature
tree, the synchronous complement to history-based modeling.
