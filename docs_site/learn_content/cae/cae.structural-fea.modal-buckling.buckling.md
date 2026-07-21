Linear (eigenvalue) buckling analysis estimates the load at which a structure loses stability and deflects sideways out of its primary load path, and the shape it collapses into. It answers a question static stress analysis cannot: a slender column or thin shell may be nowhere near material yield yet fail suddenly by buckling, so predicting the critical load is a distinct and essential check for compression-dominated and thin-walled structures.

## Geometric stiffness and the bifurcation problem

The key physical ingredient is that an internal stress state changes a structure's apparent stiffness: tension stiffens, compression softens (stress stiffening). Under a reference load \(\mathbf{f}_0\) the model develops an internal stress field, from which a geometric (stress) stiffness matrix \(\mathbf{K}_\sigma\) is formed. Assuming this internal stress scales linearly with a load factor \(\lambda\), equilibrium of a slightly perturbed configuration admits a nontrivial solution when the tangent stiffness becomes singular:

\[ \left(\mathbf{K} + \lambda\,\mathbf{K}_\sigma\right)\boldsymbol{\phi} = \mathbf{0}. \]

This is a generalized eigenproblem. The smallest eigenvalue \(\lambda_{\text{cr}}\) multiplies the reference load to give the critical (bifurcation) load \(\mathbf{f}_{\text{cr}}=\lambda_{\text{cr}}\mathbf{f}_0\), and its eigenvector \(\boldsymbol{\phi}\) is the buckling mode shape. The classical Euler column, \(P_{\text{cr}}=\pi^2 EI/(KL)^2\), is the closed-form special case of exactly this eigenvalue problem.

## What the linear result does and does not tell you

Linear buckling assumes a linear-elastic material and a linear prebuckling state that does not deform appreciably before the bifurcation. For that reason it typically gives an unconservative (overestimated) prediction for real hardware. Structures that are imperfection-sensitive, above all axially compressed cylindrical and spherical shells, can buckle at a small fraction of the theoretical eigenvalue because tiny geometric imperfections trigger collapse early; this is handled in practice with empirical knockdown factors or, more rigorously, with geometrically nonlinear post-buckling analysis (often seeded with an imperfection shaped like the first eigenmode). The linear eigenvalue is therefore best read as an upper bound and a mode-shape indicator, valuable for screening and design direction, not as the guaranteed failure load.

<svg viewBox="0 0 200 170" role="img" aria-label="Column under axial load: straight configuration and first buckled mode">
  <line x1="40" y1="25" x2="40" y2="140" stroke="currentColor" fill="none"/>
  <line x1="40" y1="25" x2="40" y2="10" stroke="currentColor" fill="none"/>
  <path d="M34 16 L40 8 L46 16" stroke="currentColor" fill="none"/>
  <line x1="25" y1="140" x2="55" y2="140" stroke="currentColor" fill="none"/>
  <path d="M130 25 C 165 60, 165 105, 130 140" stroke="currentColor" fill="none"/>
  <line x1="130" y1="25" x2="130" y2="10" stroke="currentColor" fill="none"/>
  <path d="M124 16 L130 8 L136 16" stroke="currentColor" fill="none"/>
  <line x1="115" y1="140" x2="145" y2="140" stroke="currentColor" fill="none"/>
  <text x="22" y="160" font-size="10" fill="currentColor">P &lt; P_cr</text>
  <text x="108" y="160" font-size="10" fill="currentColor">P = P_cr</text>
</svg>
