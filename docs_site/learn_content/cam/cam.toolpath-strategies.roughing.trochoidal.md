Trochoidal milling clears material, especially **slots and narrow channels**, by superimposing a circular (looping) motion on the tool's linear advance so the cutter traces a series of overlapping arcs rather than plowing straight down the slot. The result is a path resembling a stretched cycloid. Its purpose is to convert a full-slot cut, where a straight tool would be at 100% radial immersion with no room to eject chips, into a sequence of light, curved engagements that never exceed a small controlled arc of contact.

The center of the tool follows a curtate trochoid: a point advancing at feed rate \(v_f\) while orbiting a circle of radius \(a\) at angular rate \(\omega\),

\[ x(t) = v_f\,t + a\cos\omega t, \qquad y(t) = a\sin\omega t. \]

The linear advance per loop is the **step** \(\delta = 2\pi v_f/\omega\). Because the tool only touches the far wall over the leading portion of each loop, the maximum radial engagement, and thus the peak chip load, is set by \(\delta\) and the loop radius \(a\) rather than by the slot width. Making \(\delta\) small keeps engagement low; the price is more revolutions of the loop per unit length of slot and therefore a longer path. Trochoidal milling is thus the slot-specific member of the constant-engagement (HSM) family, sharing its physics with adaptive clearing.

Because each engagement is brief and light, the flutes spend most of each loop out of contact, which lets the chips clear and the tool cool, and it permits the **full flute length** to be used as axial depth. That distributes wear along the whole cutting edge instead of concentrating it, extends tool life, and lets a small-diameter cutter machine a slot much wider than itself (the slot width is covered by the loop diameter plus the tool). It is the standard remedy for deep slots, keyways, and hard-material grooves where a plunge or a straight slotting cut would trap chips and burn the tool.

## Relation to adaptive clearing

Trochoidal and adaptive clearing are often conflated because both cap the engagement angle, but they differ in scope: trochoidal is a fixed geometric loop pattern applied to open channels and slots, whereas adaptive clearing is a general area-clearing strategy that inserts trochoidal-like moves only where the topology would otherwise cause over-engagement. In modern practice a roughing operation blends the two, running efficient offset passes in open areas and switching to trochoidal loops in slots and corners to keep the load uniform throughout.
