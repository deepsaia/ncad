The **exponential map on \(SE(3)\)** is the bridge between a *twist* (an instantaneous velocity, an element of the Lie algebra \(\mathfrak{se}(3)\)) and a *finite rigid-body displacement* (a pose, an element of the Lie group \(SE(3)\)). It answers a concrete question: if a body moves with a constant unit screw \(\mathcal{S}=(\omega,v)\) for a parameter distance \(\theta\), where does it end up? The answer is the matrix exponential \(e^{[\mathcal{S}]\theta}\), and it is the analytical form of Chasles' theorem: a finite screw motion.

## Closed form

Because the skew-symmetric matrix \([\omega]\) satisfies \([\omega]^3=-[\omega]\), the infinite exponential series collapses to a finite trigonometric formula. For the rotation part this is **Rodrigues' formula**,

\[
e^{[\omega]\theta} = I + \sin\theta\,[\omega] + (1-\cos\theta)\,[\omega]^2,
\]

and for the full rigid motion (with \(\|\omega\|=1\)),

\[
e^{[\mathcal{S}]\theta} = \begin{bmatrix} e^{[\omega]\theta} & G(\theta)\,v \\ 0 & 1 \end{bmatrix},\qquad
G(\theta) = I\,\theta + (1-\cos\theta)\,[\omega] + (\theta-\sin\theta)\,[\omega]^2.
\]

For a pure translation (\(\omega=0\)), \(G\) reduces to \(I\theta\) and the motion is a straight slide \(v\theta\). The inverse operation, the **logarithm** \(\log: SE(3)\to\mathfrak{se}(3)\), extracts the screw axis and the scalar \(\theta\) from a given pose, recovering the unique screw (up to the usual \(2\pi\) ambiguity in rotation) that produces that displacement.

## Why it matters: product of exponentials

The exponential map is what makes screw theory computational. In the **product-of-exponentials** formulation, the forward kinematics of a serial chain with joint variables \(\theta_1,\dots,\theta_n\) is

\[
T(\theta) = e^{[\mathcal{S}_1]\theta_1}\,e^{[\mathcal{S}_2]\theta_2}\cdots e^{[\mathcal{S}_n]\theta_n}\,M,
\]

where each \(\mathcal{S}_i\) is the screw axis of joint \(i\) in a fixed reference configuration and \(M\) is the tool pose at zero. Unlike link-frame conventions, this needs no per-link coordinate frames: only the joint axes as lines in space and one home pose. The Jacobian columns then follow directly as adjoint-transformed screw axes.

Beyond kinematics, the map is central to numerical work on the group manifold. It provides retractions for optimization over poses (as in pose-graph and bundle-adjustment problems), consistent interpolation between poses (screw interpolation, which yields the geometrically natural constant-twist path rather than a decoupled translate-and-rotate), and the integration step in rigid-body and multibody simulators that advance a pose by an incremental twist while staying exactly on \(SE(3)\). Working through the exponential also avoids the singularities of three-parameter angle representations, since the group element itself is never parameterized by a minimal chart.
