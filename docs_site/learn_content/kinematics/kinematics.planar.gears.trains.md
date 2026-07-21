A **gear train** is any set of meshing gears used to obtain a desired speed ratio, torque multiplication, or direction of rotation between an input and an output shaft. The building block is a single mesh, for which the speed ratio is the inverse ratio of tooth numbers, since meshing gears share the same pitch-line velocity: two gears with tooth counts \(N_1\) and \(N_2\) satisfy \(\omega_1 N_1 = \omega_2 N_2\).

## Simple, compound, and reverted trains

In a **simple train** each shaft carries one gear, and idler gears between the first and last change only the sign (direction), not the magnitude, of the ratio. In a **compound train** two or more gears share a shaft, so their tooth counts multiply, allowing large ratios in a modest package. The overall **train value** \(e\) is the product of the individual tooth-number ratios,

\[ e = \frac{\omega_{\text{out}}}{\omega_{\text{in}}} = (\pm 1)\prod \frac{N_{\text{driver}}}{N_{\text{driven}}}, \]

where the sign accounts for the number of external meshes (each external mesh reverses direction; an internal mesh preserves it). A **reverted** train is a compound train whose input and output are coaxial, a common requirement in transmissions and clocks, which imposes an additional center-distance constraint on the tooth counts.

## Epicyclic (planetary) trains

An **epicyclic** or **planetary** train allows one or more gears, the **planets**, to have moving axes: they are carried on an arm (the **carrier** or planet carrier) that itself rotates. A typical single-stage set has a central **sun** gear, several planets meshing with it, an internal-tooth **ring** (annulus) gear, and the carrier. Concentricity requires the tooth counts to satisfy

\[ N_{\text{ring}} = N_{\text{sun}} + 2\,N_{\text{planet}}. \]

Because a planet axis moves, absolute gear ratios cannot be read off directly. The standard method superposes motions, expressed compactly by the **train (Willis) equation**

\[ \frac{\omega_L - \omega_A}{\omega_F - \omega_A} = e, \]

where \(A\) is the carrier (arm), \(F\) and \(L\) are the first and last gears of the train taken *as if the carrier were fixed*, and \(e\) is that fixed-carrier train value. This single equation, together with fixing or driving two of the three coaxial members (sun, ring, carrier), solves any planetary stage.

Epicyclic trains matter because they deliver very high reduction ratios in a compact, coaxial, load-sharing package: multiple planets split the torque among several meshes, reducing tooth loads and giving good power density. Having three input/output ports also makes them the basis of differentials (splitting one input into two outputs, as in a vehicle drive axle) and of automatic transmissions, where selectively holding or releasing the sun, ring, or carrier with brakes and clutches produces different gears from one compact set.
