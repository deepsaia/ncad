"""Drive the input x op matrix through GuardedRunner and write results.json + report.md.

Each cell runs one probe on one input in a child process with a wall-clock timeout, so a hang
(#33561) or segfault is measured (timeout/crashed), not fatal. SOME CELLS WILL TIME OUT OR
CRASH BY DESIGN: that is the data this spike exists to collect, not a harness failure.

The corpus records ({name, path, input_class}) come from make_inputs.build_corpus, so this
driver never hardcodes part names (gate docs expand to parts like pattern_studs/spoke_hub).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from ncad.kernel.guarded_runner import GuardedRunner
from spikes.direct_modeling_4_0.make_inputs import build_corpus
from spikes.direct_modeling_4_0.probes import defeature_probe, move_face_probe, offset_probe

logger = logging.getLogger(__name__)

_HERE = Path(__file__).resolve().parent


def _cells_for(record: dict[str, Any]) -> list[dict[str, Any]]:
    """The matrix cells for one corpus record (a few target faces per face-indexed op)."""
    name = record["name"]
    input_class = record["input_class"]
    cells: list[dict[str, Any]] = []
    for face_index in (0, 1, 2):
        cells.append({"input": name, "input_class": input_class,
                      "op": "defeature", "face_index": face_index})
        cells.append({"input": name, "input_class": input_class,
                      "op": "move_face", "face_index": face_index, "delta": 3.0})
    for distance in (1.0, -1.0):
        cells.append({"input": name, "input_class": input_class,
                      "op": "offset", "distance": distance})
    return cells


def _dispatch(runner: GuardedRunner, cell: dict[str, Any], step_path: str) -> Any:
    op = cell["op"]
    if op == "defeature":
        return runner.run(defeature_probe, step_path, cell["face_index"])
    if op == "move_face":
        return runner.run(move_face_probe, step_path, cell["face_index"], cell["delta"])
    return runner.run(offset_probe, step_path, cell["distance"])


def _record_row(cell: dict[str, Any], guarded: Any) -> dict[str, Any]:
    """Fold a GuardedResult into a recorded-field row (verdict + disagreement)."""
    row: dict[str, Any] = {
        **cell,
        "outcome": guarded.outcome,
        "elapsed_s": round(guarded.elapsed_s, 3),
        "error": guarded.error,
    }
    if guarded.outcome != "ok" or not isinstance(guarded.value, dict):
        row["verdict"] = "FAIL"
        return row
    oracle = guarded.value
    if oracle.get("skipped"):
        # The probe self-skipped (e.g. face_index out of range): not a measured run.
        row["outcome"] = "skipped"
        row["verdict"] = "SKIP"
        return row
    # Carry the full oracle dict (flags + raw measures like before/after faces and volume) so
    # the envelope can be interpreted, then derive the verdict and disagreement from the flags.
    row.update(oracle)
    gate = bool(oracle.get("gate_pass"))
    sanity = bool(oracle.get("sanity_pass"))
    intent = bool(oracle.get("intent_pass"))
    row["verdict"] = "PASS" if (gate and sanity and intent) else "FAIL"
    row["disagreement"] = None if (gate == sanity == intent) else "gate_vs_reality"
    return row


def run_all(out_dir: str = "out", timeout_s: float = 20.0) -> list[dict[str, Any]]:
    """Build the corpus, run every matrix cell, and return the recorded-field rows."""
    corpus = build_corpus(out_dir)
    runner = GuardedRunner(timeout_s=timeout_s)
    rows: list[dict[str, Any]] = []
    for record in corpus:
        step_path = record["path"]
        for cell in _cells_for(record):
            cell["timeout_s"] = timeout_s
            if not os.path.exists(step_path):
                rows.append({**cell, "outcome": "skipped", "verdict": "SKIP"})
                continue
            guarded = _dispatch(runner, cell, step_path)
            row = _record_row(cell, guarded)
            rows.append(row)
            logger.info("%s/%s[%s] -> %s", record["name"], cell["op"],
                        cell.get("face_index", cell.get("distance")), row["verdict"])
    return rows


def _summarize(rows: list[dict[str, Any]]) -> str:
    """A per-(op, input_class) results table plus the #1315 disagreement count."""
    lines = ["# Direct-modeling spike results", ""]
    header = "| op | input_class | n | pass | fail | timeout | crashed | raised | skip | disagree |"
    lines.append(header)
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    keys = sorted({(r["op"], r["input_class"]) for r in rows})
    for op, klass in keys:
        group = [r for r in rows if r["op"] == op and r["input_class"] == klass]
        measured = [r for r in group if r.get("outcome") != "skipped"]
        n = len(measured)
        passed = sum(1 for r in measured if r.get("verdict") == "PASS")
        failed = sum(1 for r in measured if r.get("verdict") == "FAIL")
        timeout = sum(1 for r in measured if r.get("outcome") == "timeout")
        crashed = sum(1 for r in measured if r.get("outcome") == "crashed")
        raised = sum(1 for r in measured if r.get("outcome") == "raised")
        skip = sum(1 for r in group if r.get("outcome") == "skipped")
        disagree = sum(1 for r in measured if r.get("disagreement"))
        lines.append(
            f"| {op} | {klass} | {n} | {passed} | {failed} | {timeout} | {crashed} "
            f"| {raised} | {skip} | {disagree} |"
        )
    total_disagree = sum(1 for r in rows if r.get("disagreement"))
    total_measured = sum(1 for r in rows if r.get("outcome") != "skipped")
    lines.append("")
    lines.append(
        f"Gate-vs-reality disagreements (BRepCheck valid but sanity/intent failed): "
        f"{total_disagree} of {total_measured} measured runs (the OCCT #1315 incidence)."
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    rows = run_all()
    (_HERE / "results.json").write_text(json.dumps(rows, indent=2))
    (_HERE / "report.md").write_text(_summarize(rows))
    print(f"wrote {_HERE / 'results.json'} and {_HERE / 'report.md'}")


if __name__ == "__main__":
    main()
