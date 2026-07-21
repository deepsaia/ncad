A looped pipe network is a graph of nodes (junctions with demands, tanks, reservoirs) connected by links (pipes, pumps, valves). Solving it means finding the set of pipe flows \( Q \) and nodal heads \( H \) that simultaneously satisfy two conservation laws everywhere: **mass balance at every junction** (inflow minus outflow equals demand) and **energy balance around every independent loop** (the head losses around a closed loop sum to zero). Because each pipe's head loss is nonlinear in its flow, \( h_L = r\,Q^{n} \) with \( n = 2 \) for Darcy-Weisbach or \( 1.852 \) for Hazen-Williams, the resulting system is a set of coupled nonlinear equations that must be solved iteratively.

## Hardy-Cross

The classical **Hardy-Cross** method (1936) was the first systematic hand-computable scheme. In its loop-balancing form it starts from an assumed set of flows that already satisfy continuity at every node, then repeatedly corrects each loop's flow by \( \Delta Q \) so the loop energy imbalance is driven toward zero. Applying a first-order Newton correction to \( \sum r Q|Q|^{n-1} = 0 \) gives the well-known formula

\[ \Delta Q = -\,\frac{\sum_{\text{loop}} r\,Q\,|Q|^{n-1}}{\;n\sum_{\text{loop}} r\,|Q|^{n-1}\;} = -\,\frac{\sum h_L}{\,n\sum |h_L / Q|\,}. \]

Each loop is corrected in turn and the sweep repeats until the corrections fall below a tolerance. Hardy-Cross is transparent and needs no matrix machinery, which is why it dominated pre-computer practice and still teaches the concept well, but it corrects one loop at a time and converges slowly (or fails) on large, tightly coupled, or ill-conditioned networks.

<svg viewBox="0 0 260 120" width="260" height="120" stroke="currentColor" fill="none" stroke-width="1.5">
  <circle cx="40" cy="30" r="4"/><circle cx="140" cy="30" r="4"/><circle cx="140" cy="90" r="4"/><circle cx="40" cy="90" r="4"/>
  <circle cx="220" cy="30" r="4"/><circle cx="220" cy="90" r="4"/>
  <line x1="40" y1="30" x2="140" y2="30"/><line x1="140" y1="30" x2="140" y2="90"/>
  <line x1="140" y1="90" x2="40" y2="90"/><line x1="40" y1="90" x2="40" y2="30"/>
  <line x1="140" y1="30" x2="220" y2="30"/><line x1="220" y1="30" x2="220" y2="90"/><line x1="220" y1="90" x2="140" y2="90"/>
  <text x="78" y="63" font-size="11" fill="currentColor" stroke="none">loop I</text>
  <text x="165" y="63" font-size="11" fill="currentColor" stroke="none">loop II</text>
</svg>

## Gradient / global solution

Modern solvers replace loop-by-loop relaxation with a **simultaneous Newton solution of the full network**. The **Global Gradient Algorithm** of Todini and Pilati (1988), the engine inside the widely used public-domain network solver, writes the coupled node-continuity and link-energy equations in matrix form and linearizes them about the current iterate. Collecting unknown heads \( \mathbf{H} \) and flows \( \mathbf{Q} \), each Newton step solves a symmetric, positive-definite linear system for the head corrections,

\[ \big(\mathbf{A}_{21}\,\mathbf{D}^{-1}\,\mathbf{A}_{12}\big)\,\mathbf{H} = \mathbf{A}_{21}\,\mathbf{D}^{-1}\big(\mathbf{A}_{11}\mathbf{Q} + \mathbf{A}_{10}\mathbf{H}_0\big) - \big(\mathbf{A}_{21}\mathbf{Q} - \mathbf{q}\big), \]

after which the flows are updated explicitly. Here \( \mathbf{A}_{12} = \mathbf{A}_{21}^{\mathsf T} \) is the node-link incidence matrix, \( \mathbf{A}_{11} \) is diagonal holding each link's head-loss-per-flow, \( \mathbf{D} \) is the diagonal of head-loss derivatives \( \partial h_L/\partial Q \), \( \mathbf{A}_{10}\mathbf{H}_0 \) carries the fixed-head (reservoir/tank) boundary conditions, and \( \mathbf{q} \) is the demand vector. Because it updates all heads and flows together, the method exhibits quadratic (Newton) convergence, handles pumps, check valves, and pressure-regulating valves through the diagonal terms, and scales to networks of many thousands of links.

Steady-state solution is only one time slice. Real systems are analyzed by **extended-period simulation**, which chains a sequence of these hydraulic solves while advancing tank levels, demand patterns, and control rules between steps, and can pass the resulting flows and velocities to a water-quality (age, tracer, or chlorine-decay) transport model. In practice the network model is validated by comparing computed pressures and flows against field measurements and then used for capacity planning, pump scheduling, fire-flow checks, and contamination or leakage studies.
