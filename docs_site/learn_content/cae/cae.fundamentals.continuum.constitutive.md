The equilibrium and kinematic relations of continuum mechanics are *universal*: they hold for steel, rubber, or bone alike. What distinguishes one material from another is the **constitutive law**, the relation that closes the system by tying stress to strain (and often to temperature, rate, and history). Without it there are more unknowns than equations; with it the boundary-value problem becomes solvable. Choosing the constitutive model is therefore the single most consequential modeling decision in a stress analysis, and it must match the regime the part actually operates in.

## Generalized Hooke's law

For small strains and moderate loads most engineering metals behave linearly and elastically: strain is proportional to stress and fully recoverable. The general linear relation is a fourth-order stiffness tensor mapping strain to stress,

\[ \sigma_{ij} = C_{ijkl}\, \varepsilon_{kl}. \]

The symmetries of stress and strain, plus the existence of a strain-energy potential, reduce \( C_{ijkl} \) from 81 to at most **21 independent constants** for a fully anisotropic solid. Material symmetry reduces this further: 9 for orthotropic materials (composites, rolled sheet, wood) and just **2 for an isotropic material**. In the isotropic case the law takes the compact Lamé form

\[ \sigma_{ij} = \lambda\, \varepsilon_{kk}\, \delta_{ij} + 2\mu\, \varepsilon_{ij}, \]

where \( \mu = G \) is the shear modulus and \( \lambda \) the first Lamé parameter. Engineers usually work instead with Young's modulus \( E \) and Poisson's ratio \( \nu \), which are interchangeable with the Lamé constants:

\[ \mu = \frac{E}{2(1+\nu)}, \qquad \lambda = \frac{E\,\nu}{(1+\nu)(1-2\nu)}, \qquad K = \frac{E}{3(1-2\nu)}. \]

Note that as \( \nu \to 0.5 \) the bulk modulus \( K \) diverges: the material becomes incompressible, which is why nearly incompressible rubbers and soft tissue require special formulations to avoid numerical locking.

## Beyond linear elasticity

Many simulations must go further. **Plasticity** models introduce a yield surface (for example von Mises) beyond which deformation is permanent, requiring a flow rule and a hardening law. **Hyperelasticity** (Neo-Hookean, Mooney–Rivlin, Ogden forms) describes large, recoverable strains in elastomers through a strain-energy density function. **Viscoelasticity and creep** add rate and time dependence. **Thermoelasticity** superimposes a thermal strain \( \varepsilon^{\text{th}}_{ij} = \alpha\,\Delta T\,\delta_{ij} \) that the elastic law acts on. Each of these is still "a constitutive law"; they simply trade the constant matrix \( C \) for a nonlinear, path-dependent operator. The practical lesson is that the reported stresses are only as trustworthy as the material model and its calibrated constants, so the constitutive choice belongs to the owned model, not to the solver.
