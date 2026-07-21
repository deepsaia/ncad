Contact makes the dynamics of a multibody system **non-smooth**. As long as bodies move freely the equations of motion are ordinary differential equations, but the instant two surfaces touch, a unilateral constraint switches on: the normal gap cannot go negative, the contact can only push (not pull), and an impact can make velocities jump discontinuously. Dry friction adds a second non-smoothness, because the friction force sits somewhere inside a cone and only becomes determinate once sliding begins. A standard smooth integrator marching across such an event will step straight through the interpenetration and produce garbage. Handling contact correctly is therefore about *how* you cross these events in time.

## The complementarity structure

The canonical model of frictionless unilateral contact is the **Signorini condition**, a complementarity relation between the normal gap \(g_N\) and the normal contact force \(\lambda_N\):

\[ 0 \le g_N \;\perp\; \lambda_N \ge 0. \]

Read this as three statements at once: the gap is non-negative (no penetration), the force is non-negative (no pulling), and their product is zero (force acts only when the gap is closed). At the velocity level, when \(g_N=0\) the same structure applies to the relative normal velocity, and an impact law such as Newton's restitution \(\dot g_N^{+} = -e\,\dot g_N^{-}\) relates post- and pre-impact velocities through the coefficient of restitution \(e\in[0,1]\). Coulomb friction adds \(\|\lambda_T\|\le \mu\,\lambda_N\), with the tangential force opposing sliding and lying strictly inside the cone when stuck. Collecting these gives a **linear (or nonlinear) complementarity problem**, LCP or NCP, to be solved at each contact.

<svg viewBox="0 0 300 130" width="300" height="130" stroke="currentColor" fill="none" stroke-width="1.3">
  <line x1="40" y1="110" x2="260" y2="110"/><line x1="40" y1="110" x2="40" y2="20"/>
  <line x1="40" y1="110" x2="120" y2="110"/>
  <line x1="40" y1="110" x2="40" y2="40"/>
  <text x="150" y="124" font-size="10" stroke="none" fill="currentColor">gap g_N &gt; 0  &#8658;  force = 0</text>
  <text x="48" y="32" font-size="10" stroke="none" fill="currentColor">g_N = 0  &#8658;  force &#8805; 0</text>
</svg>

## Event-driven versus time-stepping

Two schemes dominate. **Event-driven** integration treats the trajectory as a sequence of smooth arcs separated by events. Between events it uses an ordinary smooth integrator; it detects each contact by root-finding on the gap function \(g_N(t)=0\), stops exactly there, applies the impact/complementarity law to reset the state, and restarts. This is accurate and physically transparent, but it degrades badly when events become dense: during a settling chatter, a bouncing die, or a granular pile, the number of events can grow without bound (so-called Zeno behavior), stalling the integrator as it resolves ever-shorter arcs. **Time-stepping** methods instead advance by a fixed step \(h\) and never locate events exactly. Over each step they integrate the equations of motion in *measure* form, so that impulsive and continuous forces are treated on equal footing, and they solve one complementarity problem per step that simultaneously enforces non-penetration, restitution, and the friction cone. The velocity-impulse update takes the schematic form

\[ M\,(v_{n+1}-v_n) = h\,f_n + G_N^{\mathsf T} p_N + G_T^{\mathsf T} p_T, \]

with impulses \(p_N,p_T\) determined by the complementarity conditions rather than by force laws evaluated at a point. The friction cone is often approximated by a polyhedral (faceted) cone to keep the per-step problem an LCP.

## Practical consequences

Time-stepping trades the exactness of event location for robustness: it handles simultaneous and accumulating contacts, sustained rolling and sliding, and impact all within one uniform sweep, which is why it underlies most large-scale contact and granular simulation. Its price is order: these schemes are typically only first-order accurate in position, and the polyhedral friction approximation and the choice of \(h\) introduce artificial anisotropy and energy behavior that must be controlled. Event-driven schemes retain high order between events and give crisp impact resolution, but need reliable, well-conditioned event detection and a fallback when events cluster. Real solvers frequently blend the two, using time-stepping through dense-contact phases and event handling for isolated, energetically important collisions, and they always separate the geometric problem (detecting proximity and computing gaps and normals) from the dynamic problem (solving the resulting complementarity system).
