## What a sheet is

A drawing sheet is the fixed, bounded page on which one or more views of a model are laid out for documentation, review, and manufacture. It separates two coordinate worlds: model space, where geometry lives at true, unbounded 1:1 size in physical units, and sheet (paper) space, whose extent is a fixed physical rectangle. Everything placed on the sheet, including view borders, dimensions, notes, and the title block, is positioned in sheet coordinates, while the geometry inside each view is a scaled projection of model space.

Sheet formats standardize the page so drawings archive, print, fold, and reproduce predictably. The ISO A-series (A0 through A4) is built on a geometric progression: each size has half the area of the next larger one, obtained by halving the long side. Requiring the aspect ratio to be preserved under halving forces a unique ratio. If the long and short sides are \(L\) and \(S\), halving yields a page \(S \times L/2\) with the same ratio, so

\[ \frac{L}{S} = \frac{S}{L/2} \quad\Longrightarrow\quad \left(\frac{L}{S}\right)^2 = 2 \quad\Longrightarrow\quad \frac{L}{S} = \sqrt{2}. \]

A0 is fixed at an area of one square metre at that ratio (841 x 1189 mm). The inch-based series instead doubles a base 8.5 x 11 in page and alternates its aspect ratio between successive sizes.

## Scale

Scale is the linear mapping from model units to sheet units, written \(n{:}1\) for an enlargement or \(1{:}n\) for a reduction. If a view is drawn at scale factor \(s\), a model edge of true length \(\ell\) prints at length \(s\,\ell\). Crucially, scale is a display property of the view, not of the geometry: dimensions report the true model value regardless of the view scale, so a hole dimensioned 12 mm reads 12 mm whether its view is at 1:1 or 1:5. Multiple views on one sheet may each carry a different scale, and a detail view typically enlarges a local region while the main views stay at the sheet's nominal scale.

## Borders, zones, and the title block

A standard format supplies a border and frame, a zone grid (numbered along one edge and lettered along the other) for referencing regions of a large drawing, and a title block. The title block is the drawing's metadata record: part or document number, title, revision, sheet x of y, drawing scale, units, the projection-method symbol (first- or third-angle), material and finish, general tolerances, and approval signatures. Because this block is the authoritative identity and configuration record for the document, it is governed tightly by standards and by an organization's drawing-control process. Consistent formats and title blocks are what let a drawing be unambiguously identified, revised, and released across a supply chain.
