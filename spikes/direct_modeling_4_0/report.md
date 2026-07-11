# Direct-modeling spike results

| op | input_class | n | pass | fail | timeout | crashed | raised | skip | disagree |
|---|---|---|---|---|---|---|---|---|---|
| defeature | real_filleted | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| defeature | real_multibody | 27 | 0 | 27 | 0 | 0 | 0 | 0 | 27 |
| defeature | synthetic_sliver | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| defeature | synthetic_tangent | 3 | 1 | 2 | 0 | 0 | 0 | 0 | 2 |
| defeature | synthetic_thinwall | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| move_face | real_filleted | 3 | 1 | 2 | 0 | 0 | 0 | 0 | 2 |
| move_face | real_multibody | 27 | 26 | 1 | 0 | 0 | 0 | 0 | 1 |
| move_face | synthetic_sliver | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| move_face | synthetic_tangent | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| move_face | synthetic_thinwall | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| offset | real_filleted | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| offset | real_multibody | 18 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |
| offset | synthetic_sliver | 2 | 1 | 1 | 0 | 0 | 1 | 0 | 0 |
| offset | synthetic_tangent | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| offset | synthetic_thinwall | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |

Gate-vs-reality disagreements (BRepCheck valid but sanity/intent failed): 38 of 104 measured runs (the OCCT #1315 incidence).
