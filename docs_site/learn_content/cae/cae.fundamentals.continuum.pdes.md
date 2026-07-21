Almost every physics a CAE tool simulates is expressed as a **partial differential equation (PDE)**: a statement that a conservation or balance principle holds at every point of a domain, coupled with a constitutive relation. The PDE is the *strong form* of the problem. Understanding its type tells you what the solution looks like, what boundary data it needs, and which numerical method is appropriate.

## Mechanical equilibrium

Starting from balance of linear momentum on an arbitrary sub-volume and applying the divergence theorem gives Cauchy's first equation of motion, whose static form is the **equilibrium equation**:

\[ \frac{\partial \sigma_{ji}}{\partial x_j} + b_i = \rho\, \ddot{u}_i \quad\xrightarrow{\text{static}}\quad \sigma_{ji,j} + b_i = 0, \]

where \( b_i \) is the body force per unit volume. Substituting the strain–displacement relation and the isotropic Hooke law turns this into the **Navier equation**, a coupled elliptic system in the displacement field alone:

\[ \mu\, u_{i,jj} + (\lambda + \mu)\, u_{j,ji} + b_i = 0. \]

Its elliptic character means disturbances are felt everywhere instantly (no wave-like propagation in the static case) and that a well-posed problem needs boundary data over the *entire* boundary.

## Diffusion and steady conduction

The same recipe (conservation plus a flux law) governs transport. Energy conservation with Fourier's law \( \mathbf{q} = -k\,\nabla T \) yields the **heat/diffusion equation**

\[ \rho c_p\, \frac{\partial T}{\partial t} = \nabla\cdot(k\,\nabla T) + \dot{q}, \]

which is *parabolic*: it smooths initial data and marches forward in time, needing an initial condition plus boundary conditions. Its steady state drops the time term and, for constant conductivity, reduces to the **Poisson equation** \( \nabla^2 T = -\dot{q}/k \) (or Laplace's equation \( \nabla^2 T = 0 \) with no source), which is elliptic like the mechanical problem. Mass diffusion (Fick's law), electrostatics, seepage, and steady potential flow share this identical mathematical structure, which is why one field solver can serve many physics.

## Why the strong form is rarely solved directly

The strong form demands that the solution be smooth enough for its highest derivatives to exist pointwise, which is too strict for real geometry with corners and material interfaces. Numerical methods therefore recast the PDE into an equivalent **weak (variational) form** by multiplying by a test function and integrating by parts, lowering the differentiability requirement and, crucially, exposing where each kind of boundary condition enters. This weak form is the bridge from the continuum PDE to the discrete algebraic system that a finite-element engine actually solves.
