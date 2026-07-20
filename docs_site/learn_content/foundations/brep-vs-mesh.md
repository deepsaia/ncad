Two fundamentally different ways to represent a 3D shape sit at opposite ends of the accuracy
spectrum: **exact** boundary representation and **approximate** tessellation.

A **boundary representation (B-rep)** describes a solid by its exact topology and geometry: faces
bounded by edges bounded by vertices, where each face carries an exact analytic or spline surface
(plane, cylinder, NURBS) and each edge an exact curve. A cylinder's wall *is* a cylindrical
surface, not a set of flat strips. B-rep is the representation of record for mechanical CAD because
it is exact, queryable (areas, volumes, tangencies are computed from the true geometry), and
manufacturable to tolerance.

A **tessellation** (mesh) approximates the same shape with a net of flat triangles. It cannot
represent a curved surface exactly, only sample it to a chosen **deflection** (the maximum gap
between the triangle and the true surface). Finer deflection means more triangles and a closer
approximation. Meshes are cheap to render and universally portable, which is why they drive
real-time viewers and are the input to physics engines and 3D printing.

## Why the distinction matters

The two are not interchangeable. Measurements, booleans, fillets, and export to a machining
pipeline must run on the **exact** B-rep, tessellating first would bake in approximation error and
lose the analytic surfaces a toolpath needs. Conversely, a browser viewer or a collision check
wants the **mesh**, because triangles are what a GPU and a broadphase actually consume.

A robust modeling engine therefore keeps the B-rep as the source of truth and derives a mesh only
at the display or simulation boundary, with a deflection tuned to the purpose. Determinism lives on
the exact side: the same document must yield the same B-rep, while the tessellation is a
downstream, purpose-specific projection of it.
