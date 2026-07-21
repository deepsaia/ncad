**Chip load** is the thickness of material each cutting edge removes, and it is the true control variable of chip formation. Nominally it equals the feed per tooth \(f_z\), but the *instantaneous* uncut chip thickness in milling varies through the cut. As a flute sweeps from entry to exit, its immersion angle \(\varphi\) changes and the chip thickness follows

\[ h(\varphi) = f_z\, \sin\varphi , \]

so the chip starts thin and thickens (or the reverse, depending on climb versus conventional). This sinusoidal variation is why milling forces are inherently pulsating and why the *average* chip thickness, not the peak, is what one compares against a recommended value.

Chip load must be kept inside a working band. Too small and the edge **rubs** rather than cuts: below the tool's minimum chip thickness (a fraction of the edge radius) the material plows and elastically recovers instead of shearing, generating heat, work-hardening the surface, and accelerating flank wear. Too large and the edge sees excessive force and risks chipping or breakage. Productive, tool-friendly cutting lives between these limits, which is why simply reducing feed to be safe can paradoxically destroy tools.

The most important practical correction is **radial chip thinning**. When the radial engagement (stepover) \(a_e\) is less than the tool radius, the arc of contact is short and the flute never reaches full immersion, so the *actual* average chip thickness is smaller than the programmed \(f_z\). To restore the intended chip thickness, the feed per tooth is scaled up by a **radial chip-thinning factor**

\[ f_{z,\text{prog}} = f_{z,\text{desired}}\cdot \frac{1}{\sqrt{\,1-\left(1-\dfrac{2 a_e}{D}\right)^{2}}} = f_{z,\text{desired}}\cdot\frac{D}{2\sqrt{a_e\,(D-a_e)}} . \]

At light radial engagement this factor is large, which is exactly why high-efficiency and trochoidal strategies deliberately run small \(a_e\) at high feed: the thin engagement lets feed climb while keeping the chip, and therefore the edge load and heat, near optimal. Neglecting the correction leaves the edge rubbing, hot, and short-lived.

A companion effect, **axial chip thinning**, applies to ball nose and radiused tools taking a shallow axial depth: the effective cutting diameter and the geometry of the round edge reduce chip thickness for a given \(f_z\), again calling for a feed increase to hit the target chip load. In both cases the principle is the same: the controller is fed \(f_z\), but the physics respond to the geometric chip thickness, and a competent feed calculation converts between the two rather than treating them as equal.
