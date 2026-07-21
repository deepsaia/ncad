Additive manufacturing (AM) builds a part by adding material, almost always in thin layers, directly from a digital solid model. Instead of asking what to remove, the process asks where to place material and how to fuse it to what is already there. This inverts the reachability problem of subtractive work: internal cavities, lattices, and conformal channels that no tool could reach become straightforward, while new constraints appear around overhangs, thermal history, and layer bonding.

The field is organized by a standardized taxonomy of **seven process categories**: material extrusion, vat photopolymerization, powder-bed fusion, directed energy deposition, binder jetting, material jetting, and sheet lamination. They differ in feedstock (filament, resin, powder, wire, sheet) and in the binding mechanism (thermal fusion, photopolymerization, chemical binder, sintering), but all reduce a 3D solid to a stack of 2D layers through **slicing**. Each layer is decomposed into a boundary contour plus an interior fill, and the fill pattern, hatch spacing, and layer thickness \(t\) become the primary levers on strength, density, and build time.

## Energy input and layer discretization

For fusion-based processes a useful first-order descriptor is the **volumetric energy density**, the energy delivered per unit of consolidated material,

\[ E_v = \frac{P}{v\, h\, t}, \]

where \(P\) is beam power, \(v\) scan speed, \(h\) hatch spacing, and \(t\) layer thickness. Too little energy leaves lack-of-fusion porosity; too much drives keyholing and vaporization. The layered nature of the build also makes properties **anisotropic**: bonds within a layer are generally stronger than bonds between layers, so orientation on the build plate is a design decision, not a convenience.

Geometry that overhangs beyond a critical angle cannot be deposited onto empty space and requires **support structures** that anchor the region and conduct heat away; these are consumed as scrap and drive post-processing. Residual stress from repeated local heating and cooling can warp thin walls or detach a part from the plate, so build orientation, support strategy, and scan pattern are chosen together to manage the thermal field.

AM matters most where geometric freedom pays for itself: consolidated assemblies printed as one piece, internal cooling passages, topology-optimized load paths, and low-volume or patient-specific parts. It is comparatively weak on large flat surfaces, on the finish and tolerance achievable directly off the machine (which usually still need a finishing cut), and on the tight, validated property control that mature wrought-and-machined routes provide.
