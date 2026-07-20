**Volume** and **centre of gravity** (centroid) are the first mass properties computed from a
solid's geometry plus its material density. Volume follows from integrating over the solid; with a
uniform density $\rho$, mass is $m = \rho V$ and the centre of gravity is the density-weighted
average position:

\[
\mathbf{c} = \frac{1}{V}\iiint_V \mathbf{r}\, dV .
\]

## Computed from the exact B-rep

A modeling kernel evaluates these by integrating over the exact boundary representation (via the
divergence theorem, turning volume integrals into surface integrals over the faces), so the results
are exact, not mesh approximations. Assign a material with a density and the part reports its mass
and centroid directly.

## Why they are free and load-bearing

Because the BOM and mass properties read the *same* model the geometry does, they are a
byproduct of the build, no separate authoring. Volume and centroid feed the bill of materials
(mass roll-up), assembly balance, and the inertia computation that motion and dynamics need. In a
multibody or assembly context they roll up: each body/part contributes its mass at its centroid, and
the whole's centre of gravity is the mass-weighted combination. A part with no assigned material has
volume but no mass, itself a signal worth reporting.
