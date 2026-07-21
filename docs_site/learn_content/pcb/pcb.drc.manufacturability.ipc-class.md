Where geometric and connectivity checks ask whether a design is internally consistent, manufacturability checks ask whether a specific fabricator can reliably build it and whether the finished board meets a stated reliability grade. The framing standard for this is the **performance class**, a three-tier scheme that sets the acceptance criteria a board must satisfy, coupled to a set of **fabrication constraints** derived from the shop's process capability.

## The three performance classes

The classes describe the end product's reliability demand, not its complexity:

- **Class 1 (General Electronic Products)**: consumer-grade items where the main requirement is that the assembly functions. The loosest acceptance criteria; cosmetic and minor conductor imperfections are tolerated.
- **Class 2 (Dedicated Service Electronic Products)**: equipment expected to perform reliably over a long life, with limited tolerance for defects, but where uninterrupted service is not critical.
- **Class 3 (High-Reliability Electronic Products)**: hardware that must function on demand, such as life-support, aerospace, and safety systems. The tightest criteria.

The class does not change what the board *does*; it tightens the numbers a fabricator must hold. Higher classes demand a positive annular ring on every layer with no breakout, greater minimum copper plating in the plated-through hole (on the order of 20 µm for Classes 1–2 versus 25 µm average for Class 3), less permitted conductor nicking and etch reduction, and stricter registration and defect limits. A Class-3 ruleset is therefore a superset of Class-2 requirements with smaller allowances.

## Producibility levels and fabrication constraints

Separate from reliability class, designs are graded by **producibility level** (Level A general/low density, Level B moderate, Level C high complexity/high density). These levels attach concrete minimums to features such as minimum trace width and spacing, minimum drilled-hole diameter, and minimum annular ring: Level C permits finer geometry but presumes a more capable, more expensive process. A design-for-manufacture (DFM) check enforces the intersection of the chosen class, the chosen producibility level, and the target shop's stated capability, testing constraints that the pure geometric checks do not, including:

- minimum trace width and minimum copper spacing the etch process can hold;
- minimum drill diameter and the **aspect ratio**, the board thickness divided by the finished hole diameter, \( \text{AR} = t_{\text{board}} / d_{\text{hole}} \), which must stay below the plating limit (commonly \(\le 8{:}1\), higher only for advanced processes) so that plating chemistry can reach the centre of the hole;
- minimum solder-mask sliver and mask-to-copper clearance so the mask neither cracks off nor exposes adjacent copper;
- minimum silkscreen line width and copper-to-board-edge clearance so routing and legend survive fabrication.

The practical consequence is that the manufacturability ruleset is parameterized: a designer selects a performance class and a fabricator capability profile, and the DRC engine loads the corresponding limits. This lets the same layout be validated against, say, a low-cost Class-2 prototype shop or a Class-3 qualified line, and it turns otherwise-invisible process risk (unfillable holes, tented-via failures, mask breakdown) into explicit, checkable violations before the board is ever sent out.
