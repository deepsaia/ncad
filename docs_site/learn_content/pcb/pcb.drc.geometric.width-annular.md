Trace width and annular ring are the two feature-sizing rules that decide whether a conductor can carry its current safely and whether a drilled connection lands reliably on its pad. They are grouped together because both are constraints on the *minimum copper dimension* of a net, but they are driven by different physics: width by electrical and thermal capacity, annular ring by mechanical registration between the drilled hole and the copper pad around it.

## Conductor width and current capacity

A trace behaves as a resistive, self-heating conductor. Its steady-state current is limited by the temperature rise the designer will tolerate, because the copper both carries the current and dissipates the \(I^2R\) heat into the board. The long-standing empirical relationship expresses the allowable current as a function of cross-sectional area and temperature rise:

\[
I = k\,\Delta T^{0.44}\,A^{0.725},
\]

where \(I\) is in amperes, \(\Delta T\) is the permitted temperature rise in °C, \(A\) is the conductor cross-section in mils², and \(k \approx 0.048\) for external (surface) traces and \(\approx 0.024\) for internal traces, which are cooled less effectively. The cross-section is \(A = w \cdot t\), where the copper thickness \(t\) comes from the plating weight (1 oz/ft² ≈ 34.8 µm ≈ 1.37 mils). Inverting for the required width gives

\[
w = \frac{1}{t}\left(\frac{I}{k\,\Delta T^{0.44}}\right)^{1/0.725}.
\]

Modern current-capacity data supersedes those original charts, because the charts assumed a conductor in still air with no adjacent copper. Real boards conduct heat through the laminate and into planes, so newer test-based data parameterizes capacity by board thickness, dielectric conductivity, copper weight, and the presence of a nearby copper plane, typically allowing narrower traces than the conservative legacy curves. A width DRC therefore enforces a minimum width per net class (a power net gets a wider rule than a signal net), while permitting controlled *neck-downs* where a wide trace must pass a fine pitch, as long as the necked segment stays within thermal limits.

## Annular ring

The annular ring is the band of pad copper that remains around a plated hole after drilling. For a pad diameter \(D_p\) and finished hole diameter \(D_h\), the nominal ring width is

\[
a = \frac{D_p - D_h}{2}.
\]

The governing concern is **registration**: the drill position, the artwork-to-drill alignment, and layer-to-layer misregistration all vary within a tolerance stack, so the drill can land off-centre. If the accumulated error exceeds \(a\), the hole breaks out of the pad (tangency, then breakout), weakening or severing the connection. Acceptance criteria scale with the reliability class: the highest class typically requires a positive ring on every layer (for example on the order of 0.025 mm internal and 0.05 mm external) with no breakout permitted, while lower classes tolerate limited breakout. A DRC checks the minimum annular ring by comparing pad and hole geometry against the class rule, and often adds hole-to-copper and pad-to-pad checks so that shrinking a pad to gain clearance does not silently starve the ring. These rules matter most on dense boards with small vias, on high-layer-count stackups where misregistration accumulates, and on any high-reliability product where a marginal ring is a latent open.
