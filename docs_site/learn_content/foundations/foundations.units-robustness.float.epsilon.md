Computers approximate the real numbers with a finite set of **floating-point** values. Under the IEEE 754 standard, a binary floating-point number is stored as a sign, a significand (mantissa), and an exponent, representing \( \pm m \times 2^{e} \) with a fixed number of significand bits. The near-universal double-precision format (binary64) uses 52 stored significand bits plus one implicit leading bit, giving 53 bits of precision, roughly 15 to 16 significant decimal digits. Because the exponent shifts the spacing, representable numbers are *not* evenly distributed: they are dense near zero and coarse at large magnitudes, so the absolute gap between consecutive values grows with the value itself.

## Machine epsilon and ULP

**Machine epsilon**, \( \varepsilon \), quantifies this granularity. It is the gap between \( 1.0 \) and the next larger representable number, equal to \( 2^{-52} \approx 2.22 \times 10^{-16} \) for binary64. Equivalently, correctly rounded arithmetic guarantees a relative error bounded by the *unit roundoff* \( u = \varepsilon/2 \): for any elementary operation \( \circ \in \{+,-,\times,\div\} \),

\[ \mathrm{fl}(a \circ b) = (a \circ b)(1 + \delta), \qquad |\delta| \le u = 2^{-53}. \]

The closely related notion of a **ULP** (unit in the last place) is the spacing between adjacent floats near a given magnitude; expressing error in ULPs makes it scale-independent. The essential consequence is that most real numbers, including simple decimals like \( 0.1 \), have no exact binary representation, and every operation may introduce a rounding error of order \( u \).

Because of this, **exact equality comparison of computed floats is almost always a bug**. Two mathematically equal quantities reached by different arithmetic paths will generally differ in their last bits, so tests must use a **tolerance**. A robust comparison blends an absolute and a relative bound,

\[ |a - b| \le \max\big(\tau_{\text{abs}},\; \tau_{\text{rel}} \cdot \max(|a|, |b|)\big), \]

where the absolute term \( \tau_{\text{abs}} \) handles values near zero (where relative error is meaningless) and the relative term \( \tau_{\text{rel}} \), typically a small multiple of \( \varepsilon \), handles large magnitudes. Choosing these thresholds is a modeling decision: too tight and coincident features are seen as distinct; too loose and genuinely separate features are merged.

Errors do not merely accumulate linearly, they can be *amplified*. **Catastrophic cancellation** occurs when subtracting two nearly equal numbers: the leading significant digits cancel, promoting previously negligible rounding error into the most significant surviving digits and destroying relative accuracy. The sensitivity of a result to such effects is captured by the **condition number** of the problem, while the quality of an algorithm is described by its numerical **stability**; an unstable algorithm can ruin a well-conditioned problem. Practical engineering software therefore designs comparisons and formulas with these facts in mind, using scale-aware tolerances derived from the model's size, reformulating cancellation-prone expressions, and, where the outcome is combinatorial rather than numeric, escalating to the exact techniques of geometric robustness.
