Every dimension is either **driving** or **driven**.

A **driving** dimension is an *input*: its value controls the geometry, and the solver moves
entities to satisfy it. These are the parameters an author edits.

A **driven** (reference) dimension is an *output*: it *measures* geometry that other constraints
already determine, and displays the result. It cannot be edited directly, changing it would
over-define the sketch. Driven dimensions are shown parenthetically or greyed to signal they are
read-only.

## Why the distinction is essential

A fully-defined sketch has exactly enough driving dimensions to pin every degree of freedom. Adding
another *driving* dimension where the geometry is already fixed **over-constrains** it (a conflict
the solver must reject). But you often still want to *see* a derived length, the overall span
implied by several partial dimensions, and that is exactly what a driven dimension provides: a live
measurement that adds no constraint.

The rule of thumb: driving dimensions express intent (what you set), driven dimensions report
consequences (what results). A robust parametric sketch keeps the driving set minimal and complete,
and uses driven dimensions freely for inspection.
