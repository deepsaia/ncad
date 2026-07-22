// --- Orientation ViewCube (Creo/NX/Fusion/Blender style), labeled in CAD Z-up ---
// An interactive cube in its own overlay canvas: 26 pickable cells (6 faces + 12 edges + 8
// corners) laid out as a 3x3x3 grid minus the center. Each cell carries a world-space direction;
// clicking it tweens the main camera to look FROM that direction (a face -> orthographic view,
// an edge -> edge-on, a corner -> isometric). Faces are labeled in the Z-up CAD convention:
// +Z TOP, -Z BOTTOM, +X RIGHT, -X LEFT, -Y FRONT, +Y BACK. The cube is axis-aligned and static;
// the gizmo camera mirrors the main view so the cube tumbles exactly with the model.
//
// Extracted from app.js: the cube owns its own scene/camera/renderer/raycaster/cells, so its only
// couplings to the main viewer are the main `camera` (a stable const, injected once) and the main
// `controls` (which app.js swaps between OrbitControls/TrackballControls, so it is read live via an
// injected accessor). initViewCube wires it up; renderGizmo (called each frame by app.js's render
// loop) and orientCameraTo (also reused by the dev debug handle) are the public surface.
import * as THREE from "three";
import { CUBE_FACES } from "./constants.js";
import { cubeLabelTexture } from "./gizmos.js";

// The main camera (stable const, injected by initViewCube) and a live accessor for the main
// controls (swapped between Orbit/Trackball in app.js, so read fresh on every use).
let camera = null;
let getControls = null;

// Cube scene singletons + pick state, created/populated in initViewCube (once #gizmo exists).
let gizmoRenderer = null, cubeScene = null, cubeCam = null;
const _cubePlain = () => new THREE.MeshStandardMaterial({ color: 0xcfd6de, metalness: 0.0,
  roughness: 0.9 });
const cubeCells = [];   // pickable meshes, each userData.dir (world direction) + .baseMats
const CUBE_STEP = 0.68, CUBE_CELL = 0.6;

export function renderGizmo() {
  // Mirror the main camera: look at the cube's origin from the same direction + up as the main
  // view, so the cube's orientation always matches the model on screen.
  const controls = getControls();
  const dir = camera.position.clone().sub(controls.target);
  if (dir.lengthSq() < 1e-9) dir.set(0, -1, 0);
  cubeCam.position.copy(dir).setLength(8);
  cubeCam.up.copy(camera.up);
  cubeCam.lookAt(0, 0, 0);
  gizmoRenderer.render(cubeScene, cubeCam);
}

// Hover highlight + click-to-orient on the cube canvas.
const cubeRay = new THREE.Raycaster();
let cubeHovered = null;
function cubeCellAt(ev) {
  const rect = gizmoRenderer.domElement.getBoundingClientRect();
  const p = new THREE.Vector2(((ev.clientX - rect.left) / rect.width) * 2 - 1,
                              -((ev.clientY - rect.top) / rect.height) * 2 + 1);
  cubeRay.setFromCamera(p, cubeCam);
  const hits = cubeRay.intersectObjects(cubeCells, false);
  return hits.length ? hits[0].object : null;
}
function setCubeHover(cell) {
  if (cubeHovered === cell) return;
  if (cubeHovered) cubeHovered.material = cubeHovered.userData.baseMats;
  cubeHovered = cell;
  gizmoRenderer.domElement.style.cursor = cell ? "pointer" : "default";
  if (cell) {
    // A translucent blue overlay material on all 6 sides signals the hovered cell.
    cell.material = cell.userData.baseMats.map(() => new THREE.MeshStandardMaterial({
      color: 0x5aa0ff, metalness: 0.0, roughness: 0.6, emissive: 0x1b3c66 }));
  }
}

// Tween the main camera to look FROM `dir` (world), keeping the current orbit distance + target.
// Spherical interpolation around the target so the camera arcs smoothly. Up is Z, except a
// top/bottom view (dir ~ +/-Z) uses Y so the view is not gimbal-degenerate.
let _orientToken = 0;
export function orientCameraTo(dir) {
  const controls = getControls();
  const target = controls.target.clone();
  const dist = camera.position.distanceTo(target);
  const endDir = dir.clone().normalize();
  const startDir = camera.position.clone().sub(target).normalize();
  const up = Math.abs(endDir.z) > 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(0, 0, 1);
  // Axis mode locks world-up; free mode (Trackball) tumbles camera.up, so snapping should restore
  // a sane up too. Set it up front so OrbitControls' math is consistent through the tween.
  camera.up.copy(up);
  const q = new THREE.Quaternion().setFromUnitVectors(startDir, endDir);
  const ident = new THREE.Quaternion();
  const token = ++_orientToken;
  const start = performance.now(), DUR = 320;
  (function step(now) {
    if (token !== _orientToken) return;   // superseded by a newer click
    const t = Math.min((now - start) / DUR, 1);
    const e = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;  // easeInOutCubic
    const partial = new THREE.Quaternion().slerpQuaternions(ident, q, e);
    const d = startDir.clone().applyQuaternion(partial).multiplyScalar(dist);
    camera.position.copy(target).add(d);
    camera.up.copy(up);
    controls.update();
    if (t < 1) requestAnimationFrame(step);
  })(start);
}

// Build the cube overlay + wire hover/click, then return. Called once by app.js after the main
// camera + controls exist. `cameraArg` is the main camera; `getControlsArg` returns the current
// main controls (which app.js swaps between Orbit/Trackball).
export function initViewCube(cameraArg, getControlsArg) {
  camera = cameraArg;
  getControls = getControlsArg;
  const gizmoDiv = document.getElementById("gizmo");
  gizmoRenderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  gizmoRenderer.setPixelRatio(window.devicePixelRatio);
  gizmoRenderer.setSize(128, 128);
  gizmoRenderer.setClearColor(0x000000, 0);
  gizmoDiv.appendChild(gizmoRenderer.domElement);
  cubeScene = new THREE.Scene();
  cubeCam = new THREE.OrthographicCamera(-1.7, 1.7, 1.7, -1.7, 0.1, 20);
  cubeScene.add(new THREE.HemisphereLight(0xffffff, 0x888c94, 1.1));
  const cubeKey = new THREE.DirectionalLight(0xffffff, 0.55); cubeKey.position.set(3, 5, 8);
  cubeScene.add(cubeKey);

  for (let i = -1; i <= 1; i++) {
    for (let j = -1; j <= 1; j++) {
      for (let k = -1; k <= 1; k++) {
        if (i === 0 && j === 0 && k === 0) continue;   // no center cell
        const mats = [0, 1, 2, 3, 4, 5].map(_cubePlain);
        // Label a FACE cell (exactly one axis nonzero) on its outward group.
        const nonzero = [i, j, k].filter(v => v !== 0).length;
        if (nonzero === 1) {
          const face = CUBE_FACES.find(f => f.dir[0] === i && f.dir[1] === j && f.dir[2] === k);
          mats[face.group] = new THREE.MeshStandardMaterial({ map: cubeLabelTexture(face.label),
            metalness: 0.0, roughness: 0.85 });
        }
        const cell = new THREE.Mesh(new THREE.BoxGeometry(CUBE_CELL, CUBE_CELL, CUBE_CELL), mats);
        cell.position.set(i * CUBE_STEP, j * CUBE_STEP, k * CUBE_STEP);
        cell.userData.dir = new THREE.Vector3(i, j, k).normalize();
        cell.userData.baseMats = mats;
        cubeScene.add(cell);
        cubeCells.push(cell);
      }
    }
  }

  gizmoRenderer.domElement.addEventListener("pointermove", ev => setCubeHover(cubeCellAt(ev)));
  gizmoRenderer.domElement.addEventListener("pointerleave", () => setCubeHover(null));
  gizmoRenderer.domElement.addEventListener("click", ev => {
    const cell = cubeCellAt(ev);
    if (cell) orientCameraTo(cell.userData.dir);
  });
}
