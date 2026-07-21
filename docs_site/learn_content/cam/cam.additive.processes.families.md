The many additive processes are organized by the physical mechanism that adds and consolidates material, not by machine brand or feedstock. The ratified terminology standard groups all of them into seven process categories; the four families named here map onto three of those categories, and understanding the underlying physics explains their distinct capabilities and limitations.

## Material extrusion (FDM / FFF)

In material extrusion, a thermoplastic filament is heated above its glass-transition or melt temperature, forced through a nozzle, and deposited as a bead that fuses to adjacent and underlying beads as it cools. Interlayer strength is governed by polymer *reptation*: diffusion of chain segments across the weld interface during the brief interval the contact stays above the mobility temperature. Because welding is time- and temperature-limited and beads have finite width, parts are strongly anisotropic (weakest across layers) and surface finish is dominated by bead geometry and the staircase effect. It is the most accessible family, with an open ecosystem where the trademarked term and its generic equivalent describe the same physics.

## Vat photopolymerization (SLA / DLP)

Vat processes cure a liquid photopolymer resin by spatially controlled light. A scanned laser point or a projected image (frame at a time) delivers exposure that triggers free-radical or cationic polymerization above a critical dose. The depth of cure follows the exposure working curve

\[ C_d = D_p\,\ln\!\left(\frac{E}{E_c}\right), \]

where \(C_d\) is cure depth, \(D_p\) the resin's penetration depth, \(E\) the delivered exposure, and \(E_c\) the critical exposure for gelation. The logarithm shows that cure depth grows slowly with exposure, so layer thickness and overcure (bonding to the prior layer) are set by controlling \(E\). These processes deliver the finest feature resolution and smoothest surfaces, limited by optical spot or pixel size and by resin diffusion, and require post-cure and support removal.

## Powder bed fusion (SLS / DMLS / SLM)

Powder-bed processes spread a thin layer of powder and fuse selected regions with a thermal source, usually a laser or electron beam. Polymer powder is *sintered* (SLS): particles coalesce by viscous flow below full melting, and the surrounding loose powder self-supports the part. Metal powder is fully *melted* (the melt-based variants) into a dense pool that solidifies, which demands inert atmosphere, support structures for heat conduction and stress control, and careful management of the melt-pool. The controlling process quantity is the volumetric energy density

\[ E_v = \frac{P}{v\,h\,t}, \]

with laser power \(P\), scan speed \(v\), hatch spacing \(h\), and layer thickness \(t\); too little energy leaves lack-of-fusion porosity, too much causes keyholing and vaporization. Powder-bed fusion produces the strongest, most nearly isotropic, and functionally end-use parts, especially in metal, at the cost of thermal complexity, residual stress, and post-processing.

## Choosing a family

The families trade resolution, material range, mechanical performance, and cost along predictable lines: extrusion is cheapest and most flexible but anisotropic and coarse; vat is highest resolution but limited to photopolymers with modest long-term properties; powder-bed fusion is strongest and most versatile in engineering materials but the most capital- and process-intensive. Process planning downstream of design (slicing, supports, orientation) is tailored to whichever mechanism is in play, which is why the standardized category, rather than a product name, is the right level at which to reason about capability.
