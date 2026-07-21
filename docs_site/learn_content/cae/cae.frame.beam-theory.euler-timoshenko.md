A beam is a slender structural member that carries load chiefly by bending. Beam *theories* reduce the full three-dimensional elasticity problem to a one-dimensional model along the member axis by postulating how each cross-section moves. The two theories that dominate frame analysis differ in a single kinematic assumption: whether a plane cross-section, after deformation, stays **perpendicular** to the bent neutral axis (Euler-Bernoulli) or is allowed to **rotate independently** to absorb transverse shear (Timoshenko-Ehrenfest). That one choice determines the governing equations, the element formulation used in a solver, and the range of member geometries over which the answer is trustworthy.

## Euler-Bernoulli (classical) theory

Euler-Bernoulli theory assumes cross-sections remain plane *and* normal to the deformed axis, so the section rotation equals the slope of the deflection curve, \( \theta = dw/dx \). Shear deformation and rotary inertia are neglected. For a prismatic beam of bending stiffness \(EI\) under distributed transverse load \(q(x)\), equilibrium collapses to a single fourth-order equation:

\[ EI\,\frac{d^4 w}{dx^4} = q(x). \]

Because the curvature is \( \kappa = d^2 w/dx^2 \) and the moment is \( M = EI\,\kappa \), the deflection field is smooth (requiring \(C^1\) continuity), which is why the corresponding finite element uses cubic Hermite shape functions with two nodes carrying transverse displacement and rotation. This model is accurate for slender members, roughly span-to-depth ratios \(L/h \gtrsim 10\text{--}20\).

## Timoshenko theory and where it matters

Timoshenko theory relaxes the normality condition: the section rotation \( \varphi \) becomes an **independent field**, and the difference between the axis slope and the section rotation is the transverse shear strain, \( \gamma = dw/dx - \varphi \). The constitutive relations then involve two stiffnesses, the bending stiffness \(EI\) and the shear stiffness \(kGA\), where \(k\) (often written \( \kappa \)) is a **shear correction factor** accounting for the non-uniform distribution of shear stress over the section (\(k \approx 5/6\) for a rectangle). The coupled equilibrium equations \( dV/dx + q = 0 \) and \( dM/dx - V = 0 \), with \( M = EI\,d\varphi/dx \) and \( V = kGA(dw/dx - \varphi) \), combine for uniform properties into

\[ EI\,\frac{d^4 w}{dx^4} = q - \frac{EI}{kGA}\,\frac{d^2 q}{dx^2}. \]

The practical consequence is extra flexibility. A cantilever of length \(L\) under an end load \(P\) deflects by a bending term plus a shear term:

\[ w_{\text{tip}} = \underbrace{\frac{PL^3}{3EI}}_{\text{bending}} + \underbrace{\frac{PL}{kGA}}_{\text{shear}}. \]

The shear contribution scales with \( EI/(kGA\,L^2) \), i.e. with the square of the depth-to-length ratio, so it is negligible for slender beams but becomes significant for deep or short members, sandwich sections, and higher vibration modes (where rotary inertia also matters). The diagram below contrasts the two kinematics.

<svg viewBox="0 0 420 160" width="420" height="160" stroke="currentColor" fill="none" stroke-width="1.5" font-family="sans-serif" font-size="11">
  <text x="70" y="14" stroke="none" fill="currentColor">Euler-Bernoulli</text>
  <path d="M20 90 Q80 60 130 55"/>
  <line x1="95" y1="55" x2="75" y2="105"/>
  <line x1="95" y1="55" x2="115" y2="5" stroke-dasharray="3 3"/>
  <text x="20" y="120" stroke="none" fill="currentColor">section stays normal to axis</text>
  <text x="290" y="14" stroke="none" fill="currentColor">Timoshenko</text>
  <path d="M250 90 Q310 60 360 55"/>
  <line x1="325" y1="55" x2="312" y2="105"/>
  <line x1="325" y1="55" x2="345" y2="5" stroke-dasharray="3 3"/>
  <path d="M325 78 A26 26 0 0 1 333 82" stroke-width="1"/>
  <text x="338" y="84" stroke="none" fill="currentColor">γ</text>
  <text x="250" y="120" stroke="none" fill="currentColor">section rotates by shear angle γ</text>
</svg>

In a finite element implementation, the Timoshenko element interpolates \(w\) and \( \varphi \) independently, which requires only \(C^0\) continuity but introduces **shear locking**: with naive equal-order linear interpolation, a thin element cannot represent pure bending and becomes spuriously stiff. Standard remedies are reduced or selective integration of the shear term, assumed-strain formulations, or interdependent interpolation. Because it degenerates gracefully to the Euler-Bernoulli result as the section becomes slender, the Timoshenko formulation is the more general and is commonly the default in general-purpose frame solvers.
