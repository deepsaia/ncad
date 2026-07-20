An **assembly** is a composition of **instances** of parts, each part built once and placed one or
more times, related by position and by mates/joints. The assembly document references part files
and records where each instance sits, rather than duplicating geometry.

## Instances, not copies

An instance is a *reference* to a part plus a placement (a rigid transform). Ten bolts in a flange
are ten instances of one bolt part, each with its own position; editing the bolt updates all ten.
This keeps assemblies lightweight (geometry is built per part and reused) and editable (one master
part, many placements).

A part instance can be placed **explicitly** (a given transform) or by a **connector snap** (land
one part's connector frame onto another's). Instances can also nest: a **sub-assembly** is itself an
instance in a parent assembly, composed under the parent's placement, so a machine is an assembly of
sub-assemblies of parts.

## Why composition, not merging

The assembly is a *lightweight composition* of independently-built, cached parts, not a re-baked
single solid. Each instance keeps its identity, material, and mass; the assembly adds placement and
relationships on top. A bad instance reference is reported by id and skipped, so one broken part does
not sink the whole assembly. This structure is what scales to large assemblies and what motion,
interference, and BOM all traverse.
