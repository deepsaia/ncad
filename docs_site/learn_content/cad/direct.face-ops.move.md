**Move face** is a direct (history-free) edit that translates or rotates a selected face of the
current solid, dragging the adjacent faces to follow. Unlike a parametric edit (which changes a
feature's parameter and replays), a direct edit reshapes the baked B-rep in place, useful on
imported geometry that has no feature history, or for a quick local tweak.

## How it works and where it breaks

The kernel identifies the target face, offsets or reorients it, and reconstructs the neighbouring
faces to remain connected. On a clean planar face bounded by other planar faces this is robust. It
becomes fragile fast: a non-planar neighbour, a face adjacent to a fillet, or an over-complex solid
can make the reconstruction fail or silently corrupt the B-rep.

Because of that fragility, a robust modeler runs a **guard** before attempting the op: it inspects
the target face and its neighbourhood and refuses the edit when it falls outside a measured safe
envelope (planar target, planar neighbours, single body, moderate complexity), failing safe rather
than risking a bad result. Direct edits also come *after* the geometry they act on and reference the
face by a persistent name, so the edit reattaches correctly if the model is rebuilt.
