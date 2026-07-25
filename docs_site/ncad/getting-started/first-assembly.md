# Compose an assembly

A part is one solid. An **assembly** places instances of parts and constrains how they sit together
with mates and joints. The document kind is a `.asm.hocon` file with an `assembly {}` block.

We will use the smallest real example: `examples/06-assemblies/wheel_axle.asm.hocon`, a wheel pinned
to an axle so it is free to spin. It instances two parts from the caster document and joins them with
one revolute joint.

## The assembly document

```properties
units = mm
assembly {
  instances = [
    { id = axle, file = "caster.hocon", part = axle, lock = true }
    { id = wheel, file = "caster.hocon", part = wheel }
  ]
  joints = [
    { id = spin, type = revolute, between = [
      { instance = axle, connector = shaft },
      { instance = wheel, connector = hub } ] }
  ]
}
```

Three ideas:

- **Instances** name reusable copies of parts. Each `instance` points at a part in a document
  (`file = "caster.hocon", part = axle`) and gets a local `id`. `lock = true` pins the axle as the
  fixed reference; the wheel is free to be positioned by the solver.
- **Connectors** are named coordinate frames on a part (declared in the part document, e.g. the
  axle's `shaft` cylindrical face and the wheel's `hub` bore). The assembly refers to them by name,
  so it never hard-codes coordinates.
- A **joint** couples two connectors with a defined degree of freedom. `type = revolute` leaves one
  rotational DoF, so the wheel spins about the axle but cannot translate or wobble.

## Assemble it and look

```bash
ncad assemble examples/06-assemblies/wheel_axle.asm.hocon
ncad view
```

`ncad assemble` solves the constraint network and writes `out/assemblies/wheel_axle/wheel_axle.assembly.json`
(the scene: each instance placed by a solved 4x4 matrix). In `ncad view`, switch to the Assemblies
mode and pick `wheel_axle` to see the two parts placed together.

Assemblies also give you a bill of materials, rolled-up mass properties, and interference checks
between instances. The [assemblies guide](../guides/authoring-assemblies.md) covers mates, the full
joint set, couplings, and sub-assemblies.

Next: [drive a mechanism with a motion study](first-motion.md).
