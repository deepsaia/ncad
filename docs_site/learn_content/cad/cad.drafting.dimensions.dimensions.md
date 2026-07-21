## Driving versus driven dimensions

A dimension states the size or location of a feature. In a parametric workflow the distinction between driving and driven dimensions matters. Driving (sketch or constraint) dimensions are inputs: their values control the geometry, and changing one moves the model. Driven (reference) dimensions are outputs: they measure whatever the current geometry is and update on rebuild, but cannot be edited to change the model. Drawing dimensions are normally driven and associative, so they always report the true model value. A value carried purely for information is marked as a reference dimension by enclosing it in parentheses, for example (25), signalling that it is not to be used for inspection or manufacture.

## Chain, baseline, and ordinate

Three schemes locate a series of features along an axis. Chain (continuous) dimensioning measures each feature from the previous one, end to end. Baseline (parallel) dimensioning measures every feature from one common origin or datum. Ordinate (coordinate) dimensioning also references a single origin but omits dimension lines entirely, labelling each feature with its coordinate value; it suits plates with many holes and pairs naturally with a hole table.

The choice is not cosmetic, because it governs how manufacturing tolerances accumulate. With a chain of \(n\) links, each of tolerance \(\pm\delta_i\), the position of the last feature relative to the first has a worst-case tolerance equal to the sum of the links,

\[ \Delta_{\text{chain}} = \sum_{i=1}^{n}\delta_i, \]

so error piles up along the chain. Baseline dimensioning removes this accumulation: because every feature is tied to the same origin, the location tolerance of each feature is just its own \(\delta_i\), independent of its neighbors. When the individual variations are independent random variables, a statistical root-sum-square estimate is often used instead of the worst case,

\[ \Delta_{\text{RSS}} = \sqrt{\sum_{i=1}^{n}\delta_i^{2}}, \]

which is smaller than the arithmetic sum and better reflects realistic process spread. Understanding this stack-up is why precision hole patterns are almost always baseline- or ordinate-dimensioned rather than chained.

## Why it matters

Dimensioning encodes design intent for the shop floor and for inspection. A well-dimensioned drawing avoids over-dimensioning (redundant, potentially conflicting values), locates each feature exactly once, and chooses the scheme whose tolerance behavior matches the function of the part.
