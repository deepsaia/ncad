"""Golden-spec regression: pin the generator's exact output for a fixed seed+params.

Distinct from the determinism test (two runs agree): this pins the *actual* output, so a
change to the generation algorithm — even one that stays internally deterministic — is
caught here. If a change to output is intended, regenerate the golden file deliberately.
"""

import json
from pathlib import Path

from ncad.generate.generator import Generator

_GOLDEN_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "golden_spec_seed42.json"
_PARAMS = {"width": 12.0, "depth": 9.0, "num_rooms": 4, "storey_height": 3.0}
_SEED = 42


def test_generator_matches_golden_spec() -> None:
    spec = Generator(_PARAMS).generate(seed=_SEED)

    golden = json.loads(_GOLDEN_PATH.read_text())
    # Round-trip through JSON so tuple/list and int/float compare like the stored form.
    actual = json.loads(json.dumps(spec))

    assert actual == golden, (
        "generated spec drifted from the golden fixture. If intended, regenerate "
        f"{_GOLDEN_PATH.name} and review the diff."
    )
