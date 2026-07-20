A sketch is a **system of constraint equations** over the coordinates of its entities. Solving the
sketch means finding entity positions that satisfy every constraint simultaneously.

Each free entity contributes **degrees of freedom** (a point: 2; a line: 4; a circle: 3). Each
constraint removes DoF (a coincidence: up to 2; a dimension: 1; a horizontal: 1). The sketch is
**fully defined** when the remaining DoF reach zero, that is, when

\[
\text{DoF} = (\text{entity coordinates}) - (\text{independent constraints}) = 0 .
\]

## How the solver works

The constraints form a nonlinear system $f(x) = 0$ over the coordinate vector $x$. A geometric
constraint solver drives the residual to zero by **Newton-Raphson** iteration (see the numerics
foundations), computing the constraint Jacobian and stepping until every constraint is satisfied to
tolerance. Near a valid configuration this converges quadratically, which is why a well-posed sketch
solves instantly.

The Jacobian's rank is diagnostic. Full rank with zero remaining DoF means a unique solution
(fully defined). A rank deficiency signals redundant or conflicting constraints; extra DoF mean the
sketch is under-defined and geometry can still move. A robust solver reports which state the sketch
is in rather than silently returning one of many solutions.
