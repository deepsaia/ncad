## The idea of an instant center

At any instant, two rigid bodies in relative planar motion behave, kinematically, as if one were simply rotating about the other around a single point. That point is their **instantaneous center of velocity** (also called the instant center, or the pole): the location at which the two bodies have zero relative velocity. If one of the bodies is the fixed frame, the instant center of a moving body is the point on it (or on its extension) that is momentarily at rest, so the body's motion at that instant is a pure rotation about it. The qualifier *instantaneous* is essential; the instant center generally moves as the mechanism moves, tracing a curve called the centrode.

The practical payoff is a very simple velocity rule. If \(P\) is any point of a body whose instant center relative to ground is \(I\), and the body's angular velocity is \(\omega\), then

\[ \mathbf{v}_P = \boldsymbol{\omega} \times \mathbf{r}_{P/I}, \qquad |\mathbf{v}_P| = \omega\, |\mathbf{r}_{P/I}|, \]

so the velocity of \(P\) is perpendicular to the line joining it to \(I\), with magnitude proportional to that distance. This reduces velocity analysis to geometry: locate the instant center, and every point's velocity direction and relative magnitude follow at once, without differentiating position equations.

## How many, and how to find them

For a mechanism of \(n\) links (counting the frame), every pair of links shares one instant center, so the total count is

\[ N = \binom{n}{2} = \frac{n(n-1)}{2}. \]

Some are found by inspection: a revolute joint is the instant center of the two links it connects (they can only rotate about it), and a prismatic (sliding) joint places the shared instant center at infinity in the direction perpendicular to the slide. The rest are located with the **Aronhold-Kennedy theorem of three centers**: the three instant centers defined by any three bodies in relative plane motion are collinear. Given two lines each containing one unknown center, their intersection fixes it; repeated application (often organized with a circle diagram) resolves every center in turn.

<svg viewBox="0 0 260 120" width="300" stroke="currentColor" fill="none" stroke-width="1.6" aria-label="Kennedy line of three instant centers">
  <line x1="20" y1="85" x2="240" y2="35"/>
  <circle cx="55" cy="77" r="4"/><circle cx="140" cy="58" r="4"/><circle cx="215" cy="41" r="4"/>
  <text x="40" y="98" font-size="11" stroke="none" fill="currentColor">I₁₂</text>
  <text x="128" y="78" font-size="11" stroke="none" fill="currentColor">I₂₃</text>
  <text x="206" y="32" font-size="11" stroke="none" fill="currentColor">I₁₃</text>
  <text x="70" y="20" font-size="11" stroke="none" fill="currentColor">Kennedy line (three centers collinear)</text>
</svg>

## Velocity ratios and mechanical advantage

The instant center shared by two moving links carries a special meaning: it is the one point that momentarily has the *same* velocity whether regarded as belonging to either link. That common velocity ties their angular speeds together. If \(I_{jk}\) is the shared center of links \(j\) and \(k\), and \(I_{1j}\), \(I_{1k}\) are their centers relative to the frame, then

\[ \omega_j\, |\mathbf{r}_{I_{jk}/I_{1j}}| = \omega_k\, |\mathbf{r}_{I_{jk}/I_{1k}}|, \]

which gives the angular-velocity ratio directly from distances measured on a scaled drawing or from coordinates. Because output-to-input velocity ratio and force ratio are reciprocal in an ideal mechanism, the same construction yields the instantaneous **mechanical advantage**, and it exposes the dead-center positions where a velocity ratio goes to zero or infinity.

## Where it matters

Instant centers are the fastest route to a full first-order velocity picture of a planar linkage, valued both as a hand-analysis method and as an intuition builder for how a mechanism transmits motion. They explain transmission-angle and toggle behavior, locate the coupler points that trace desired paths, and underpin classical linkage synthesis. The concept generalizes: in three dimensions the analogous object is the instantaneous screw axis, about which the body simultaneously rotates and translates, which is the spatial counterpart used in screw-theory treatments of velocity.
