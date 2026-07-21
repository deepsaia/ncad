A simulation workflow has always separated cleanly into three stages: **pre-processing** (build the geometry, mesh it, assign materials, apply loads and restraints), the **solve** (assemble the global system and run the numerical solver), and **post-processing** (extract and visualize results). The *owned-model / delegated-solve* principle takes this classical triad and draws the ownership boundary deliberately: the modeling environment **owns** everything that defines the problem, and **delegates** the numerically intensive solve to a separate, ideally open, engine through a well-defined, human-readable interface.

## What is owned

The owned side is the *definition of the problem*, and it is where all the engineering intent lives: the geometry and its feature history, the discretization (mesh and element choices), the constitutive models and their calibrated constants, and the boundary conditions bound to persistent geometric references so they survive edits and re-meshing. This is precisely the content of the preceding fundamentals: stress/strain measures, constitutive laws, governing PDEs, and boundary conditions. It is authored, versioned, and validated locally; it must be deterministic (the same inputs produce the same problem statement) and auditable.

## What is delegated

The solve, matrix assembly, factorization or iterative solution, nonlinear and time integration, is a mature, commodity capability. Delegating it to an external engine yields several engineering advantages:

- **Solver independence.** The same owned model can be exported to more than one engine, enabling cross-verification (do two independent solvers agree?) and avoiding lock-in to any single implementation.
- **Reproducibility and auditability.** A neutral input deck is a complete, inspectable record of exactly what was solved. Anyone can re-run it years later; the result is not trapped inside an opaque binary session.
- **Separation of concerns.** The modeling side can evolve its geometry and meshing without reimplementing linear algebra, and the solver can be upgraded without touching the model.

The contract between the two sides is a **neutral solver deck**: a text description enumerating nodes, elements, materials, sections, and the boundary-condition sets, that the engine consumes to produce results the modeler reads back. Keeping this interface explicit and standardized is what makes the delegation clean rather than a hidden coupling.

## The trade-off

Delegation costs a round trip and a translation step, and it demands rigor at the interface: the mapping of geometry-associated loads and restraints onto mesh entities must be exact, and result quantities must be interpreted in the frame and units the deck declared. The payoff is a durable division of labor that mirrors decades of finite-element practice, keeps the model portable and inspectable, and lets verification live where it belongs, with the owner checking the problem statement and the delegated engine responsible for solving those equations correctly.
