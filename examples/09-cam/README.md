# CAM slicing example

`fdm_petg.slice.json` is a slice-profile wrapper for `ncad slice`. It points at a slicer's OWN
config file (`petg_0.2mm.ini`) which ncad does NOT ship: export that config from your installed
slicer (OrcaSlicer / PrusaSlicer) into this directory, then:

```
ncad build <part>.hocon --format stl        # ncad owns the model + mesh export
ncad slice out/<part>.stl --profile examples/09-cam/fdm_petg.slice.json
```

With no slicer installed, `ncad slice` reports `skipped` (by design). See
`src/ncad/cam/README.md` for the delegation boundary.
