Once the space is chosen, each variable still needs a concrete **motion profile**: a time function that connects a start state to an end state while keeping velocity, acceleration, and often jerk bounded and continuous. Continuity matters physically. A discontinuity in velocity implies infinite acceleration; a discontinuity in acceleration implies infinite jerk, which excites structural resonances, wears gearing, and shows up as audible knock and tracking error. The profile families below are ordered by how much smoothness they guarantee.

## Polynomial profiles

The simplest point-to-point profile is the **cubic polynomial**, \( q(t) = a_0 + a_1 t + a_2 t^2 + a_3 t^3 \). Its four coefficients are fixed by four boundary conditions: position and velocity at both ends. For a rest-to-rest move of duration \( T \) from \( q_0 \) to \( q_f \) with zero endpoint velocities,

\[
a_0 = q_0,\quad a_1 = 0,\quad a_2 = \frac{3(q_f - q_0)}{T^2},\quad a_3 = -\frac{2(q_f - q_0)}{T^3}.
\]

A cubic gives continuous position and velocity but only piecewise-linear acceleration, so jerk is a step (discontinuous) at the endpoints. Constraining acceleration as well requires the **quintic** (fifth-order) polynomial with six coefficients, which delivers continuous acceleration and finite jerk. Polynomials are smooth but do not let you cap peak velocity or acceleration independently; those extrema are dictated by the coefficients and \( T \).

## Trapezoidal and S-curve profiles

When the goal is *time-optimal* motion under explicit actuator limits, the classic answer is the **trapezoidal velocity profile** (linear-segment-with-parabolic-blends). The move is split into constant-acceleration ramp-up, constant-velocity cruise at \( v_{\max} \), and constant-acceleration ramp-down. It is time-optimal subject to \( |\dot{q}| \le v_{\max} \) and \( |\ddot{q}| \le a_{\max} \), but its acceleration is a square wave, so jerk is impulsive at the corners. The **S-curve** (seven-segment) profile fixes this by bounding jerk, rounding each corner of the trapezoid into a parabolic acceleration ramp; it trades a small amount of cycle time for dramatically smoother, lower-vibration motion, which is why it is the default on high-performance machine axes.

<svg viewBox="0 0 320 140" width="320" height="140" stroke="currentColor" fill="none" stroke-width="1.5" aria-label="Trapezoidal velocity profile">
  <line x1="30" y1="110" x2="300" y2="110"/>
  <line x1="30" y1="110" x2="30" y2="15"/>
  <polyline points="30,110 100,40 230,40 300,110"/>
  <line x1="100" y1="40" x2="100" y2="110" stroke-dasharray="3 3"/>
  <line x1="230" y1="40" x2="230" y2="110" stroke-dasharray="3 3"/>
  <text x="305" y="114" font-size="10" fill="currentColor" stroke="none">t</text>
  <text x="12" y="20" font-size="10" fill="currentColor" stroke="none">v</text>
  <text x="150" y="34" font-size="9" fill="currentColor" stroke="none">v_max</text>
</svg>

## Splines through via points

When a trajectory must pass through a sequence of intermediate **via points**, fitting a single high-order polynomial is ill-conditioned (Runge oscillation). The standard remedy is a **spline**: piecewise low-order polynomials joined with continuity constraints at the knots. A natural **cubic spline** enforces continuity of position, velocity, and acceleration (\( C^2 \)) across every via point, yielding smooth multi-segment motion. B-splines and their rational (NURBS) generalizations add local control and the ability to place velocity/acceleration constraints on each segment, and are widely used to smooth the piecewise-linear output of a path planner into a dynamically feasible trajectory.
