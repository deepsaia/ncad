Fatigue is the progressive, localized damage that accumulates in a material subjected to repeated loading, culminating in cracking and fracture at stress amplitudes well below the static strength. It dominates the durability of almost everything that cycles: shafts, springs, airframes, welds, and pressure equipment. Fatigue and durability assessment sits downstream of stress analysis, converting a stress or strain history into a predicted life (cycles or hours) or a safety margin.

## Stress-life and strain-life

Two complementary approaches cover the range of severity. The **stress-life (S-N)** method correlates a cyclic stress amplitude \(S_a\) with cycles to failure \(N\), typically as a power law (Basquin's relation) \(S_a = \sigma_f'\,(2N)^b\); it governs high-cycle fatigue where response is essentially elastic and many steels exhibit an endurance (fatigue) limit below which life is effectively infinite. The **strain-life** method uses total strain amplitude and is required for low-cycle fatigue, where local plasticity is significant, via the Coffin-Manson relation

\[ \frac{\Delta\varepsilon}{2} = \frac{\sigma_f'}{E}\,(2N_f)^{b} + \varepsilon_f'\,(2N_f)^{c}, \]

which adds an elastic term and a plastic term. Because real service loads are rarely constant amplitude, a mean stress correction (Goodman, Gerber, Morrow, or Smith-Watson-Topper) is applied to account for the strongly detrimental effect of tensile mean stress.

## Cycle counting and cumulative damage

A measured or simulated load history is an irregular sequence, not a set of clean cycles, so it must first be reduced to equivalent closed cycles. **Rainflow counting**, standardized in ASTM E1049, is the accepted algorithm: it pairs reversals into hysteresis loops so that each is matched with a range and mean. The counted cycles are then accumulated with the linear **Palmgren-Miner rule**,

\[ D = \sum_i \frac{n_i}{N_i}, \qquad \text{failure at } D = 1, \]

where \(n_i\) is the number of applied cycles at level \(i\) and \(N_i\) the allowable cycles at that level from the S-N curve. Miner's rule ignores load sequence effects and is only an engineering approximation, but it remains the backbone of practical life prediction.

## Factors, notches, and scope

Laboratory S-N data come from polished specimens, so design life must be corrected for the real part: surface finish, size, loading type, temperature and corrosive environment, and above all stress concentrations. Notches are handled with a fatigue notch factor \(K_f\) (related to, but smaller than, the elastic stress concentration \(K_t\)) or with local strain approaches at the notch root. Welds are treated with their own detail-category S-N curves. Because fatigue depends on microstructure, residual stress, manufacturing, and load spectra that a stress solver does not know, credible durability assessment is a specialist discipline built on top of the structural analysis rather than a direct output of it.

<svg viewBox="0 0 250 160" role="img" aria-label="Schematic S-N curve: stress amplitude versus cycles to failure, leveling to an endurance limit">
  <line x1="35" y1="12" x2="35" y2="128" stroke="currentColor" fill="none"/>
  <line x1="35" y1="128" x2="235" y2="128" stroke="currentColor" fill="none"/>
  <path d="M45 28 C 95 55, 135 92, 175 100 L 230 100" stroke="currentColor" fill="none"/>
  <line x1="175" y1="100" x2="230" y2="100" stroke="currentColor" fill="none" stroke-dasharray="3 3"/>
  <text x="14" y="22" font-size="10" fill="currentColor">S_a</text>
  <text x="200" y="146" font-size="10" fill="currentColor">log N</text>
  <text x="120" y="118" font-size="9" fill="currentColor">endurance limit</text>
</svg>
