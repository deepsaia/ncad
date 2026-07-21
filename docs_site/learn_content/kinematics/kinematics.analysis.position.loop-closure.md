## What loop closure expresses

A closed kinematic chain is a set of rigid links joined so that at least one path through the joints forms a loop that returns to its starting link. Because the links form a physically continuous ring, the rigid-body transformations accumulated by traversing the loop must compose to the identity: the chain closes on itself. Writing that condition algebraically produces the **loop-closure equations**, the foundation of position analysis for mechanisms. This is the essential difference from an open serial chain, where the pose of the last link follows directly from forward kinematics. In a closed chain the joint variables are not independent; the loop equations couple them, so only a few (the degrees of freedom) can be chosen freely and the rest are solved for.

## Vector form and the planar four-bar

For a single planar loop it is convenient to treat each link as a vector \(r_i e^{i\theta_i}\) in the complex plane and require the directed sum around the loop to vanish. For the canonical four-bar with fixed link \(1\), input crank \(2\), coupler \(3\), and output link \(4\),

\[ r_2 e^{i\theta_2} + r_3 e^{i\theta_3} - r_4 e^{i\theta_4} - r_1 e^{i\theta_1} = 0 . \]

Separating real and imaginary parts gives two scalar equations,

\[ r_2\cos\theta_2 + r_3\cos\theta_3 - r_4\cos\theta_4 - r_1\cos\theta_1 = 0, \qquad r_2\sin\theta_2 + r_3\sin\theta_3 - r_4\sin\theta_4 - r_1\sin\theta_1 = 0 . \]

With the ground along the \(x\)-axis (\(\theta_1 = 0\)) and the input \(\theta_2\) prescribed, the two unknowns are \(\theta_3\) and \(\theta_4\). Eliminating the coupler angle by isolating its terms and squaring produces **Freudenstein's equation**,

\[ K_1\cos\theta_4 - K_2\cos\theta_2 + K_3 = \cos(\theta_2 - \theta_4), \]

with \(K_1 = d/a\), \(K_2 = d/c\), and \(K_3 = (a^2 - b^2 + c^2 + d^2)/(2ac)\), where \(a, b, c, d\) are the crank, coupler, output, and ground lengths. Its two roots for \(\theta_4\) correspond to the two assembly configurations (the open and crossed circuits) into which the same link lengths can be built.

<svg viewBox="0 0 240 150" width="300" stroke="currentColor" fill="none" stroke-width="1.6" aria-label="Four-bar loop">
  <line x1="30" y1="120" x2="180" y2="120" stroke-dasharray="5 4"/>
  <line x1="30" y1="120" x2="75" y2="55"/>
  <line x1="75" y1="55" x2="155" y2="48"/>
  <line x1="180" y1="120" x2="155" y2="48"/>
  <circle cx="30" cy="120" r="4"/><circle cx="180" cy="120" r="4"/>
  <circle cx="75" cy="55" r="4"/><circle cx="155" cy="48" r="4"/>
  <text x="18" y="135" font-size="11" stroke="none" fill="currentColor">O₂</text>
  <text x="184" y="135" font-size="11" stroke="none" fill="currentColor">O₄</text>
  <text x="48" y="92" font-size="11" stroke="none" fill="currentColor">r₂</text>
  <text x="108" y="44" font-size="11" stroke="none" fill="currentColor">r₃</text>
  <text x="172" y="88" font-size="11" stroke="none" fill="currentColor">r₄</text>
  <text x="96" y="134" font-size="11" stroke="none" fill="currentColor">r₁ (ground)</text>
</svg>

## Counting equations, and the general solve

How many loop equations a mechanism has follows from its topology. For a planar mechanism with \(n\) links and \(j\) lower-pair joints, the number of independent loops is \(L = j - n + 1\), and each planar loop contributes two scalar equations (a spatial loop contributes six). The mobility, from the Kutzbach criterion \(M = 3(n-1) - 2j\) in the planar case, tells how many joint variables remain free once the constraints are imposed. Collecting all constraints into a vector \(\boldsymbol{\Phi}(\mathbf{q}) = \mathbf{0}\), where \(\mathbf{q}\) stacks the joint coordinates, gives the complete position problem for the assembly.

Beyond simple linkages these equations are transcendental and have no closed form, so they are solved numerically. Newton-Raphson iteration is standard,

\[ \mathbf{q}_{k+1} = \mathbf{q}_k - \boldsymbol{\Phi}_{\mathbf{q}}^{-1}(\mathbf{q}_k)\,\boldsymbol{\Phi}(\mathbf{q}_k), \]

where \(\boldsymbol{\Phi}_{\mathbf{q}} = \partial\boldsymbol{\Phi}/\partial\mathbf{q}\) is the constraint Jacobian. Because the system is nonlinear it has multiple roots, one per assembly branch (or circuit), and Newton-Raphson converges to whichever branch the initial guess is nearest. This is why position analysis over a motion is done as a **stepped solve**: the driving input is advanced in small increments and each step is seeded with the previous solution, keeping the mechanism on a single continuous branch. The method degrades near singular (dead-center) configurations, where \(\boldsymbol{\Phi}_{\mathbf{q}}\) loses rank, the linkage can switch branches, and the iteration becomes ill-conditioned.

## Why it matters

Loop closure is what makes a closed mechanism analyzable at all: it converts a geometric assembly into a solvable algebraic system, and its Jacobian \(\boldsymbol{\Phi}_{\mathbf{q}}\) is reused directly for velocity and acceleration analysis (differentiate once and twice) and for detecting singularities. In practice it underlies assembly validation (does a given set of dimensions close?), motion simulation of linkages, and dimensional synthesis, where Freudenstein's equation is inverted to choose link lengths that pass through specified positions.
