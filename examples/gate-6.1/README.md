# Gate 6.1: motion outputs (traces, measures, mobility)

Bucket 6.1 adds the motion OUTPUTS design section 8 calls for, on top of the 6.0 trajectory:

- **trace curves** - the world path a chosen point sweeps over the motion;
- **measures over time** - a declared measurement (coordinate / distance / angle / swept volume)
  sampled per frame;
- **a mobility (DoF) report** - the planar Gruebler count next to the static solve's rest-pose DoF.

Outputs are OPTIONAL and additive: they are declared in an `outputs { traces = [...],
measures = [...] }` block in the `.motion.hocon`, and a motion doc without that block just produces
the trajectory (as the gate-6.0 crank-slider and four-bar do). The mobility report is always emitted
(a cheap legibility line). This is the single gate that exercises the outputs; other gates stay
outputs-free.

## reciprocating_pump

A crank-driven reciprocating (plunger) pump: `flywheel` (crank) + `rod` (bronze) + `plunger` +
`pump_body`, 3 revolute + 1 slider in one closed chain, driven one flywheel revolution. Kinematically
it is a crank-slider; as a PUMP its `.motion.hocon` adds the outputs:

- a **trace** `crownPath` on the plunger crown (a straight reciprocating line, contrasting with the
  four-bar's curved coupler trace);
- a **coordinate** measure `stroke` (the crown's world-Y over time, mm);
- a **swept_volume** measure `displacement = swept_volume(of=stroke, bore_d=28)` - the displaced
  volume in mL.

The gate test asserts the pump assembles clash-free at rest, the `stroke` series reproduces the
closed-form crank-slider stroke `yP = R sin(theta) + sqrt(L^2 - (R cos theta)^2)` within 1 mm at
every one of the 73 frames, `displacement.value` equals the full stroke `2R` times the bore area in
mL, the `crownPath` trace has one point per frame and stays a straight line, the mobility is 1 DoF
(mobile), and the whole thing is deterministic across two runs. All of this emerges from the declared
joints + one driver + a post-processing pass over the trajectory - no per-mechanism formula, no
re-solve.
