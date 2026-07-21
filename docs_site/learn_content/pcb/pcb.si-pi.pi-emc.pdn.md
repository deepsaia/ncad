The **Power Distribution Network (PDN)** is the entire path that carries current from the voltage regulator to the switching transistors of an IC and back: the regulator, bulk capacitors, plane pairs, decoupling capacitors, vias, package, and on-die capacitance. Its job is to hold the supply rail steady while loads draw current that changes by amperes in nanoseconds. Every switching event pulls charge through the network's inductance, and by \(V = L\,di/dt\) that transient demand produces a voltage droop or bounce on the rail. The PDN's purpose is to keep this ripple inside the IC's tolerance across all frequencies of interest.

The unifying design metric is **target impedance**. Given an allowed ripple \(\Delta V\) (a fraction of \(V_{dd}\)) and a worst-case transient current \(\Delta I\), the PDN impedance seen by the load must satisfy

\[ Z_{\text{target}} = \frac{\Delta V}{\Delta I} = \frac{V_{dd}\cdot(\text{ripple \%})}{\Delta I} \]

over the full bandwidth from DC up to the highest frequency the current step contains. Because the tolerated ripple is small and the currents are large, \(Z_{\text{target}}\) is often in the low milliohm range, and it must be met flat across many decades of frequency, not just at one point. This is far harder than it looks, because no single component is low-impedance everywhere.

## Decoupling as a Frequency-Domain Problem

Each element covers a band. The regulator holds the rail at DC and low frequency; **bulk capacitors** cover kHz to low MHz; **ceramic decoupling capacitors** cover MHz to tens of MHz; the **power/ground plane capacitance** and finally the **on-package and on-die capacitance** cover the highest frequencies where nothing external can respond fast enough. A real capacitor is not ideal: it is a series RLC with equivalent series resistance (ESR) and equivalent series inductance (ESL), and its impedance is

\[ Z(\omega) = \text{ESR} + j\!\left(\omega \,\text{ESL} - \frac{1}{\omega C}\right), \qquad f_{\text{res}} = \frac{1}{2\pi\sqrt{\text{ESL}\cdot C}} \]

Below self-resonance it looks capacitive; above it, the mounting and package inductance dominate and it looks inductive and useless. Effective decoupling therefore means **staggering capacitor values** so each takes over as the previous one runs out, and above all minimizing mounting inductance (short, wide traces; vias close to pads; capacitors on the same side as the IC or directly beneath) because ESL, not capacitance, sets the high-frequency floor.

The hazard of combining many capacitors is **anti-resonance**: where the inductive tail of one capacitor bank meets the capacitive rise of the next, their parallel combination forms a resonant peak that spikes the PDN impedance above \(Z_{\text{target}}\). Good PDN design flattens these peaks by choosing overlapping values, adding ESR (or a deliberately lossy part) to damp the resonance, and using plane capacitance to fill the gap. The result is a PDN impedance profile that stays under the target line across the whole band, so that whatever current spectrum the load draws, the resulting voltage noise stays within budget.
