In history-free (direct) modeling, a solid is edited by grabbing a face, edge, or vertex and pushing, pulling, rotating, or offsetting it. Unlike history-based modeling, there is no feature tree recording the sequence of operations and the parametric intent behind them. That absence is the whole point of direct editing (it lets you change late-stage or imported "dumb" geometry cheaply) but it creates a problem: a naive push of one face would slide it through neighboring faces and leave the boundary representation invalid or geometrically nonsensical. **Auto-maintained relations**, often marketed as *live rules*, are the mechanism that solves this. They detect the geometric relationships implicit in the current shape and re-enforce them as the edit propagates, so a single drag produces a coherent new solid rather than a broken one.

The relationships that are inferred and preserved are the classic geometric conditions between surfaces and curves: **coplanarity, parallelism, perpendicularity, tangency, concentricity, coaxiality, symmetry about a plane, equal radius, and equal dimension**. When you pull a face, the system first scans the local topology for faces and edges that satisfy one of these conditions with the face being moved. Those become candidate relations. The user typically retains the ability to toggle individual rules on or off for a given edit (for example, "keep tangent" or "maintain symmetry") because inferred intent is a heuristic, not a stored fact. This is the fundamental contrast with parametric modeling, where the constraints were authored explicitly and stored; here they must be recovered from the geometry itself at edit time.

## The governing idea: variational geometric constraint solving

Once candidate relations are selected, the edit becomes a **geometric constraint satisfaction problem**. Each surface carries parameters (a plane has a normal and an offset; a cylinder has an axis, a point, and a radius), and each preserved relation contributes one or more equations in those parameters. Collecting them yields a nonlinear system

\[
F(\mathbf{x}) = \mathbf{0}, \qquad \mathbf{x} \in \mathbb{R}^n,
\]

where \( \mathbf{x} \) stacks the free parameters of the affected faces and \( F \) is the vector of residuals (for instance, a parallelism residual \( \mathbf{n}_1 \times \mathbf{n}_2 \) or a tangency/distance residual). The driven quantity from the user's drag enters as a driving constraint, effectively removing one degree of freedom. The solver then seeks \( \mathbf{x} \) satisfying \( F(\mathbf{x}) = \mathbf{0} \), usually by Newton-Raphson iteration

\[
\mathbf{x}_{k+1} = \mathbf{x}_k - J(\mathbf{x}_k)^{-1} F(\mathbf{x}_k),
\]

with \( J = \partial F / \partial \mathbf{x} \) the Jacobian. Because full Newton on the entire model is fragile and slow, production solvers first perform **degree-of-freedom analysis**: they model the entities and constraints as a graph, use maximum matching and connected-component (or dense-cluster) decomposition to break the system into small, independently solvable clusters, and solve those in dependency order. This graph-based decomposition is what makes the response feel interactive even on large parts.

## Why detection and consistency are the hard part

Two failure modes dominate. First, **under- or over-constraining**: if the inferred relations plus the drive leave residual freedom, the result is ambiguous and the solver may pick an unintended configuration; if they conflict, the system is inconsistent and no valid solid exists. The DOF count \( d = n - m \) (parameters minus independent constraint equations) is the first-order diagnostic, though rank deficiency in \( J \) can hide redundant or conflicting constraints even when \( d = 0 \). Second, **relation detection is a tolerance decision**: two faces that are parallel to within a micro-radian either "are" parallel (and must stay so) or are not (and may freely diverge). The chosen angular and distance tolerances directly determine which relations get captured, so a good implementation exposes and documents them rather than hiding them.

A further subtlety absent from parametric modeling is that after the parameters are solved, the **boundary representation must be regenerated**: moved surfaces are re-intersected to recompute edges and vertices, faces are re-trimmed, and the shell is re-sewn and validated. A push that geometrically over-runs a neighbor can eliminate a face entirely or merge two, so the topological rebuild, not just the numeric solve, is where robustness is won or lost.

## Where it matters

Auto-maintained relations are what make direct modeling usable for the tasks it is chosen for: editing supplier or legacy models that arrive with no construction history, making fast "what-if" shape changes late in a design, and repairing translated geometry. They let a designer move a mounting boss and have the symmetric boss on the other side follow, or shorten a rib and keep its draft and blend tangencies intact, without ever having authored those constraints. The trade-off relative to stored parametrics is that the intent is re-inferred on every edit and is only as good as the detection heuristics and the solver's ability to keep the result valid; understanding the constraint-solving and topology-rebuild machinery underneath is essential to predicting when a direct edit will succeed and when it will produce a surprising or invalid shape.
