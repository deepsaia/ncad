# gate-3.1: transforms

- `transformed_blocks.hocon` - a base block rotated in place, then a scaled COPY added as a
  second body (`transform copy = true`). A 2-body part round-tripping to STEP.

Exercises move / rotate / scale and copy >> multibody (bucket 3.1). Slow determinism + STEP
round-trip in `tests/examples/test_gate_examples.py`.
