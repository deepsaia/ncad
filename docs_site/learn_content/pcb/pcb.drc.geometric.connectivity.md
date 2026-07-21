The net-connectivity check answers a different question from the geometric spacing and width checks: not *are the features large enough and far enough apart*, but *does the copper actually implement the intended electrical schematic*. The design carries a **netlist**, the logical statement of which component pins are meant to be electrically common (each named net is a set of pins). The connectivity check reconstructs the *physical* nets from the copper and compares them against that logical truth.

## The graph model

Connectivity is a topological, not a metric, property, so it is naturally a graph problem. Every conductive primitive (pad, trace segment, via, filled pour, plane) is a node; two nodes share an edge when their copper physically touches or overlaps on the same layer, or when a via joins layers. Running a **union-find (disjoint-set)** pass over these adjacencies collapses each electrically continuous blob of copper into one connected component. Each component is a *physical net*. The check then aligns physical nets with logical nets by the pins they contain, and any mismatch is a defect:

- **Unrouted / open**: pins that share a logical net fall in different physical components. The still-needed connections are drawn as *airwires* (a ratsnest), usually rendered as a minimum spanning tree over the disconnected pin clusters so the display shows the fewest, shortest hints.
- **Short**: pins from two different logical nets land in the same physical component, meaning copper bridges nets that must stay separate.
- **Unconnected pin / dangling copper**: a required pin has no copper, or an isolated copper island belongs to no net.
- **Starved or missing thermal**: a pad connects to a pour only through relief spokes that a rules-aware check must still count as connected.

Because the reconstruction is exact and independent of distance, connectivity checking is the complement to geometric DRC: geometric rules can pass on a board that is wired wrong, and connectivity can pass on a board that violates spacing, so both must run. The union-find approach is near-linear in the number of copper primitives (effectively \(O(N\,\alpha(N))\) with the inverse-Ackermann factor), which is what lets the check run interactively as copper is edited and incrementally re-flag only the components that changed.

## Where it matters and how it is verified downstream

A clean connectivity result is the precondition for release: an unrouted board is incomplete, and an undetected short is a scrapped fabrication run. The same principle extends past design into fabrication, where the extracted board netlist is exported in a standard machine-readable form and handed to the bare-board **electrical test** step. There the fabricator flying-probes or bed-of-nails-tests every net for continuity and isolation and compares the measured connectivity against the supplied netlist, catching etching opens and shorts that the artwork alone cannot reveal. The design-time connectivity check and the fabrication-time electrical test are the same graph comparison applied at two stages of the flow.
