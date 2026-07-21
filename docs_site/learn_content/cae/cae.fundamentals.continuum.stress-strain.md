Continuum mechanics idealizes a solid as a body that fills space continuously, so that at every material point we can define local measures of internal force intensity and local deformation. **Stress** answers "how hard is the material pulling on itself here, and in what direction?" and **strain** answers "how much has the neighborhood of this point stretched and sheared?" Both are *second-order tensors* because a single number cannot capture that the answer depends on the orientation of the surface (for stress) or the pair of directions (for strain) you interrogate.

## Stress

The stress state at a point is defined through the traction vector \( \mathbf{t} \), the force per unit area acting on an internal cut whose outward normal is \( \mathbf{n} \). Cauchy's stress theorem states that traction depends linearly on the normal through the Cauchy stress tensor \( \boldsymbol{\sigma} \):

\[ t_i = \sigma_{ji}\, n_j . \]

Balance of angular momentum forces the tensor to be symmetric, \( \sigma_{ij} = \sigma_{ji} \), so only six independent components exist (three normal, three shear). Because \( \boldsymbol{\sigma} \) is symmetric it has three real eigenvalues, the **principal stresses** \( \sigma_1 \ge \sigma_2 \ge \sigma_3 \), acting on planes free of shear. It is often split into a spherical (hydrostatic) part and a traceless **deviatoric** part,

\[ \sigma_{ij} = \underbrace{\tfrac{1}{3}\sigma_{kk}\,\delta_{ij}}_{\text{volume change}} + \underbrace{s_{ij}}_{\text{shape change}}, \]

because many yield and failure criteria (for example the von Mises equivalent stress \( \sigma_v = \sqrt{\tfrac{3}{2}\, s_{ij} s_{ij}} \)) depend only on the deviator.

## Strain

Deformation is described by a displacement field \( \mathbf{u}(\mathbf{x}) \). Its gradient is decomposed into a symmetric part (strain) and an antisymmetric part (rigid rotation). For small displacements the **infinitesimal strain tensor** is

\[ \varepsilon_{ij} = \tfrac{1}{2}\!\left( \frac{\partial u_i}{\partial x_j} + \frac{\partial u_j}{\partial x_i} \right), \]

whose diagonal entries are stretches and whose off-diagonal entries are (half) the engineering shear strains. When rotations or stretches are large this linear measure is inadequate because it is not invariant to rigid rotation; one then uses a finite measure such as the Green–Lagrange strain \( E_{ij} = \tfrac{1}{2}(F_{ki}F_{kj} - \delta_{ij}) \) built from the deformation gradient \( F_{ij} = \partial x_i/\partial X_j \).

These two tensors are the raw language of every structural simulation: the solver's job is essentially to find the displacement field whose strain, pushed through a material law into stress, balances the applied loads. Reporting quantities such as principal stress, maximum shear, or von Mises equivalent stress are all invariants extracted from \( \boldsymbol{\sigma} \), and mesh-independent because they do not depend on the coordinate frame.
