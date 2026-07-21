## Tables on a drawing

A table gathers structured, repeating information into rows and columns on the sheet rather than scattering it across notes. The common kinds each answer a specific question. A bill of materials (BOM), or parts list, enumerates the components of an assembly: item number, quantity, part number, description, and often material or reference designator, with the item numbers keyed to the balloons in the views. A hole table lists each hole's identifier, its X and Y coordinates from a common origin, and its size, and is the natural companion to ordinate dimensioning when a plate has dozens of holes. A revision table records the document's change history: revision letter, description, date, and approval.

## Associativity and roll-up

The professional expectation is that these tables are live queries into a single source of truth, not manually retyped text. A BOM is generated from the assembly structure, so its quantities and part numbers reflect the actual model; a hole table reads coordinates directly from the features; a revision block ties to the drawing's controlled revision state. When the model changes, for instance a component is added or a hole is moved, the associated table updates on rebuild, which eliminates a large class of transcription errors and keeps the drawing consistent with what will actually be built.

Quantity roll-up follows the assembly's part-occurrence graph. If an assembly \(a\) contains each subassembly \(k\) with multiplicity \(n_{a\to k}\), and each \(k\) contains component \(c\) with multiplicity \(m_{k\to c}\), the total count of \(c\) is

\[ Q(c) = \sum_{k} n_{a\to k}\, m_{k\to c}, \]

applied recursively down the tree. BOMs expose this in different forms: a top-level (parts-only) list shows just the immediate children, while an indented or exploded structured list walks the full tree and can show total or per-parent quantities. Because the numbers are computed from structure rather than entered by hand, the same master model can drive an assembly BOM, a purchasing list, and per-sheet callouts that all agree.
