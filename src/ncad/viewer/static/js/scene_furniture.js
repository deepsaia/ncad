// Static scene furniture: the shadow-catcher ground plane, the floor grid, and the world-origin
// axis gizmo. These are created once and added to the scene; none of them change with the loaded
// model (the grid recolors on theme change, and frameModel rescales the world-origin marker by
// name), so they are a small, self-contained slice out of app.js.
//
// initSceneFurniture builds all three and returns the grid, which app.js still references (the Grid
// visibility toggle + the theme recolor). The ground + world-origin need no handle: the ground is
// inert, and frameModel finds the origin marker via scene.getObjectByName("worldOrigin").
import * as THREE from "three";
import { cssColor } from "./utils.js";
import { buildAxisGizmo } from "./gizmos.js";

// Build the ground plane + floor grid + world-origin gizmo, add them to `scene`, and return the
// grid (the one app.js keeps a handle to). Called once by app.js after the scene exists.
export function initSceneFurniture(scene) {
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(400, 400),
    new THREE.ShadowMaterial({ opacity: 0.32 })
  );
  // Z-up world: PlaneGeometry lies in XY by default, which is already the floor, so no
  // rotation is needed (the old -90deg-about-X tilt was for a Y-up scene).
  ground.receiveShadow = true; scene.add(ground);

  // GridHelper is built in the XZ plane (Y-up); rotate it into XY for the Z-up floor.
  const grid = new THREE.GridHelper(80, 80, cssColor("--grid-major"), cssColor("--grid-minor"));
  grid.rotation.x = Math.PI / 2;
  scene.add(grid);

  // A small poly gizmo fixed at the WORLD origin (X=red, Y=green, Z=blue), always visible as a
  // reference. A poly gizmo (not an AxesHelper) because GL LINES are 1px-capped and z-fight the grid,
  // causing a stutter. Its size is refreshed to the current model in frameModel (scaled from 0.02).
  const worldOrigin = buildAxisGizmo(0.02, { radius: 0.02 * 0.02 });  // thin shafts (2% of length)
  worldOrigin.name = "worldOrigin";
  scene.add(worldOrigin);

  return grid;
}
