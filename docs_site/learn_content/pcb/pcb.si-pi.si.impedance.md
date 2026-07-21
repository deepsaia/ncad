A copper trace on a printed circuit board stops behaving like a simple wire once the signal's rise time becomes comparable to the round-trip propagation delay along it. At that point the interconnect is a **transmission line**: a distributed structure whose voltage and current are governed by wave propagation rather than by a lumped resistance. The rule of thumb is that a line must be treated as distributed when its electrical length exceeds roughly one-sixth to one-tenth of the signal's rise-time distance, i.e. when \( t_{\text{prop}} \gtrsim t_r / 6 \). Below that threshold the line is electrically short and lumped analysis suffices; above it, reflections and impedance matter.

The distributed line is modeled by its per-unit-length inductance \(L\), capacitance \(C\), series resistance \(R\), and shunt conductance \(G\). The **telegrapher's equations** relate voltage and current along position \(x\):

\[ \frac{\partial V}{\partial x} = -\left(R + j\omega L\right) I, \qquad \frac{\partial I}{\partial x} = -\left(G + j\omega C\right) V \]

For a low-loss line at digital frequencies (\(R \ll \omega L\), \(G \ll \omega C\)) the **characteristic impedance** reduces to the familiar

\[ Z_0 = \sqrt{\frac{L}{C}}, \qquad v_p = \frac{1}{\sqrt{LC}} = \frac{c}{\sqrt{\varepsilon_r^{\text{eff}}}} \]

where \(v_p\) is the propagation velocity set by the effective dielectric constant of the surrounding material. \(Z_0\) is a property of geometry and dielectric, not of length: it is the ratio the line presents to a wavefront before any reflection returns.

## Controlled Impedance and Reflections

"Controlled impedance" means fabricating traces so that \(Z_0\) holds a specified value (commonly 50 ohm single-ended, or 90 to 100 ohm differential) within a tolerance, typically by dimensioning trace width, dielectric thickness, and copper weight together and specifying the substrate's dielectric constant. The two dominant geometries are **microstrip** (a trace over a single reference plane, with air on one side) and **stripline** (a trace buried between two planes). Their impedance depends on width \(w\), dielectric height \(h\), copper thickness \(t\), and \(\varepsilon_r\); closed-form approximations exist but field-solver extraction is used for accuracy.

Why control it? Wherever the instantaneous impedance changes, part of the wave reflects. At a junction from \(Z_0\) into a load \(Z_L\) the **reflection coefficient** is

\[ \Gamma = \frac{Z_L - Z_0}{Z_L + Z_0} \]

Reflections cause overshoot, ringing, and stair-step waveforms that erode timing and voltage margins. **Termination** cancels them: a series resistor at the source raising the driver output to \(Z_0\), or a parallel resistor at the receiver matching \(Z_0\), drives \(\Gamma \to 0\). Impedance discontinuities from vias, connectors, stubs, and stackup transitions are the practical enemy of high-speed links, so controlled-impedance routing plus deliberate termination is the foundation of clean signaling.

Note that \(Z_0\) and its verification (coupon measurement, TDR, field-solver checks) are **electrical/physics analyses**, distinct from the geometric design-rule checks (clearance, width, spacing) a layout tool enforces. Impedance targets are captured as constraints and validated against the fabricated stackup rather than derived from routing geometry alone.
