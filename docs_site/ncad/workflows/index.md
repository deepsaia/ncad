# Workflows

The [authoring guides](../guides/authoring-parts.md) cover each document kind on its own. These
workflows chain them into the pipelines you actually run, each end to end on a real example:

- [Part to motion](part-to-motion.md) - author parts, compose an assembly, drive a motion study.
- [Assembly to robot](assembly-to-robot.md) - overlay physics on an assembly and export URDF / MJCF.
- [Part to FEA](part-to-fea.md) - take a part into a structural load case and read the results.
- [Import, edit, export](import-edit-export.md) - bring in a dumb STEP solid, edit it directly, and
  export it back.

Every step is one `ncad` command over a text document, and every artifact is reproducible from the
repository. The through-line: one document kind's output is the next kind's input, and nothing is
authored twice.
