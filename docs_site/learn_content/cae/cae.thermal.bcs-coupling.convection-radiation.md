A conduction model is only as meaningful as the conditions imposed on the surfaces where the body exchanges energy with its surroundings. Thermal boundary conditions come in three canonical mathematical forms. A **Dirichlet** (first-kind, essential) condition fixes the surface temperature, \(T = T_s\). A **Neumann** (second-kind, natural) condition fixes the surface heat flux, \(-k\,\partial T/\partial n = q''\), with the special case \(q'' = 0\) representing a perfectly insulated (adiabatic) or symmetry surface. The remaining physical exchanges, **convection** and **radiation**, both make the surface flux depend on the surface temperature itself, so they enter as **Robin** (third-kind, mixed) conditions that modify the system matrices rather than merely the load vector.

## Convection

Convection couples a solid surface to a moving fluid and is modeled by **Newton's law of cooling**,

\[ q'' = h\,(T_s - T_\infty), \]

where \(h\) is the convective heat-transfer coefficient and \(T_\infty\) is the bulk fluid (sink) temperature. The coefficient \(h\) is not a material property; it lumps the entire fluid-side boundary-layer behavior and is normally supplied from empirical correlations expressed through the dimensionless **Nusselt number** \(\mathrm{Nu} = hL/k_f\), itself a function of Reynolds and Prandtl numbers (forced convection) or Rayleigh number (natural convection). In the finite-element system the convection term contributes to both sides: \(\int_\Gamma h\,\mathbf{N}^{\mathsf T}\mathbf{N}\,d\Gamma\) adds to the conductivity matrix \(\mathbf{K}\), while \(\int_\Gamma h\,T_\infty\,\mathbf{N}^{\mathsf T} d\Gamma\) adds to the load vector \(\mathbf{F}\). Because it draws the surface toward \(T_\infty\) with a finite conductance, convection is the mechanism that makes an analysis behave physically instead of accumulating heat without limit.

## Radiation

Radiation exchanges energy through electromagnetic emission and requires no medium. Its net flux follows the **Stefan-Boltzmann law**,

\[ q'' = \varepsilon\,\sigma\,\big(T_s^4 - T_{\text{surr}}^4\big), \]

with emissivity \(\varepsilon\), the Stefan-Boltzmann constant \(\sigma = 5.67\times10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}\), and temperatures on an absolute scale. The fourth-power dependence makes radiation strongly **nonlinear**, so it dominates at high temperature and is often negligible near ambient. Solvers commonly linearize it about the current temperature using a radiative heat-transfer coefficient

\[ h_r = \varepsilon\,\sigma\,(T_s + T_{\text{surr}})(T_s^2 + T_{\text{surr}}^2), \]

so that \(q'' = h_r (T_s - T_{\text{surr}})\) can be folded into the same Robin machinery and iterated (Newton-Raphson or Picard) until the temperature-dependent \(h_r\) converges.

## Enclosures and view factors

When surfaces radiate to one another rather than to a single distant sink, the exchange depends on geometry through **view factors** \(F_{ij}\), the fraction of radiation leaving surface \(i\) that reaches surface \(j\), constrained by reciprocity \(A_i F_{ij} = A_j F_{ji}\) and the summation rule \(\sum_j F_{ij} = 1\). Gray-diffuse enclosure analysis assembles these into a dense radiative-exchange matrix that couples every participating facet, which is far more expensive than convection and is usually restricted to the surfaces where it matters (furnace linings, spacecraft radiators, electronics in vacuum). In practice an engineer chooses the least complex condition that still captures the dominant loss path: a fixed temperature where a large thermal mass clamps a face, a flux where a heater or absorbed power is known, convection wherever a fluid flows, and radiation wherever temperatures are high or convection is absent. Getting the boundary conditions right, and being honest about the uncertainty in \(h\) and \(\varepsilon\), is typically the largest source of error in a thermal model.
