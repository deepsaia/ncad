import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { TrackballControls } from "three/addons/controls/TrackballControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { cssVar, cssColor, fmtDuration, fmtSpeed, escapeHtml, iconButton,
         scrollActiveIntoView, matrixFromRowMajor } from "./utils.js";

const stage = document.getElementById("stage");
const spinner = document.getElementById("spinner");

// API base + model-bytes base, so ONE SPA serves both servers. The Tornado service (ncad serve)
// injects window.NCAD_API_BASE = "/api/v1"; the stdlib viewer (ncad view) injects nothing and uses
// its historical prefixes (JSON under /api, model bytes at /models). Call apiUrl/modelUrl with the
// path AFTER the prefix (e.g. apiUrl("/specs"), modelUrl(name)):
//   ncad serve:  /api/v1/specs, /api/v1/models/<name>
//   ncad view:   /api/specs,    /models/<name>
const API = (typeof window !== "undefined" && window.NCAD_API_BASE) || "/api";
const MODEL_BASE = (typeof window !== "undefined" && window.NCAD_API_BASE)
  ? window.NCAD_API_BASE + "/models" : "/models";
function apiUrl(path) { return API + path; }              // path AFTER /api, e.g. "/specs"
function modelUrl(name) { return MODEL_BASE + "/" + name; }  // model bytes

// Browser live-reload (dev only, ncad serve): open /ws/livereload and reload when the server's
// boot id changes. Reconnect-and-compare, not server push: we record the first boot id we see;
// when autoreload re-execs the server the socket drops, we reconnect with backoff, and the fresh
// process reports a different boot id, which triggers a reload. Guarded by window.NCAD_DEV so the
// stdlib viewer (no ws route) never attempts it and production stays quiet.
function startLiveReload() {
  if (typeof window === "undefined" || !window.NCAD_DEV) return;
  const url = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws/livereload";
  let firstBootId = null, backoff = 250;
  const connect = () => {
    let ws;
    try { ws = new WebSocket(url); } catch (e) { setTimeout(connect, backoff); return; }
    ws.onmessage = ev => {
      let msg; try { msg = JSON.parse(ev.data); } catch (e) { return; }
      if (msg.type !== "hello") return;
      if (firstBootId === null) { firstBootId = msg.boot_id; backoff = 250; }
      else if (msg.boot_id !== firstBootId) { location.reload(); }
    };
    // On drop (server re-exec), reconnect with capped exponential backoff; the successful
    // reconnect to the fresh process delivers the new boot id and reloads.
    ws.onclose = () => { setTimeout(connect, backoff); backoff = Math.min(backoff * 2, 2000); };
    ws.onerror = () => { try { ws.close(); } catch (e) { /* onclose handles retry */ } };
  };
  connect();
}
startLiveReload();

const scene = new THREE.Scene();
scene.background = cssColor("--scene-bg");
scene.fog = new THREE.Fog(cssColor("--scene-bg"), 40, 120);

const camera = new THREE.PerspectiveCamera(45, stage.clientWidth / stage.clientHeight, 0.01, 1000);
// Z-up world: models are authored Z-up and the loaded glTF is rotated into a
// Z-up scene (see loadModel), so scene coordinates equal modeled coordinates.
camera.up.set(0, 0, 1);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(stage.clientWidth, stage.clientHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
stage.appendChild(renderer.domElement);

// Orientation mode: "axis" keeps up-vector fixed and revolves around the vertical
// axis (OrbitControls, good for grounded parts); "free" allows full trackball tumble
// so the model can be overturned completely (TrackballControls). `controls` is
// swapped between the two, preserving the camera position and orbit target.
let controls = null;
let orientationMode = "axis";
let autoRotate = false;

function makeControls(mode) {
  if (mode === "free") {
    const c = new TrackballControls(camera, renderer.domElement);
    c.rotateSpeed = 3.0;
    c.panSpeed = 0.8;
    c.dynamicDampingFactor = 0.15;
    return c;
  }
  const c = new OrbitControls(camera, renderer.domElement);
  c.enableDamping = true;
  c.dampingFactor = 0.08;
  return c;
}

function setOrientationMode(mode) {
  const target = controls ? controls.target.clone() : new THREE.Vector3(0, 0, 0);
  if (controls) controls.dispose();
  orientationMode = mode;
  // TrackballControls tilts camera.up while tumbling; axis mode must restore world-up
  // (Z-up) so OrbitControls revolves around the vertical, still able to look up at the
  // underside. Without this the locked-in view stays tilted after a free-look session.
  if (mode === "axis") camera.up.set(0, 0, 1);
  controls = makeControls(mode);
  controls.target.copy(target);
  // OrbitControls honors autoRotate; TrackballControls has no such option.
  if (mode === "axis") controls.autoRotate = autoRotate;
  controls.update();
}

setOrientationMode("axis");

// --- Orientation ViewCube (Creo/NX/Fusion/Blender style), labeled in CAD Z-up ---
// An interactive cube in its own overlay canvas: 26 pickable cells (6 faces + 12 edges + 8
// corners) laid out as a 3x3x3 grid minus the center. Each cell carries a world-space direction;
// clicking it tweens the main camera to look FROM that direction (a face -> orthographic view,
// an edge -> edge-on, a corner -> isometric). Faces are labeled in the Z-up CAD convention:
// +Z TOP, -Z BOTTOM, +X RIGHT, -X LEFT, -Y FRONT, +Y BACK. The cube is axis-aligned and static;
// the gizmo camera mirrors the main view so the cube tumbles exactly with the model.
const gizmoDiv = document.getElementById("gizmo");
const gizmoRenderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
gizmoRenderer.setPixelRatio(window.devicePixelRatio);
gizmoRenderer.setSize(128, 128);
gizmoRenderer.setClearColor(0x000000, 0);
gizmoDiv.appendChild(gizmoRenderer.domElement);
const cubeScene = new THREE.Scene();
const cubeCam = new THREE.OrthographicCamera(-1.7, 1.7, 1.7, -1.7, 0.1, 20);
cubeScene.add(new THREE.HemisphereLight(0xffffff, 0x888c94, 1.1));
const cubeKey = new THREE.DirectionalLight(0xffffff, 0.55); cubeKey.position.set(3, 5, 8);
cubeScene.add(cubeKey);

// Face labels by outward direction, and the BoxGeometry material-group index of that outward face
// (group order is +X, -X, +Y, -Y, +Z, -Z).
const CUBE_FACES = [
  { dir: [1, 0, 0], label: "RIGHT", group: 0 },
  { dir: [-1, 0, 0], label: "LEFT", group: 1 },
  { dir: [0, 1, 0], label: "BACK", group: 2 },
  { dir: [0, -1, 0], label: "FRONT", group: 3 },
  { dir: [0, 0, 1], label: "TOP", group: 4 },
  { dir: [0, 0, -1], label: "BOTTOM", group: 5 },
];

function cubeLabelTexture(text) {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#e9eef4"; ctx.fillRect(0, 0, 128, 128);
  ctx.strokeStyle = "#9aa6b4"; ctx.lineWidth = 5; ctx.strokeRect(4, 4, 120, 120);
  ctx.fillStyle = "#33414f"; ctx.font = "bold 22px sans-serif";
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(text, 64, 66);
  const tex = new THREE.CanvasTexture(c); tex.anisotropy = 4;
  return tex;
}

const _cubePlain = () => new THREE.MeshStandardMaterial({ color: 0xcfd6de, metalness: 0.0,
  roughness: 0.9 });
const cubeCells = [];   // pickable meshes, each userData.dir (world direction) + .baseMats
const CUBE_STEP = 0.68, CUBE_CELL = 0.6;
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

function renderGizmo() {
  // Mirror the main camera: look at the cube's origin from the same direction + up as the main
  // view, so the cube's orientation always matches the model on screen.
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
gizmoRenderer.domElement.addEventListener("pointermove", ev => setCubeHover(cubeCellAt(ev)));
gizmoRenderer.domElement.addEventListener("pointerleave", () => setCubeHover(null));
gizmoRenderer.domElement.addEventListener("click", ev => {
  const cell = cubeCellAt(ev);
  if (cell) orientCameraTo(cell.userData.dir);
});

// Tween the main camera to look FROM `dir` (world), keeping the current orbit distance + target.
// Spherical interpolation around the target so the camera arcs smoothly. Up is Z, except a
// top/bottom view (dir ~ +/-Z) uses Y so the view is not gimbal-degenerate.
let _orientToken = 0;
function orientCameraTo(dir) {
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

// Face picking: raycast against the model's mesh parts. build123d exports one glTF
// primitive per face in face order, so a part's index into `pickParts` is its index
// into the element-map sidecar's `elements` array.
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
renderer.domElement.addEventListener("click", ev => {
  if (!modelRoot) return;
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(pickParts, false);
  // Assemblies: a click selects the hit mesh's instance (highlight + tree sync); empty space
  // clears. This runs regardless of elementMap (an assembly has none; it is a part concept).
  if (isAssemblyScene()) {
    selectInstance(hits.length ? hits[0].object.userData.instanceId : null);
    return;
  }
  const out = document.getElementById("i-picked");
  if (!elementMap) return;
  if (!hits.length) { out.textContent = "-"; return; }
  const idx = pickParts.indexOf(hits[0].object);
  // Report the clicked mesh's BODY id + material via the sidecar `meshes` list (mesh index ->
  // body), which is body-correct for multibody. If there is no mesh entry (older sidecar) fall
  // back to the flat element lookup (correct for a single body).
  const meshes = (elementMap && elementMap.meshes) || [];
  if (meshes[idx]) {
    const info = meshes[idx];
    out.textContent = `${info.body_id} (${info.material || "no material"})`;
  } else {
    const el = (elementMap.elements || [])[idx];
    out.textContent = el ? `${el.id} (by ${el.created_by})` : "-";
  }
});

// Ambient base, always on; the rig below provides the directional/spot character. The world is
// Z-UP (ground in XY), so a HemisphereLight's sky/ground axis must point up +Z (its default is
// +Y); position (0,0,1) reorients its gradient so "sky" is overhead, not sideways.
const ambient = new THREE.HemisphereLight(0xffffff, 0x2a3340, 0.45);
ambient.position.set(0, 0, 1);
scene.add(ambient);

// A swappable light rig. Each preset clears and rebuilds `lightRig`.
const lightRig = new THREE.Group();
scene.add(lightRig);

// IMPORTANT: this scene is Z-UP (the ground plane lies in XY). Every light's HEIGHT is therefore
// on +Z, not +Y. Authoring positions with +Y as "up" (the old Y-up rig) put the key light in the
// ground plane, which raked light sideways (leaving tall vertical faces near-black) and cast the
// directional shadow sideways across the floor as long streaks. Keep lights high on +Z.
function makeShadowCaster(light) {
  light.castShadow = true;
  light.shadow.mapSize.set(2048, 2048);
  light.shadow.bias = -0.0004;
  const c = light.shadow.camera;
  c.near = 0.5; c.far = 160; c.left = -40; c.right = 40; c.top = 40; c.bottom = -40;
  return light;
}

const LIGHT_PRESETS = {
  sun() {
    ambient.intensity = 0.55;
    const key = makeShadowCaster(new THREE.DirectionalLight(0xfff4e6, 2.0));
    key.position.set(14, -10, 24);   // high on +Z, from the camera's front-right
    // A fill from the opposite, still-elevated side so no large vertical face goes black.
    const fill = new THREE.DirectionalLight(0x9fc7ff, 0.7); fill.position.set(-14, 12, 10);
    return [key, fill];
  },
  natural() {
    // Even, all-around illumination with no harsh single source. Directionals ring the model from
    // four sides AND from below (-Z), plus a bright hemisphere and strong ambient, so the underside
    // is lit too (a top-only rig leaves the bottom dark). All heights are on +Z.
    ambient.intensity = 0.85;
    const hemi = new THREE.HemisphereLight(0xeaf4ff, 0xb8c2d0, 1.0);
    hemi.position.set(0, 0, 1);
    const top = makeShadowCaster(new THREE.DirectionalLight(0xffffff, 0.7));
    top.position.set(8, -10, 24);
    const left = new THREE.DirectionalLight(0xffffff, 0.4); left.position.set(-16, 0, 8);
    const right = new THREE.DirectionalLight(0xffffff, 0.4); right.position.set(16, 0, 8);
    const back = new THREE.DirectionalLight(0xffffff, 0.4); back.position.set(0, 16, 8);
    const under = new THREE.DirectionalLight(0xffffff, 0.35); under.position.set(0, 4, -14);
    return [hemi, top, left, right, back, under];
  },
  studio() {
    ambient.intensity = 0.5;
    const key = makeShadowCaster(new THREE.DirectionalLight(0xffffff, 1.5)); key.position.set(12, -10, 20);
    const fill = new THREE.DirectionalLight(0xcfe0ff, 0.9); fill.position.set(-12, 6, 12);
    const rim = new THREE.DirectionalLight(0xffffff, 1.1); rim.position.set(0, 14, 16);
    return [key, fill, rim];
  },
  spotlight() {
    ambient.intensity = 0.25;
    const spot = makeShadowCaster(new THREE.SpotLight(0xffffff, 900, 0, Math.PI / 6, 0.4, 1.4));
    spot.position.set(6, -4, 30);
    return [spot];
  },
  overcast() {
    ambient.intensity = 1.0;
    const soft = makeShadowCaster(new THREE.DirectionalLight(0xeaf0f6, 0.6));
    soft.position.set(4, -6, 26);
    return [soft];
  },
};

function setLighting(name) {
  lightRig.clear();
  const preset = LIGHT_PRESETS[name] || LIGHT_PRESETS.sun;
  preset().forEach(l => { lightRig.add(l); if (l.target) lightRig.add(l.target); });
  localStorage.setItem("ncad.light", name);
  if (modelRoot) fitShadowCameras();
}

// Size every shadow-casting light's ortho frustum to the current model so the fixed 2048 shadow
// map spends its texels on the model (a frustum many times the model size gives coarse, streaky
// shadows). Called from frameModel + setLighting. Uses the framed model radius; the model sits
// centered at the origin lifted by half its height on +Z.
let shadowRadius = 40;
function fitShadowCameras() {
  const extent = Math.max(shadowRadius, 1e-3);
  lightRig.traverse(o => {
    if (o.isLight && o.castShadow && o.shadow && o.shadow.camera.isOrthographicCamera) {
      const c = o.shadow.camera;
      c.left = -extent; c.right = extent; c.top = extent; c.bottom = -extent;
      c.near = extent / 100; c.far = extent * 8;
      c.updateProjectionMatrix();
    }
  });
}

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(400, 400),
  new THREE.ShadowMaterial({ opacity: 0.32 })
);
// Z-up world: PlaneGeometry lies in XY by default, which is already the floor, so no
// rotation is needed (the old -90deg-about-X tilt was for a Y-up scene).
ground.receiveShadow = true; scene.add(ground);

// GridHelper is built in the XZ plane (Y-up); rotate it into XY for the Z-up floor.
let grid = new THREE.GridHelper(80, 80, cssColor("--grid-major"), cssColor("--grid-minor"));
grid.rotation.x = Math.PI / 2;
scene.add(grid);

// A small poly axis gizmo: three thin colored cylinders (X red / Y green / Z blue) + a center
// sphere. Poly meshes take real thickness and do NOT z-fight like GL LINES (AxesHelper), fixing the
// world-origin stutter. `size` is the axis length; opts.radius scales the shaft thickness. Reused
// for the world origin, instance origins, connector triads, and joint-glyph bases (DRY).
function buildAxisGizmo(size, opts) {
  opts = opts || {};
  const r = opts.radius != null ? opts.radius : size * 0.04;
  const g = new THREE.Group();
  g.userData.isGizmo = true;
  const axes = [
    { color: 0xff5555, rot: [0, 0, -Math.PI / 2], off: [size / 2, 0, 0] },  // +X
    { color: 0x55ff55, rot: [0, 0, 0], off: [0, size / 2, 0] },             // +Y
    { color: 0x5599ff, rot: [Math.PI / 2, 0, 0], off: [0, 0, size / 2] },   // +Z
  ];
  for (const a of axes) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, size, 12),
                             new THREE.MeshBasicMaterial({ color: a.color }));
    m.rotation.set(a.rot[0], a.rot[1], a.rot[2]);
    m.position.set(a.off[0], a.off[1], a.off[2]);
    g.add(m);
  }
  g.add(new THREE.Mesh(new THREE.SphereGeometry(r * 1.6, 12, 12),
                       new THREE.MeshBasicMaterial({ color: 0xdddddd })));
  return g;
}

// True if the object is inside a gizmo group (so it is excluded from the pick raycast set).
function _inGizmo(o) {
  for (let p = o; p; p = p.parent) if (p.userData && p.userData.isGizmo) return true;
  return false;
}

// A thin arc line in the plane perpendicular to `dir` (a rotation-freedom marker). Color-coded.
function _rotArc(dir, size, color) {
  // Two in-plane basis vectors perpendicular to `dir`, so the arc lies around the rotation axis.
  const up = Math.abs(dir.z) > 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
  const u = new THREE.Vector3().crossVectors(dir, up).normalize();
  const w = new THREE.Vector3().crossVectors(dir, u).normalize();
  const rad = size * 0.6, pts = [];
  for (let i = 0; i <= 32; i++) {
    const t = (i / 32) * Math.PI * 1.5;   // a 270deg arc reads as "turns about this axis"
    pts.push(u.clone().multiplyScalar(Math.cos(t) * rad).add(w.clone().multiplyScalar(Math.sin(t) * rad)));
  }
  return new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
                        new THREE.LineBasicMaterial({ color }));
}

// A thin double-headed arrow line along `dir` (a translation-freedom marker). Color-coded.
function _transArrow(dir, size, color) {
  const h = size * 0.6, head = size * 0.16;
  const tip = dir.clone().multiplyScalar(h), tail = dir.clone().multiplyScalar(-h);
  // A perpendicular for the arrowhead barbs.
  const up = Math.abs(dir.z) > 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
  const perp = new THREE.Vector3().crossVectors(dir, up).normalize().multiplyScalar(head * 0.5);
  const pts = [tail, tip,
    tip, tip.clone().sub(dir.clone().multiplyScalar(head)).add(perp),
    tip, tip.clone().sub(dir.clone().multiplyScalar(head)).sub(perp),
    tail, tail.clone().add(dir.clone().multiplyScalar(head)).add(perp),
    tail, tail.clone().add(dir.clone().multiplyScalar(head)).sub(perp)];
  return new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts),
                               new THREE.LineBasicMaterial({ color }));
}

// A signature-keyed joint glyph at a joint's world connector frame: rotation -> arc about the axis;
// translation -> double arrow along it; cylindrical -> both; ball -> three arcs; screw -> arc+arrow
// on Z; fixed -> a cube. The signature axis "Z"/"X"/"Y" maps to that FRAME's vector (not world), so
// a tilted joint shows its freedom about the tilted axis. `frame` = {origin,x,y,z} (world, metres).
function buildJointGlyph(joint, frame, size) {
  const g = new THREE.Group();
  g.userData.isGizmo = true;
  const axisVec = { X: frame.x, Y: frame.y, Z: frame.z, line: frame.z };
  const sig = joint.signature || [];
  if (joint.type === "fixed" || sig.length === 0) {
    g.add(new THREE.Mesh(new THREE.BoxGeometry(size * 0.4, size * 0.4, size * 0.4),
                         new THREE.MeshBasicMaterial({ color: 0x999999 })));
  }
  for (const a of sig) {
    const v = axisVec[a.axis] || frame.z;
    const dir = new THREE.Vector3(v[0], v[1], v[2]).normalize();
    if (a.motion === "rotation" || a.motion === "screw") g.add(_rotArc(dir, size, 0xffaa33));
    if (a.motion === "translation" || a.motion === "screw") g.add(_transArrow(dir, size, 0x33ccff));
  }
  g.position.set(frame.origin[0], frame.origin[1], frame.origin[2]);
  return g;
}

// A small poly gizmo fixed at the WORLD origin (X=red, Y=green, Z=blue), always visible as a
// reference. A poly gizmo (not an AxesHelper) because GL LINES are 1px-capped and z-fight the grid,
// causing a stutter. Its size is refreshed to the current model in frameModel (scaled from 0.02).
const worldOrigin = buildAxisGizmo(0.02, { radius: 0.02 * 0.02 });  // thin shafts (2% of length)
worldOrigin.name = "worldOrigin";
scene.add(worldOrigin);

// Recolor the 3D scene from the current theme's CSS variables. Called on theme change.
function applySceneTheme() {
  const bg = cssColor("--scene-bg");
  scene.background = bg;
  if (scene.fog) scene.fog.color = bg;
  const major = cssColor("--grid-major"), minor = cssColor("--grid-minor");
  const gm = grid.material;
  (Array.isArray(gm) ? gm : [gm]).forEach((m, i) => { m.color = i === 0 ? major : minor; });
  const edgeColor = cssColor("--edge");
  edges.forEach(e => { e.material.color = edgeColor; });
}

// Material presets for "Material" mode.
const MATERIALS = [
  { name: "Concrete",  color: 0xb8bdc4, metalness: 0.05, roughness: 0.9 },
  { name: "Brick",     color: 0xa8533a, metalness: 0.0,  roughness: 0.85 },
  { name: "Red brick", color: 0x8c3b2b, metalness: 0.0,  roughness: 0.9 },
  { name: "Timber",    color: 0xb9824f, metalness: 0.05, roughness: 0.6 },
  { name: "Oak",       color: 0x9c6b3f, metalness: 0.05, roughness: 0.55 },
  { name: "Sandstone", color: 0xd8c9a3, metalness: 0.0,  roughness: 0.8 },
  { name: "Plaster",   color: 0xeae6dd, metalness: 0.0,  roughness: 0.95 },
  { name: "Stucco",    color: 0xc9b79a, metalness: 0.0,  roughness: 0.85 },
  { name: "Steel",     color: 0x9aa6b4, metalness: 0.85, roughness: 0.35 },
  { name: "Copper",    color: 0xb87333, metalness: 0.9,  roughness: 0.4 },
  { name: "Glass",     color: 0x8fb8d8, metalness: 0.1,  roughness: 0.05, opacity: 0.45 },
  { name: "Slate",     color: 0x4a525c, metalness: 0.1,  roughness: 0.7 },
  { name: "Marble",    color: 0xe8e8ea, metalness: 0.05, roughness: 0.3 },
  { name: "Terracotta",color: 0xc06a4b, metalness: 0.0,  roughness: 0.8 },
  { name: "Graphite",  color: 0x2f3640, metalness: 0.3,  roughness: 0.6 },
  { name: "Mint",      color: 0x8fd4bf, metalness: 0.05, roughness: 0.55 },
];
let materialIndex = parseInt(localStorage.getItem("ncad.material") || "0", 10) || 0;

// Smooth shading: use the per-vertex normals ncad exports in the glTF so curved surfaces
// (a swept tube, a fillet) read as round rather than faceted. flatShading would discard
// those normals and light each triangle flat. Geometry/mesh are unchanged, this is display
// only (the tessellation density is set at export time, kernel side).
const SOLID = new THREE.MeshStandardMaterial({ color: 0xc6d3e2, metalness: 0.05, roughness: 0.85, flatShading: false });
const WIRE = new THREE.MeshBasicMaterial({ color: 0x5aa0ff, wireframe: true });
const XRAY = new THREE.MeshStandardMaterial({ color: 0x5aa0ff, transparent: true, opacity: 0.26, depthWrite: false });
function materialMat() {
  const m = MATERIALS[materialIndex];
  return new THREE.MeshStandardMaterial({ color: m.color, metalness: m.metalness, roughness: m.roughness });
}

// ---- By-material coloring (color each body by its document material) ----
// The mapping is GLOBAL by material name and lives in localStorage, so a material means the
// same color across every model. "__none__" is the reserved bucket for bodies with no material.
const MAT_COLORS_KEY = "ncad.materialColors";
const NO_MATERIAL = "__none__";
// A stable distinct palette so a fresh multi-material model is legible; the index is chosen by
// a deterministic hash of the material name, so a material keeps its color between loads.
const MAT_PALETTE = ["#c9ccd1", "#b87333", "#9aa6b4", "#b9824f", "#8fd4bf", "#c06a4b",
                     "#8fb8d8", "#d8c9a3", "#a8533a", "#6a7b8c"];
let matColors = (() => {
  try { return JSON.parse(localStorage.getItem(MAT_COLORS_KEY)) || {}; }
  catch (e) { return {}; }
})();
function paletteColor(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return MAT_PALETTE[h % MAT_PALETTE.length];
}
// Resolution order: user-assigned (localStorage) > authored appearance color > stable palette.
// Unassigned bodies default to the neutral solid gray until the user colors the "(no material)".
function colorFor(name, appearanceColor) {
  const key = name || NO_MATERIAL;
  if (matColors[key]) return matColors[key];
  if (name && appearanceColor) return appearanceColor;
  if (!name) return "#c6d3e2";
  return paletteColor(name);
}

// Build a By-Material MeshStandardMaterial from a resolved color + the body/instance `appearance`
// dict. Honors appearance.opacity (< 1 => transparent, e.g. glass), appearance.metalness, and
// appearance.roughness; each falls back to a matte-solid default when absent. This is the single
// place By-Material turns authored appearance into a THREE material, so glass declared in the
// document (opacity < 1) actually renders see-through in the viewer, for ANY material (not a glass
// special-case). depthWrite is disabled on transparent materials so panes blend without z-fighting.
function byMaterialMat(color, appearance) {
  const a = appearance || {};
  const opacity = (typeof a.opacity === "number") ? a.opacity : 1;
  const params = {
    color: color,
    metalness: (typeof a.metalness === "number") ? a.metalness : 0.05,
    roughness: (typeof a.roughness === "number") ? a.roughness : 0.85,
  };
  if (opacity < 1) { params.transparent = true; params.opacity = opacity; params.depthWrite = false; }
  return new THREE.MeshStandardMaterial(params);
}

// Per-exported-mesh body/material, from the sidecar `meshes` list (one entry per glTF mesh, in
// export order). pickParts is collected in that same glb mesh order, so meshInfo(i) maps mesh i
// -> its body id + material. This is positional, not name-based: glTF mesh names do not survive
// GLTFLoader reliably, and a global face index does not match the multibody glTF face order.
function meshInfo(i) {
  const meshes = (elementMap && elementMap.meshes) || [];
  return meshes[i] || { body_id: null, material: null, appearance_color: null };
}

let modelRoot = null, edges = [], mode = "solid", showEdges = true, castShadows = true;
let pickParts = [], elementMap = null;
// Assembly origin gizmos + their toggle state, declared here (before bindVcToggle uses them,
// which runs at load) to avoid a temporal-dead-zone error.
let originGizmos = [];  // per-instance origin axes helpers (toggled by the Origins control)
let showOrigins = localStorage.getItem("ncad.origins") === "1";
// Mate connector triads (bucket 5.1): per-connector frame markers, toggled by the Connectors
// control. Declared here (before bindVcToggle runs at load) to avoid a temporal-dead-zone error.
let connectorGizmos = [];
let showConnectors = localStorage.getItem("ncad.connectors") === "1";
// Joint-freedom glyphs (bucket 5.5): per-joint free-axis markers + dashed coupling links, toggled
// by the Joints control. Declared before bindVcToggle runs to avoid a temporal-dead-zone error.
let jointGizmos = [];
let showJoints = localStorage.getItem("ncad.joints") === "1";
// Motion trace curves (bucket 6.1): a THREE.Line per declared trace, added to modelRoot (world
// path), toggled by the Traces control. Default on (localStorage null -> on).
let traceLines = [];
let showTraces = localStorage.getItem("ncad.traces") !== "0";
// A stable palette for trace curves (distinct from the material palette).
const TRACE_COLORS = [0xff5aa0, 0x5aff9a, 0xffd166, 0x9a7cff, 0x5ad1ff, 0xff8c42];
// Per-instance material {instanceId: {material, appearance_color}} from the sidecar, for the
// assembly By-Material view (bucket 5.6). Empty in Parts mode (that path uses the element map).
let assemblyMaterials = {};
// Parts | Assemblies view mode (persisted). Declared HERE, before the initial setMode() call
// (which reaches distinctMaterials -> reads viewMode); a later `let` would be a temporal dead
// zone and throw during init, blanking the whole viewer.
let viewMode = localStorage.getItem("ncad.viewMode") || "parts";
// Both Assemblies and Motion render a composed assembly scene (instances placed by matrices), so
// scene behavior (pick-by-instance, per-instance material, connector/joint overlays, the timeline)
// keys off this, while the model-list source + spec kind stay per-mode.
function isAssemblyScene() {
  return viewMode === "assemblies" || viewMode === "motion" || viewMode === "physics";
}
// Assembly selection / highlight / isolate (bucket 5.5). instanceMeshMap: instanceId -> [meshes],
// published by loadAssembly once all glbs load. Declared before bindVcToggle (isolate) runs.
let instanceMeshMap = {};
let selectedInstances = [];
let isolateOn = localStorage.getItem("ncad.isolate") === "1";
const loader = new GLTFLoader();

// Select one instance (or none) and re-apply highlight/isolate + tree active styling.
function selectInstance(id) { selectedInstances = id ? [id] : []; _applySelection(); }
// Select a set (used by a mate/joint/coupling chip highlighting both connected instances).
function selectInstances(ids) { selectedInstances = (ids || []).filter(Boolean); _applySelection(); }
function clearSelection() { selectedInstances = []; _applySelection(); }
function _applySelection() { refreshInstanceVisuals(); syncTreeActive(); }

// Capture each instance mesh's BASE material (what applyMode assigned). applyMode owns the base and
// calls this before refreshInstanceVisuals, so highlight/isolate always derive from a clean base
// rather than a prior clone (which would clone-a-clone or leak a mutated shared material).
function captureInstanceBases() {
  for (const id in instanceMeshMap)
    for (const m of instanceMeshMap[id]) m.userData._baseMat = m.material;
}

// The single place that applies per-instance visual state (highlight + isolate). Because applyMode
// assigns ONE shared material object (SOLID/XRAY/...) to every mesh, per-instance state MUST use a
// per-mesh CLONE (mutating the shared material in place would tint/fade the whole assembly). A mesh
// with no distinct state is reset to its shared base.
function refreshInstanceVisuals() {
  const sel = new Set(selectedInstances);
  const dim = isolateOn && selectedInstances.length > 0;
  for (const id in instanceMeshMap) {
    const hi = sel.has(id);
    const faded = dim && !hi;
    for (const m of instanceMeshMap[id]) {
      const base = m.userData._baseMat || m.material;
      if (!hi && !faded) { m.material = base; continue; }
      const mm = base.clone();
      if (hi && mm.emissive) mm.emissive.setHex(0x2266aa);
      if (faded) { mm.transparent = true; mm.opacity = 0.12; mm.depthWrite = false; }
      m.material = mm;
    }
  }
}

function syncTreeActive() {
  const sel = new Set(selectedInstances);
  document.querySelectorAll(".tree-row[data-instance]").forEach(r => {
    r.classList.toggle("tree-row-active", sel.has(r.dataset.instance));
  });
}

function clearModel() {
  if (modelRoot) { scene.remove(modelRoot); modelRoot = null; }
  edges.forEach(e => scene.remove(e)); edges = [];
  originGizmos = [];  // gizmos are children of modelRoot, removed with it above
  connectorGizmos = [];  // connector triads are children of modelRoot too, removed with it
  jointGizmos = [];  // joint glyphs + coupling links are children of modelRoot, removed with it
  instanceMeshMap = {}; selectedInstances = [];  // drop selection state with the old scene
  assemblyMaterials = {};  // drop per-instance material state with the old scene
  if (typeof resetMotion === "function") resetMotion();  // drop any motion timeline with the scene
  pickParts = []; elementMap = null;
  const picked = document.getElementById("i-picked");
  if (picked) picked.textContent = "-";
}

function applyMode() {
  if (!modelRoot) return;
  if (mode === "bymaterial") {
    if (isAssemblyScene()) {
      // Assemblies: color each instance's meshes by that INSTANCE's part material (from the
      // sidecar), since an assembly has no per-part element map. Each instance is one part.
      for (const id in instanceMeshMap) {
        const info = assemblyMaterials[id] || {};
        const col = new THREE.Color(colorFor(info.material, info.appearance_color));
        const transparent = info.appearance && typeof info.appearance.opacity === "number"
          && info.appearance.opacity < 1;
        for (const mesh of instanceMeshMap[id]) {
          mesh.material = byMaterialMat(col, info.appearance);
          // A transparent pane should not cast a hard shadow (it would read as opaque on the floor).
          mesh.castShadow = castShadows && !transparent;
        }
      }
    } else {
      // Parts: color each mesh by ITS BODY's material via the sidecar `meshes` list (mesh index i
      // -> body/material), since pickParts is in glb mesh (export) order. A mesh with no sidecar
      // entry falls back to the "(no material)" color.
      pickParts.forEach((mesh, i) => {
        const info = meshInfo(i);
        const col = new THREE.Color(colorFor(info.material, info.appearance_color));
        mesh.material = byMaterialMat(col, info.appearance);
        const transparent = info.appearance && typeof info.appearance.opacity === "number"
          && info.appearance.opacity < 1;
        mesh.castShadow = castShadows && !transparent;
      });
    }
    edges.forEach(e => { e.visible = showEdges; });
    captureInstanceBases(); refreshInstanceVisuals();
    return;
  }
  const mat = { solid: SOLID, material: materialMat(), wireframe: WIRE, xray: XRAY }[mode];
  modelRoot.traverse(o => { if (o.isMesh) { o.material = mat; o.castShadow = castShadows && mode !== "wireframe"; } });
  edges.forEach(e => { e.visible = showEdges && mode !== "wireframe"; });
  // Re-capture the (shared) base material each mode sets, then re-apply per-instance highlight/
  // isolate as per-mesh clones so a mode change does not clobber the selection visuals.
  captureInstanceBases(); refreshInstanceVisuals();
}

function hasMaterials() {
  if (isAssemblyScene()) {
    return Object.values(assemblyMaterials).some(m => m.material);
  }
  const els = (elementMap && elementMap.elements) || [];
  return els.some(e => e.material);
}

// Materials present in the loaded model, first-seen order, plus a trailing "(no material)"
// entry when any face/instance is unassigned. Each entry carries the appearance color (if any).
// In Assemblies mode the source is the per-instance materials; in Parts mode the element map.
function distinctMaterials() {
  const seen = new Map();
  let hasNone = false;
  const entries = isAssemblyScene()
    ? Object.values(assemblyMaterials).map(m => ({material: m.material,
                                                  appearance_color: m.appearance_color}))
    : ((elementMap && elementMap.elements) || []);
  entries.forEach(e => {
    if (e.material) { if (!seen.has(e.material)) seen.set(e.material, e.appearance_color); }
    else hasNone = true;
  });
  const out = [...seen.entries()].map(([name, appearance]) => ({ name, appearance }));
  if (hasNone) out.push({ name: null, appearance: null });
  return out;
}

// Show/hide the By-Material mode button by whether the current model (part OR assembly) has
// materials; drop out of the mode if it no longer applies. Shared by the part + assembly paths.
function updateByMaterialButton() {
  const byBtn = document.querySelector('#vc-modes .vc-btn[data-mode="bymaterial"]');
  if (byBtn) byBtn.hidden = !hasMaterials();
  if (mode === "bymaterial" && !hasMaterials()) { setMode("solid"); return; }
  syncMaterialBlock();
  applyMode();
}

function renderMaterialColors() {
  const wrap = document.getElementById("material-colors");
  wrap.innerHTML = "";
  distinctMaterials().forEach(m => {
    const key = m.name || NO_MATERIAL;
    const row = document.createElement("label");
    row.className = "matrow";
    const dot = document.createElement("span");
    dot.className = "dot"; dot.style.background = colorFor(m.name, m.appearance);
    const label = document.createElement("span");
    label.className = "mname"; label.textContent = m.name || "(no material)";
    const input = document.createElement("input");
    input.type = "color"; input.value = colorFor(m.name, m.appearance);
    input.addEventListener("input", () => {
      matColors[key] = input.value;
      localStorage.setItem(MAT_COLORS_KEY, JSON.stringify(matColors));
      dot.style.background = input.value;
      if (mode === "bymaterial") applyMode();   // live recolor
    });
    row.appendChild(dot); row.appendChild(label); row.appendChild(input);
    wrap.appendChild(row);
  });
}

function syncMaterialBlock() {
  // The 16-preset appearance panel shows in "material" mode; the per-material color panel
  // shows in "bymaterial" mode.
  document.getElementById("vc-material").hidden = mode !== "material";
  const byPanel = document.getElementById("vc-bymaterial");
  byPanel.hidden = mode !== "bymaterial";
  if (mode === "bymaterial") renderMaterialColors();
}

// Called when the element map arrives (a separate promise from the glb): reveal the
// By-material mode only if this model has materials, re-render the panel, and re-apply the
// mode so a by-material recolor now has both the meshes and the material data.
function onElementMapReady() {
  updateByMaterialButton();
}

// The bounding box of the real GEOMETRY only (the picked meshes), excluding helper gizmos. Origin
// axes + connector triads are AxesHelpers sized to a fraction of their part's extent, so a large
// part with a horizontal connector (e.g. a glass curtain wall) has a triad arm that plunges well
// below grade; if those were included, frameModel would ground THAT arm and float the whole model.
// Framing to meshes only keeps the drop-to-ground based on the actual building, not the markers.
function meshBox() {
  const box = new THREE.Box3();
  let any = false;
  modelRoot.traverse(o => {
    if (o.isMesh) { box.expandByObject(o); any = true; }
  });
  return any ? box : new THREE.Box3().setFromObject(modelRoot);
}

function frameModel() {
  const box = meshBox();
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  modelRoot.position.sub(center);
  // Only scene-level edges (the single-part path) need the manual re-centering; assembly edges are
  // parented to their instance mesh (so they move with the part under motion) and ride modelRoot's
  // shift already - shifting them again would double-offset them.
  const sceneEdges = edges.filter(e => e.parent === scene);
  sceneEdges.forEach(e => e.position.sub(center));
  // Z-up scene: drop the model onto the ground plane (z=0 at its base) along +Z.
  const half = size.z / 2;
  modelRoot.position.z += half; sceneEdges.forEach(e => e.position.z += half);
  const radius = Math.max(size.x, size.y, size.z);
  camera.position.set(radius * 1.4, -radius * 1.6, radius * 1.05);
  camera.near = radius / 100; camera.far = radius * 50; camera.updateProjectionMatrix();
  controls.target.set(0, 0, half); controls.update();
  // Fit the shadow frustum to the model so the shadow map is not spread thin over a huge area
  // (which reads as coarse, streaky floor shadows). A little margin so a moving part's shadow
  // (under motion the parts sweep a bit beyond the rest bbox) stays inside the frustum.
  shadowRadius = radius * 1.6;
  fitShadowCameras();
  // Size the world-origin marker to a fraction of the model extent so it reads as a small
  // reference at any scale. modelRoot is re-centered above, so the marker (at the scene origin)
  // sits under the model's center, marking where world (0,0,0) is for the current view.
  const originHelper = scene.getObjectByName("worldOrigin");
  if (originHelper) originHelper.scale.setScalar(Math.max(radius * 0.15, 1e-4) / 0.02);
  // Scene axes now equal part axes (X, Y, Z), so the size readout is direct.
  document.getElementById("i-size").textContent =
    `${size.x.toFixed(1)} × ${size.y.toFixed(1)} × ${size.z.toFixed(1)} m`;
}

function loadModel(name) {
  spinner.style.display = "flex";
  loader.load(modelUrl(name), gltf => {
    clearModel();
    // glTF lands the authored Z-up model Y-up; rotate +90deg about X so scene space equals
    // part space (a face authored +Z reads +Z in the viewport). Everything downstream
    // (framing, edges, picking) then operates in the part's own frame.
    gltf.scene.rotation.x = Math.PI / 2;
    modelRoot = gltf.scene;
    let tris = 0, meshes = 0;
    modelRoot.traverse(o => {
      if (o.isMesh) {
        meshes++;
        pickParts.push(o);
        const geo = o.geometry;
        tris += (geo.index ? geo.index.count : geo.attributes.position.count) / 3;
        // Edge overlay: draw a line only where adjacent faces meet above this angle.
        // It must sit ABOVE the tessellation's angular deflection (~17deg/facet at the
        // pinned 0.3 rad, build123d_kernel._ANGULAR_DEFLECTION) or facet SEAMS get drawn
        // and a smooth curve reads "cracked"; 25deg clears the facet angle while still
        // catching real geometric edges (~90deg corners/rims). If the angular deflection
        // is ever raised past ~22deg, raise this threshold in step.
        const line = new THREE.LineSegments(
          new THREE.EdgesGeometry(geo, 25),
          new THREE.LineBasicMaterial({ color: cssColor("--edge") }));
        o.updateWorldMatrix(true, false); line.applyMatrix4(o.matrixWorld);
        edges.push(line); scene.add(line);
      }
    });
    scene.add(modelRoot);
    document.getElementById("i-tris").textContent = Math.round(tris).toLocaleString();
    document.getElementById("i-meshes").textContent = meshes;
    applyMode(); frameModel();
    spinner.style.display = "none";
  }, undefined, err => { spinner.textContent = "failed to load model"; console.error(err); });
  fetch(apiUrl(`/elementmap/${name}`))
    .then(r => r.ok ? r.json() : null)
    .then(j => { elementMap = j; onElementMapReady(); })
    .catch(() => { elementMap = null; onElementMapReady(); });
  loadBom(name);
  loadHierarchy(name);
}

// ---- Bill of materials panel ----
const BOM_FIELDS = [
  { key: "floor_area", label: "Floor area", unit: "m²", digits: 1 },
  { key: "roof_area", label: "Roof area", unit: "m²", digits: 1 },
  { key: "wall_volume", label: "Wall volume", unit: "m³", digits: 2 },
  { key: "wall_face_area", label: "Wall face area", unit: "m²", digits: 1 },
  { key: "door_count", label: "Doors", unit: "", digits: 0 },
  { key: "window_count", label: "Windows", unit: "", digits: 0 },
];

function loadBom(name) {
  const body = document.getElementById("bom-body");
  fetch(apiUrl(`/bom/${name}`)).then(r => r.ok ? r.json() : Promise.reject()).then(bom => {
    body.innerHTML = "";
    BOM_FIELDS.forEach(f => {
      if (!(f.key in bom)) return;
      const row = document.createElement("div"); row.className = "bom-row";
      const v = Number(bom[f.key]).toFixed(f.digits);
      row.innerHTML = `<span class="k">${f.label}</span>` +
        `<span class="v">${v}<span class="u">${f.unit}</span></span>`;
      body.appendChild(row);
    });
  }).catch(() => { body.innerHTML = '<div class="panel-empty">no BOM for this model</div>'; });
}

// ---- Hierarchy tab (Blender-style tree, non-interactive) ----
// Icons are Google Material Symbols (referenced by glyph name, drawn by the font), chosen
// per node kind and, for features, per OP CATEGORY (additive / subtractive / dress-up /
// boolean / placement / sketch). An unknown op falls back to the generic `feature` glyph.
const TREE_ICONS = {
  part: "deployed_code",             // a 3D cube = the part
  feature: "settings",               // generic op
  element: "check_box_outline_blank",// a sketch primitive (empty square)
  sketch: "draw",                    // a sketch
  additive: "add_box",               // extrude/revolve/loft/sweep/rib/wrap (add material)
  subtractive: "indeterminate_check_box",  // pocket/hole/groove (remove material)
  dressup: "rounded_corner",         // fillet/chamfer/draft/shell (edge/wall treatment)
  boolean: "join",                   // boolean/split (combine/divide bodies)
  placement: "grid_view",            // pattern/mirror/transform (place copies)
  group: "folder",                   // the Bodies folder
  body: "deployed_code",             // a built body (cube)
};
const OP_CATEGORY = {
  sketch: "sketch",
  extrude: "additive", revolve: "additive", loft: "additive", sweep: "additive",
  rib: "additive", wrap: "additive",
  pocket: "subtractive", hole: "subtractive", groove: "subtractive",
  fillet: "dressup", chamfer: "dressup", draft: "dressup", shell: "dressup",
  boolean: "boolean", split: "boolean",
  pattern: "placement", mirror: "placement", transform: "placement",
};
function iconKey(node) {
  if (node.kind === "part") return "part";
  if (node.kind === "element") return "element";
  if (node.kind === "group") return "group";   // the Bodies folder
  if (node.kind === "body") return "body";      // a built body (cube)
  return OP_CATEGORY[node.op] || "feature";  // feature: category by op, else generic gear
}

function loadHierarchy(name) {
  const body = document.getElementById("hierarchy-body");
  fetch(apiUrl(`/hierarchy/${name}`)).then(r => r.ok ? r.json() : Promise.reject()).then(tree => {
    body.innerHTML = "";
    body.appendChild(treeNode(tree));
  }).catch(() => { body.innerHTML = '<div class="panel-empty">no hierarchy for this model</div>'; });
}

// Build one tree node (and its subtree). The twist toggles a node's children; leaves
// hide the twist. Names/ops carry a class so the label toggle can hide them.
function treeNode(node) {
  const wrap = document.createElement("div");
  wrap.className = "tree-node";
  const row = document.createElement("div");
  row.className = "tree-row";
  const kids = node.children || [];
  const twist = document.createElement("span");
  twist.className = "tree-twist" + (kids.length ? "" : " leaf");
  twist.textContent = "▼";
  const key = iconKey(node);
  const ico = document.createElement("span");
  ico.className = "tree-ico material-symbols-rounded " + node.kind + " " + key;
  ico.textContent = TREE_ICONS[key] || TREE_ICONS.feature;
  const label = node.name || node.id || "?";
  row.innerHTML = "";
  row.appendChild(twist);
  row.appendChild(ico);
  const nameEl = document.createElement("span");
  nameEl.className = "tree-name"; nameEl.textContent = label;
  row.appendChild(nameEl);
  if (node.op) {
    const opEl = document.createElement("span");
    opEl.className = "tree-op"; opEl.textContent = node.op;
    row.appendChild(opEl);
  }
  // A sketch feature shows its constraint status inline: a colored dot (green/amber/red),
  // plus a muted "dof N" label that reveals on row hover (a native title as a fallback), so
  // the constraint state is easy to read. Replaces the old separate status box.
  if (node.status) {
    const fail = (node.failing_ids && node.failing_ids.length)
      ? ` [${node.failing_ids.join(", ")}]` : "";
    const dot = document.createElement("span");
    dot.className = "status-dot tree-status " + node.status;
    row.appendChild(dot);
    const dof = document.createElement("span");
    dof.className = "tree-dof";
    dof.textContent = `${node.status}, dof ${node.dof}${fail}`;
    row.appendChild(dof);
    row.title = dof.textContent;
  }
  // A material chip (part default or a feature override) rides at the row's end.
  if (node.material) {
    const mat = document.createElement("span");
    mat.className = "tree-mat"; mat.textContent = node.material;
    mat.title = "material: " + node.material;
    row.appendChild(mat);
  }
  wrap.appendChild(row);
  if (kids.length) {
    const childWrap = document.createElement("div");
    childWrap.className = "tree-children";
    kids.forEach(c => childWrap.appendChild(treeNode(c)));
    wrap.appendChild(childWrap);
    twist.addEventListener("click", () => {
      const collapsed = wrap.classList.toggle("tree-collapsed");
      twist.textContent = collapsed ? "▶" : "▼";
    });
  }
  return wrap;
}

// ---- Right sidebar: tabs, collapse (two toggles), label toggle, drag separator ----
const rightTabs = document.querySelectorAll("#right-sidebar .tab");
const treeTextToggle = document.getElementById("tree-text-toggle");
function setTab(name) {
  rightTabs.forEach(t => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach(p =>
    p.classList.toggle("active", p.id === "tab-" + name));
  treeTextToggle.hidden = name !== "hierarchy";
  localStorage.setItem("ncad.rs.tab", name);
}
rightTabs.forEach(t => t.addEventListener("click", () => setTab(t.dataset.tab)));
// Restore the saved tab, but only if it still exists (a removed tab like the old "plan" falls back
// to hierarchy so the sidebar is never left blank).
const savedTab = localStorage.getItem("ncad.rs.tab");
const savedTabExists = [...rightTabs].some(t => t.dataset.tab === savedTab);
setTab(savedTabExists ? savedTab : "hierarchy");

// Label toggle for the hierarchy (icons-only when off), persisted.
function setTreeText(on) {
  document.getElementById("tab-hierarchy").classList.toggle("hide-text", !on);
  treeTextToggle.classList.toggle("active", on);
  localStorage.setItem("ncad.rs.treetext", on ? "1" : "0");
}
treeTextToggle.addEventListener("click", () =>
  setTreeText(!treeTextToggle.classList.contains("active")));
setTreeText(localStorage.getItem("ncad.rs.treetext") !== "0");

// Collapse/expand: the floating toggle flips state; the rail and header buttons are
// explicit open/close. State persists.
function setRightSidebar(open) {
  document.body.classList.toggle("right-collapsed", !open);
  document.getElementById("vc-sidebar-toggle").classList.toggle("active", open);
  document.getElementById("right-toggle").classList.toggle("collapsed", !open);
  localStorage.setItem("ncad.rs.open", open ? "1" : "0");
  // During the width transition the canvas is stretched by CSS to fill the stage. Track
  // the camera aspect to the displayed canvas size each frame so the image is never
  // stretched (this is cheap and does NOT recreate the drawing buffer, so no flicker),
  // then do a single crisp setSize once the slide has finished.
  const started = performance.now();
  (function follow() {
    const w = renderer.domElement.clientWidth, h = renderer.domElement.clientHeight;
    if (w && h) { camera.aspect = w / h; camera.updateProjectionMatrix(); }
    if (performance.now() - started < 320) requestAnimationFrame(follow);
    else fitRendererToStage();
  })();
}
function toggleRightSidebar() {
  setRightSidebar(document.body.classList.contains("right-collapsed"));
}
document.getElementById("vc-sidebar-toggle").addEventListener("click", toggleRightSidebar);
document.getElementById("right-toggle").addEventListener("click", toggleRightSidebar);
setRightSidebar(localStorage.getItem("ncad.rs.open") !== "0");

// Draggable separator for the right sidebar width (persisted), mirroring the left one.
const RIGHT_WIDTH_KEY = "ncad.rs.width";
const rightResizerEl = document.getElementById("right-resizer");
let rightWidth = 320;
// Width lives in the --rs-width CSS variable so the collapse animation (width -> 0) and
// the drag both drive the same property.
function applyRightWidth(px) {
  rightWidth = Math.max(220, Math.min(560, px));
  document.documentElement.style.setProperty("--rs-width", rightWidth + "px");
}
const savedRightWidth = localStorage.getItem(RIGHT_WIDTH_KEY);
if (savedRightWidth) applyRightWidth(parseFloat(savedRightWidth));
rightResizerEl.addEventListener("pointerdown", ev => {
  ev.preventDefault();
  document.body.classList.add("resizing-sidebar");
  rightResizerEl.classList.add("dragging");
  // Suppress the width transition while dragging so it tracks the pointer 1:1.
  document.getElementById("right-sidebar").style.transition = "none";
  const onMove = e => {
    // Sidebar is anchored to the right edge; width grows as the pointer moves left.
    // The canvas stretches via CSS live; the backing buffer is refit on release.
    applyRightWidth(window.innerWidth - e.clientX);
  };
  const onUp = () => {
    document.body.classList.remove("resizing-sidebar");
    rightResizerEl.classList.remove("dragging");
    document.getElementById("right-sidebar").style.transition = "";
    localStorage.setItem(RIGHT_WIDTH_KEY, rightWidth);
    fitRendererToStage();
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onUp);
  };
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
});
rightResizerEl.addEventListener("dblclick", () => {
  applyRightWidth(320);
  localStorage.removeItem(RIGHT_WIDTH_KEY);
  fitRendererToStage();
});

// ---- swatches ----
const swatchWrap = document.getElementById("swatches");
MATERIALS.forEach((m, i) => {
  const s = document.createElement("div");
  s.className = "swatch" + (i === materialIndex ? " active" : "");
  s.style.background = "#" + m.color.toString(16).padStart(6, "0");
  s.title = m.name;
  s.addEventListener("click", () => {
    materialIndex = i; localStorage.setItem("ncad.material", String(i));
    document.querySelectorAll(".swatch").forEach(e => e.classList.remove("active"));
    s.classList.add("active");
    if (mode !== "material") { setMode("material"); } else { applyMode(); }
  });
  swatchWrap.appendChild(s);
});

// ---- floating viewport controls: modes, toggles, lighting, reset (all persisted) ----
function setMode(next) {
  mode = next;
  localStorage.setItem("ncad.mode", next);
  document.querySelectorAll("#vc-modes .vc-btn").forEach(b =>
    b.classList.toggle("active", b.dataset.mode === next));
  syncMaterialBlock();
  applyMode();
}
document.querySelectorAll("#vc-modes .vc-btn").forEach(btn =>
  btn.addEventListener("click", () => setMode(btn.dataset.mode)));

// A persisted boolean scene toggle rendered as an icon button (active = on).
function bindVcToggle(name, key, apply) {
  const el = document.querySelector('.vc-toggle[data-toggle="' + name + '"]');
  const saved = localStorage.getItem(key);
  const on = saved !== null ? saved === "1" : el.classList.contains("active");
  el.classList.toggle("active", on);
  apply(on);
  el.addEventListener("click", () => {
    const now = !el.classList.contains("active");
    el.classList.toggle("active", now);
    localStorage.setItem(key, now ? "1" : "0");
    apply(now);
  });
}
bindVcToggle("edges", "ncad.edges", v => { showEdges = v; applyMode(); });
bindVcToggle("grid", "ncad.grid", v => { grid.visible = v; });
bindVcToggle("shadow", "ncad.shadow", v => { castShadows = v; applyMode(); });
bindVcToggle("rotate", "ncad.rotate", v => {
  autoRotate = v;
  if (orientationMode === "axis") controls.autoRotate = v;
});
bindVcToggle("freelook", "ncad.freelook", v => { setOrientationMode(v ? "free" : "axis"); });
bindVcToggle("connectors", "ncad.connectors", v => {
  showConnectors = v;
  connectorGizmos.forEach(g => { g.visible = v; });
});
bindVcToggle("origins", "ncad.origins", v => {
  showOrigins = v;
  originGizmos.forEach(g => { g.visible = v; });
});
bindVcToggle("isolate", "ncad.isolate", v => { isolateOn = v; refreshInstanceVisuals(); });
bindVcToggle("joints", "ncad.joints", v => { showJoints = v; jointGizmos.forEach(g => { g.visible = v; }); });
bindVcToggle("traces", "ncad.traces", v => { showTraces = v; traceLines.forEach(l => { l.visible = v; }); });
document.getElementById("vc-reset").addEventListener("click", () => { if (modelRoot) frameModel(); });

// The assembly floating controls show in Assemblies AND Motion mode (both render a scene of placed
// instances with origins/connectors/joint overlays).
function syncAssemblyControls() {
  const on = isAssemblyScene();
  document.getElementById("vc-assembly").hidden = !on;
  document.getElementById("vc-asm-sep").hidden = !on;
}

// Restore the saved display mode (default solid). Buttons reflect it; applyMode on load.
setMode(localStorage.getItem("ncad.mode") || "solid");

// Lighting: click the button to cycle presets, or use the caret dropdown to pick one.
// Each preset has its own icon so they are distinct at a glance.
const LIGHT_ORDER = ["sun", "natural", "studio", "spotlight", "overcast"];
const LIGHT_NAMES = { sun: "Sun", natural: "Natural", studio: "Studio", spotlight: "Spotlight", overcast: "Overcast" };
const LIGHT_ICONS = {
  sun: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  natural: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3.5"/><path d="M12 2.5v1.6M12 19.9v1.6M2.5 12h1.6M19.9 12h1.6M5.2 5.2l1.1 1.1M17.7 17.7l1.1 1.1M18.8 5.2l-1.1 1.1M6.3 17.7l-1.1 1.1"/></svg>',
  studio: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="7" r="2.3"/><circle cx="5" cy="16" r="2.3"/><circle cx="19" cy="16" r="2.3"/><path d="M12 9.3v3M9.8 13.8 6.9 15M14.2 13.8l2.9 1.2"/></svg>',
  spotlight: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6l3 6H6L9 3Z"/><path d="M8 9c0 4 1.5 7 4 12 2.5-5 4-8 4-12"/></svg>',
  overcast: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M7 18h9a4 4 0 0 0 .4-8 5.5 5.5 0 0 0-10.6 1.3A3.5 3.5 0 0 0 7 18Z"/></svg>',
};
const lightBtn = document.getElementById("vc-light");
const lightIconEl = document.getElementById("vc-light-icon");
const lightLabel = document.getElementById("vc-light-label");
const lightCaret = document.getElementById("vc-light-caret");
const lightMenu = document.getElementById("vc-light-menu");
lightMenu.querySelectorAll(".vc-mi").forEach(mi => { mi.innerHTML = LIGHT_ICONS[mi.parentElement.dataset.light]; });
let lightIdx = Math.max(0, LIGHT_ORDER.indexOf(localStorage.getItem("ncad.light") || "sun"));

function applyLight() {
  const name = LIGHT_ORDER[lightIdx];
  setLighting(name);
  lightIconEl.innerHTML = LIGHT_ICONS[name];
  lightLabel.textContent = LIGHT_NAMES[name];
  lightBtn.title = "Lighting: " + LIGHT_NAMES[name] + " (click to cycle)";
  lightMenu.querySelectorAll("button").forEach(b => b.classList.toggle("active", b.dataset.light === name));
}
lightBtn.addEventListener("click", () => { lightIdx = (lightIdx + 1) % LIGHT_ORDER.length; applyLight(); });
lightCaret.addEventListener("click", ev => { ev.stopPropagation(); lightMenu.hidden = !lightMenu.hidden; });
lightMenu.querySelectorAll("button").forEach(b =>
  b.addEventListener("click", () => { lightIdx = LIGHT_ORDER.indexOf(b.dataset.light); applyLight(); lightMenu.hidden = true; }));
document.addEventListener("mousedown", ev => {
  if (!lightMenu.hidden && !lightMenu.contains(ev.target) && ev.target !== lightCaret && !lightCaret.contains(ev.target)) {
    lightMenu.hidden = true;
  }
});
document.addEventListener("keydown", ev => { if (ev.key === "Escape") lightMenu.hidden = true; });
applyLight();

// Material swatches start hidden (solid is the default mode).
syncMaterialBlock();

// ---- Show-text toggle: reveal each icon's label (persisted) ----
const controlsEl = document.getElementById("viewport-controls");
const textBtn = document.getElementById("vc-text");
function applyShowText(on) {
  controlsEl.classList.toggle("show-text", on);
  textBtn.classList.toggle("active", on);
  // Tooltip describes the action, i.e. what a click will do next.
  const tip = on ? "Show icons only" : "Show labels";
  textBtn.title = tip;
  textBtn.setAttribute("aria-label", tip);
  localStorage.setItem("ncad.vc.text", on ? "1" : "0");
}
textBtn.addEventListener("click", () => applyShowText(!controlsEl.classList.contains("show-text")));
applyShowText(localStorage.getItem("ncad.vc.text") === "1");

// ---- Panel placement: corner anchor picker + free drag with edge snapping ----
const CORNER_KEY = "ncad.vc.corner", POS_KEY = "ncad.vc.pos";
const cornerBtn = document.getElementById("vc-corner");
const cornerPop = document.getElementById("vc-corner-pop");
const MARGIN = 16;

// Anchor to a corner using pixel left/top (the same basis as drag/snap) so the move can
// animate smoothly. `animate` is true only for user clicks, not the initial restore.
function anchorCorner(corner, animate) {
  controlsEl.dataset.corner = corner;
  const [v, h] = corner.split("-");
  const stageRect = stage.getBoundingClientRect();
  const r = controlsEl.getBoundingClientRect();
  const x = h === "left" ? MARGIN : stageRect.width - r.width - MARGIN;
  const y = v === "top" ? MARGIN : stageRect.height - r.height - MARGIN;
  if (animate) {
    controlsEl.classList.add("vc-animate");
    setTimeout(() => controlsEl.classList.remove("vc-animate"), 320);
  }
  placeFree(x, y);
  localStorage.setItem(CORNER_KEY, corner);
  localStorage.removeItem(POS_KEY);
}

cornerBtn.addEventListener("click", ev => { ev.stopPropagation(); cornerPop.hidden = !cornerPop.hidden; });
cornerPop.querySelectorAll("button").forEach(b =>
  b.addEventListener("click", () => { anchorCorner(b.dataset.corner, true); cornerPop.hidden = true; }));
// Close the corner popup when clicking anywhere outside it or the button, or on Escape.
document.addEventListener("mousedown", ev => {
  if (!cornerPop.hidden && !cornerPop.contains(ev.target) && ev.target !== cornerBtn && !cornerBtn.contains(ev.target)) {
    cornerPop.hidden = true;
  }
});
document.addEventListener("keydown", ev => { if (ev.key === "Escape") cornerPop.hidden = true; });

// Free-drag from the grip; on release, snap to the nearest viewport edge. A top/bottom
// snap keeps the panel horizontal; a left/right snap flips it vertical.
function placeFree(x, y) {
  controlsEl.style.left = x + "px"; controlsEl.style.top = y + "px";
  controlsEl.style.right = ""; controlsEl.style.bottom = "";
}
function snapToEdge() {
  const stageRect = stage.getBoundingClientRect();
  const r = controlsEl.getBoundingClientRect();
  const cx = r.left - stageRect.left + r.width / 2, cy = r.top - stageRect.top + r.height / 2;
  const dl = cx, dr = stageRect.width - cx, dt = cy, db = stageRect.height - cy;
  const min = Math.min(dl, dr, dt, db);
  // Snap to the nearest edge but keep the panel's shape (no vertical reorientation).
  let x = r.left - stageRect.left, y = r.top - stageRect.top;
  if (min === dl) x = MARGIN;
  else if (min === dr) x = stageRect.width - r.width - MARGIN;
  else if (min === dt) y = MARGIN;
  else y = stageRect.height - r.height - MARGIN;
  x = Math.max(MARGIN, Math.min(stageRect.width - r.width - MARGIN, x));
  y = Math.max(MARGIN, Math.min(stageRect.height - r.height - MARGIN, y));
  placeFree(x, y);
  localStorage.setItem(POS_KEY, JSON.stringify({ x, y }));
  localStorage.removeItem(CORNER_KEY);
}

document.querySelector(".vc-grip").addEventListener("mousedown", ev => {
  ev.preventDefault();
  const stageRect = stage.getBoundingClientRect();
  const r = controlsEl.getBoundingClientRect();
  const offX = ev.clientX - r.left, offY = ev.clientY - r.top;
  const onMove = e => placeFree(e.clientX - stageRect.left - offX, e.clientY - stageRect.top - offY);
  const onUp = () => {
    snapToEdge();
    window.removeEventListener("mousemove", onMove);
    window.removeEventListener("mouseup", onUp);
  };
  window.addEventListener("mousemove", onMove);
  window.addEventListener("mouseup", onUp);
});

// Restore saved placement: a free/snapped position wins, else a corner, else default.
const savedPos = localStorage.getItem(POS_KEY);
if (savedPos) {
  try { const p = JSON.parse(savedPos); placeFree(p.x, p.y); }
  catch (e) { anchorCorner("top-left"); }
} else {
  anchorCorner(localStorage.getItem(CORNER_KEY) || "top-left");
}

// ---- Spec combobox + models list ----
let specTree = [], selectedSpec = null, activeModel = null;
const REGEN_SVG = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/></svg>';
const DELETE_SVG = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>';

// Session log: appended to the Logs tab (newest at the bottom), not persisted across reloads.
// level is "info" (default) | "success" | "warn" | "error" (color-coded, themed for light + dark);
// a truthy boolean still maps to "error" for older call sites. ncad-service messages are prefixed
// [ncad]; pass opts.raw=true to skip the prefix (a third-party / non-service line).
function log(message, level, opts) {
  const body = document.getElementById("logs-body");
  if (!body) return;
  const empty = body.querySelector(".panel-empty");
  if (empty) empty.remove();
  const lvl = level === true ? "error" : (level || "info");
  const line = document.createElement("div");
  line.className = "log-line log-" + lvl;
  const now = new Date();
  // hh:mm:ss.s (one-decimal seconds).
  const t = now.toTimeString().slice(0, 8) + "." + Math.floor(now.getMilliseconds() / 100);
  line.innerHTML = '<span class="log-time"></span>';
  line.querySelector(".log-time").textContent = t;
  const text = (opts && opts.raw) ? message : "[ncad] " + message;
  line.appendChild(document.createTextNode(text));
  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}

function toast(message, isError) {
  log(message, isError);  // every toast also lands in the persistent Logs tab
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.toggle("error", !!isError);
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 3200);
}

function flattenSpecs(nodes, out) {
  for (const node of nodes) {
    if (node.type === "dir") flattenSpecs(node.children, out);
    else out.push({ name: node.name, path: node.path, kind: node.kind || "part" });
  }
  return out;
}

function renderSpecTree(filter) {
  const box = document.getElementById("spec-tree");
  const all = flattenSpecs(specTree, []);
  const q = (filter || "").toLowerCase();
  // The combobox shows only specs of the current mode's kind: Parts lists part docs, Assemblies
  // lists .asm.hocon docs, Motion lists .motion.hocon docs (each a motion study driving an assembly).
  const wantKind = viewMode === "motion" ? "motion"
                 : viewMode === "physics" ? "physics"
                 : viewMode === "assemblies" ? "assembly" : "part";
  const matches = all.filter(s => s.kind === wantKind && s.path.toLowerCase().includes(q));
  box.innerHTML = "";
  let currentDir = null;
  for (const s of matches) {
    const dir = s.path.includes("/") ? s.path.slice(0, s.path.lastIndexOf("/")) : "";
    if (dir !== currentDir) {
      currentDir = dir;
      if (dir) { const d = document.createElement("div"); d.className = "dir"; d.textContent = dir; box.appendChild(d); }
    }
    const row = document.createElement("div");
    row.className = "spec" + (selectedSpec === s.path ? " active" : "");
    row.textContent = s.name;
    row.title = s.path;
    row.addEventListener("mousedown", () => {
      selectedSpec = s.path;
      document.getElementById("spec-search").value = s.path;
      syncSpecClear();
      box.hidden = true;
    });
    box.appendChild(row);
  }
  box.hidden = matches.length === 0;
}

function loadSpecs() {
  fetch(apiUrl("/specs")).then(r => r.json()).then(data => { specTree = data.tree || []; });
}

function renderModelList(models) {
  const list = document.getElementById("model-list");
  list.innerHTML = "";
  if (!models.length) { list.innerHTML = '<div class="panel-empty">no models in out/</div>'; return; }
  for (const m of models) {
    const row = document.createElement("div");
    row.className = "model-row" + (activeModel === m.name ? " active" : "");
    const name = document.createElement("div");
    name.className = "name"; name.textContent = m.name; name.title = m.name;
    row.appendChild(name);
    const actions = document.createElement("div");
    actions.className = "row-actions";
    const regen = iconButton("Regenerate", REGEN_SVG, "act-regen");
    regen.addEventListener("click", ev => { ev.stopPropagation(); regenerate(m); });
    const del = iconButton("Delete", DELETE_SVG, "act-delete");
    del.addEventListener("click", ev => { ev.stopPropagation(); removeModel(m.name); });
    actions.appendChild(regen); actions.appendChild(del);
    row.appendChild(actions);
    row.addEventListener("click", () => selectModel(m.name));
    list.appendChild(row);
  }
  scrollActiveIntoView(list);
}

function refreshModels() {
  return fetch(apiUrl("/models")).then(r => r.json()).then(data => { renderModelList(data.models); return data.models; });
}

function selectModel(name) {
  activeModel = name;
  syncExportControl();
  // Persist the selection so a page refresh restores it (see the boot logic). Keyed by mode
  // so Parts and Assemblies each remember their own last-viewed model independently.
  localStorage.setItem("ncad.active.parts", name);
  loadModel(name);
  refreshModels();
}

// ---- Assemblies mode ----
// Parts mode (default) is unchanged: it lists /api/models and loads a single glb. Assemblies mode
// lists /api/assemblies and loads an assembly scene (its parts placed by their solved/explicit
// matrices). The choice persists in localStorage, like the theme and sidebar width.
// (viewMode is declared earlier, before setMode's init call, so distinctMaterials can read it
// during the initial setMode without a temporal-dead-zone error.)
const partGlbCache = {};  // part_glb filename -> loaded THREE.Object3D (loaded once, instanced)
const assemblySources = {};  // assembly name -> source .asm.hocon path (for regenerate)
const motionSources = {};    // assembly name -> source .motion.hocon path (for motion regenerate)

function refreshAssemblies() {
  return fetch(apiUrl("/assemblies")).then(r => r.json()).then(data => {
    renderAssemblyList(data.assemblies || []); return data.assemblies || []; });
}

function renderAssemblyList(names) {
  const list = document.getElementById("model-list");
  list.innerHTML = "";
  if (!names.length) { list.innerHTML = '<div class="panel-empty">no assemblies in out/</div>'; return; }
  for (const name of names) {
    const row = document.createElement("div");
    row.className = "model-row" + (activeModel === name ? " active" : "");
    const label = document.createElement("div");
    label.className = "name"; label.textContent = name; label.title = name;
    row.appendChild(label);
    // Same row actions as parts: regenerate (recompose from the recorded source) + delete.
    const actions = document.createElement("div");
    actions.className = "row-actions";
    const regen = iconButton("Regenerate", REGEN_SVG, "act-regen");
    regen.addEventListener("click", ev => { ev.stopPropagation(); regenerateAssembly(name); });
    const del = iconButton("Delete", DELETE_SVG, "act-delete");
    del.addEventListener("click", ev => { ev.stopPropagation(); removeAssembly(name); });
    actions.appendChild(regen); actions.appendChild(del);
    row.appendChild(actions);
    row.addEventListener("click", () => selectAssembly(name));
    list.appendChild(row);
  }
  scrollActiveIntoView(list);
}

function selectAssembly(name, verbose, timing) {
  activeModel = name;
  syncExportControl();
  localStorage.setItem("ncad.active.assemblies", name);
  loadAssembly(name, verbose, timing);
  refreshAssemblies();
}

// ---- Motion mode ----
// A driven assembly (one with a <name>.motion.json trajectory) shown with a playback timeline.
// It loads the SAME scene as Assemblies mode (loadAssembly), then setupMotion (called inside
// loadAssembly) reveals the timeline because it is Motion mode.
function refreshMotions() {
  // The /motions payload is [{name, label}] (label = the declared fps/steps). renderMotionList
  // consumes the objects; the boot callers only need the names, so return those.
  return fetch(apiUrl("/motions")).then(r => r.json()).then(data => {
    const motions = data.motions || [];
    renderMotionList(motions);
    return motions.map(m => m.name);
  });
}

function renderMotionList(motions) {
  const list = document.getElementById("model-list");
  list.innerHTML = "";
  if (!motions.length) {
    list.innerHTML = '<div class="panel-empty">no driven assemblies in out/ (add a motion block)</div>';
    return;
  }
  for (const motion of motions) {
    const name = motion.name;
    const row = document.createElement("div");
    row.className = "model-row" + (activeModel === name ? " active" : "");
    const label = document.createElement("div");
    label.className = "name"; label.textContent = name; label.title = name;
    // The declared fps/steps sits to the right of the name as a small muted suffix (never a value
    // the doc did not declare; absent when the trajectory could not be read).
    if (motion.label) {
      const meta = document.createElement("span");
      meta.className = "row-meta"; meta.textContent = motion.label;
      label.appendChild(meta);
    }
    row.appendChild(label);
    // Row actions mirror the Assemblies tab: regenerate (re-run the motion study from its recorded
    // .motion.hocon source) + delete (removes the assembly scene AND its .motion.json trajectory).
    const actions = document.createElement("div");
    actions.className = "row-actions";
    const regen = iconButton("Regenerate", REGEN_SVG, "act-regen");
    regen.addEventListener("click", ev => { ev.stopPropagation(); regenerateMotion(name); });
    const del = iconButton("Delete", DELETE_SVG, "act-delete");
    del.addEventListener("click", ev => { ev.stopPropagation(); removeMotion(name); });
    actions.appendChild(regen); actions.appendChild(del);
    row.appendChild(actions);
    row.addEventListener("click", () => selectMotion(name));
    list.appendChild(row);
  }
  scrollActiveIntoView(list);
}

function regenerateMotion(name) {
  const source = motionSources[name];
  if (!source) { toast("no motion source recorded for " + name + "; pick it in the Spec box", true); return; }
  motionBuildSpec(source);
}

function removeMotion(name) {
  // Delete removes the assembly scene sidecar + its .motion.json trajectory (delete_assembly on the
  // server removes both). No confirmation: re-running the motion study from the spec is cheap.
  fetch(apiUrl("/assembly/" + encodeURIComponent(name) + "/delete"), { method: "POST" })
    .then(r => r.json())
    .then(() => { if (activeModel === name) { activeModel = null; clearActive("motion"); clearModel(); } refreshMotions(); toast("deleted " + name); })
    .catch(() => toast("could not delete " + name, true));
}

function selectMotion(name, verbose, timing) {
  activeModel = name;
  syncExportControl();
  localStorage.setItem("ncad.active.motion", name);
  // Pass verbose + timing through so a real motion (re)build logs the same "build + render = total"
  // split as Parts and Assemblies; a plain re-select (no timing) stays quiet.
  loadAssembly(name, verbose, timing);
  refreshMotions();
}

// ---- Physics mode list (robots = assemblies with a .robot.json sidecar) ----
function refreshRobots() {
  return fetch(apiUrl("/robots")).then(r => r.json()).then(data => {
    const robots = data.robots || [];
    renderRobotList(robots);
    return robots.map(r => r.name);
  });
}

function renderRobotList(robots) {
  const list = document.getElementById("model-list");
  list.innerHTML = "";
  if (!robots.length) {
    list.innerHTML = '<div class="panel-empty">no robots in out/ (run `ncad physics`)</div>';
    return;
  }
  for (const robot of robots) {
    const name = robot.name;
    const row = document.createElement("div");
    row.className = "model-row" + (activeModel === name ? " active" : "");
    const label = document.createElement("div");
    label.className = "name"; label.textContent = name; label.title = name;
    if (robot.label) {
      const meta = document.createElement("span");
      meta.className = "row-meta"; meta.textContent = robot.label;
      label.appendChild(meta);
    }
    row.appendChild(label);
    row.addEventListener("click", () => selectRobot(name));
    list.appendChild(row);
  }
  scrollActiveIntoView(list);
}

function selectRobot(name, verbose, timing) {
  activeModel = name;
  syncExportControl();
  localStorage.setItem("ncad.active.physics", name);
  // verbose + timing flow through so a real physics (re)build logs the "build + render = total"
  // split like Parts/Assemblies/Motion; a plain re-select stays quiet.
  loadAssembly(name, verbose, timing);
  refreshRobots();
}

function assembleSpec(spec) {
  if (!spec) { toast("select an assembly spec first", true); return; }
  spinner.style.display = "block";
  const t0 = performance.now();   // client wall-clock start (button click), for the render split
  fetch(apiUrl("/assemble"), { method: "POST", headers: { "Content-Type": "application/json" },
                           body: JSON.stringify({ spec }) })
    .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "assemble failed"); return d; })
    .then(d => {
      assemblySources[d.assembled] = spec;  // remember the source for regenerate
      // Timing (build / solve / render, a profiling starting point): the server build_ms (total
      // server time) + solve_ms (the constraint/motion solve slice within it) + a render-done
      // callback that fires when loadAssembly finishes placing the scene. total = now - t0.
      const timing = { t0, buildMs: d.build_ms, solveMs: d.solve_ms };
      // Motion mode: refresh the motion list + select via motion (reveals the timeline); otherwise
      // the assembly list + selectAssembly.
      if (viewMode === "motion") {
        refreshMotions();
        if (d.assembled) selectMotion(d.assembled, true, timing);  // verbose: a real (re)build
      } else {
        renderAssemblyList(d.assemblies || []);
        if (d.assembled) selectAssembly(d.assembled, true, timing);  // verbose: a real (re)compose
      }
      const issues = (d.issues || []).length;
      toast("assembled " + d.assembled + (issues ? ` (${issues} issue(s))` : ""));
    })
    .catch(e => toast(e.message, true))
    .finally(() => { spinner.style.display = "none"; });
}

function motionBuildSpec(spec) {
  if (!spec) { toast("select a motion spec first", true); return; }
  spinner.style.display = "block";
  const t0 = performance.now();
  fetch(apiUrl("/motion-build"), { method: "POST", headers: { "Content-Type": "application/json" },
                               body: JSON.stringify({ spec }) })
    .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "motion build failed"); return d; })
    .then(d => {
      motionSources[d.assembled] = spec;  // remember the motion doc for regenerate
      // Timing (build / solve / render): the server's motion build_ms + solve_ms (the OndselSolver
      // slice) + a render-done split, logged by loadAssembly, exactly as Assemblies do.
      const timing = { t0, buildMs: d.build_ms, solveMs: d.solve_ms };
      refreshMotions();
      if (d.assembled) selectMotion(d.assembled, true, timing);  // verbose: a real motion (re)build
      const issues = (d.issues || []).length;
      toast("motion built " + d.assembled + (issues ? ` (${issues} issue(s))` : ""));
    })
    .catch(e => toast(e.message, true))
    .finally(() => { spinner.style.display = "none"; });
}

function physicsBuildSpec(spec) {
  if (!spec) { toast("select a physics spec first", true); return; }
  spinner.style.display = "block";
  const t0 = performance.now();
  fetch(apiUrl("/physics-build"), { method: "POST", headers: { "Content-Type": "application/json" },
                               body: JSON.stringify({ spec }) })
    .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "physics build failed"); return d; })
    .then(d => {
      // Timing: the server's physics build_ms + a render-done split logged by loadAssembly, exactly
      // as Parts/Assemblies/Motion. No separate solve_ms (the joint sweeps are inside build_ms).
      const timing = { t0, buildMs: d.build_ms };
      refreshRobots();
      if (d.robot) selectRobot(d.robot, true, timing);   // verbose: a real physics (re)build
      const warns = (d.warnings || []).length;
      toast("physics built " + d.robot + (warns ? ` (${warns} warning(s))` : ""));
    })
    .catch(e => toast(e.message, true))
    .finally(() => { spinner.style.display = "none"; });
}

function regenerateAssembly(name) {
  const source = assemblySources[name];
  if (!source) { toast("no source recorded for " + name + "; pick it in the Spec box", true); return; }
  assembleSpec(source);
}

function removeAssembly(name) {
  // Delete the assembly scene sidecar (the composed part glbs are shared build output, left in
  // place). No confirmation: recomposing from the spec is cheap, and the toast reports it.
  fetch(apiUrl("/assembly/" + encodeURIComponent(name) + "/delete"), { method: "POST" })
    .then(r => r.json())
    .then(d => { if (activeModel === name) { activeModel = null; clearActive("assemblies"); clearModel(); } renderAssemblyList(d.assemblies || []); toast("deleted " + name); })
    .catch(() => toast("could not delete " + name, true));
}

// Persisted last-viewed model per mode: the boot logic restores it, falling back to the first
// available model when the saved one is gone, or to nothing when nothing was ever selected.
function savedActive(mode) { return localStorage.getItem("ncad.active." + mode); }
function clearActive(mode) { localStorage.removeItem("ncad.active." + mode); }

function loadAssembly(name, verbose, timing) {
  spinner.style.display = "flex";
  // NB: name the payload `sceneDoc`, NOT `scene` - `scene` is the global THREE.Scene, and
  // shadowing it here would make `scene.add(...)` add to the JSON instead of the 3D scene.
  fetch(apiUrl(`/assembly/${name}`)).then(r => r.json()).then(sceneDoc => {
    clearModel();
    // The scene sidecar records its source .asm.hocon, so Regenerate works after a reload
    // (the in-memory map alone would be empty on a fresh page).
    if (sceneDoc.source) assemblySources[name] = sceneDoc.source;
    for (const key in partGlbCache) delete partGlbCache[key];
    // The root carries NO rotation: each part clone is individually rotated to Z-up (exactly as
    // loadModel does to a single glb), and each placement is authored in that Z-up modeled frame,
    // so placement and geometry share one frame (no double rotation).
    const root = new THREE.Group();
    modelRoot = root;
    scene.add(root);
    const instanceMeshes = {};   // instanceId -> [meshes], for selection highlight/isolate
    const instanceNodes = {};    // instanceId -> placement node (Group), for motion playback
    // Plain re-select (mode switch / page refresh) logs NOTHING, mirroring how parts log nothing
    // on select. Only an explicit assemble (verbose) narrates instances + bbox.
    if (verbose) log(`assembly ${name}: ${(sceneDoc.instances || []).length} instances`);
    let pending = 0, done = false;
    const finish = () => {
      if (!(done && pending === 0)) return;
      root.updateMatrixWorld(true);
      // All instance meshes are loaded now (glb callbacks done): publish the per-instance mesh map
      // for selection highlight/isolate, and re-apply any active selection.
      instanceMeshMap = instanceMeshes;
      assemblyMaterials = {};
      for (const inst of sceneDoc.instances) {
        assemblyMaterials[inst.id] = {material: inst.material || null,
                                      appearance_color: inst.appearance_color || null,
                                      appearance: inst.appearance || null};
      }
      buildJointOverlay(sceneDoc, root, instanceNodes);
      updateByMaterialButton();  // show the By-Material control if this assembly has materials
      applyMode();   // assigns base materials, captures them, and re-applies selection visuals
      frameModel();
      setupMotion(name, instanceNodes);   // load + wire the motion timeline if a sidecar exists
      setupPhysics(name, instanceNodes);   // Physics mode: joint picker + robot inspector
      // Verbose bbox line only on an explicit assemble/first-load, not on every plain re-select
      // (switching Parts<->Assemblies just re-loads the existing scene; do not spam the log).
      if (verbose) {
        const box = new THREE.Box3().setFromObject(modelRoot);
        const sz = box.getSize(new THREE.Vector3());
        log(`assembly rendered: ${pickParts.length} meshes, bbox ${sz.x.toFixed(1)} x ${sz.y.toFixed(1)} x ${sz.z.toFixed(1)}`, "success");
      }
      document.getElementById("i-meshes").textContent = pickParts.length;
      spinner.style.display = "none";
      // Timing split, a profiling starting point. The server build_ms is the whole server pass;
      // solve_ms is the constraint/OndselSolver solve slice WITHIN it, so build-proper = build_ms -
      // solve_ms. render = total - build_ms (client wall-clock from the button click). When a solve
      // slice is present (assemblies + motion) it is broken out as a third term; a plain part (no
      // solve) keeps the two-term "build + render" line.
      if (timing && timing.buildMs != null) {
        const total = performance.now() - timing.t0;
        const render = Math.max(total - timing.buildMs, 0);
        const solve = timing.solveMs || 0;
        const line = solve > 0.05
          ? `build ${fmtDuration(Math.max(timing.buildMs - solve, 0))} + solve ${fmtDuration(solve)}`
            + ` + render ${fmtDuration(render)} = ${fmtDuration(total)}`
          : `build ${fmtDuration(timing.buildMs)} + render ${fmtDuration(render)} = ${fmtDuration(total)}`;
        toast(line);
        log(line, "info");
      }
    };
    for (const inst of sceneDoc.instances) {
      pending++;
      loadPartGlb(inst.part_glb, obj => {
        // Placement node (Z-up modeled frame) contains an inner group that rotates the raw glb
        // (Y-up) to Z-up, so: glb Y-up >> inner Rx(+90) >> Z-up >> node placement >> world.
        const node = new THREE.Group();
        node.applyMatrix4(matrixFromRowMajor(inst.placement));
        instanceNodes[inst.id] = node;
        const inner = new THREE.Group();
        inner.rotation.x = Math.PI / 2;
        inner.add(obj.clone(true));
        node.add(inner);
        // Pickup-point aid: an axes gizmo AT the instance origin (the point the placement moves),
        // so the author can see where a part is grabbed. Sized to the instance's own extent;
        // visibility follows the Origins toggle (assembly-only floating control).
        const partBox = new THREE.Box3().setFromObject(inner);
        const partSz = partBox.getSize(new THREE.Vector3());
        // Gizmo ~60% of the part's largest extent (min 1mm = 0.001 glb-units), so it reads as a
        // small origin marker, not a scene-spanning axis. No 1-unit floor (that was 1 METRE).
        const axisLen = Math.max(partSz.x, partSz.y, partSz.z, 0.001) * 0.6;
        const gizmo = new THREE.AxesHelper(axisLen);
        gizmo.visible = showOrigins;
        originGizmos.push(gizmo);
        node.add(gizmo);
        root.add(node);
        // Mate connector triads: each `inst.connectors` entry is a world-space frame (metres) in
        // the same Z-up modeled frame as the placement. A connector is FIXED to its part, so it must
        // ride the part under MOTION - parent it to the placement `node` in the node's LOCAL frame
        // (rest^-1 . worldFrame), NOT to `root` (which would freeze it at the rest pose while the
        // part animates - the "wire diagram at the origin that doesn't move" bug). At rest the node
        // matrix IS the placement, so node . (rest^-1 . basis) = basis; under motion it follows.
        const restInv = matrixFromRowMajor(inst.placement).clone().invert();
        for (const c of (inst.connectors || [])) {
          const triad = new THREE.AxesHelper(axisLen);
          const basis = new THREE.Matrix4().makeBasis(
            new THREE.Vector3(c.x[0], c.x[1], c.x[2]),
            new THREE.Vector3(c.y[0], c.y[1], c.y[2]),
            new THREE.Vector3(c.z[0], c.z[1], c.z[2]));
          basis.setPosition(c.origin[0], c.origin[1], c.origin[2]);
          triad.applyMatrix4(restInv.clone().multiply(basis));
          triad.visible = showConnectors;
          connectorGizmos.push(triad);
          node.add(triad);
        }
        node.updateMatrixWorld(true);
        node.traverse(o => {
          if (o.isMesh) {
            o.userData.instanceId = inst.id;   // tag for bidirectional pick <> tree selection
            pickParts.push(o);
            (instanceMeshes[inst.id] = instanceMeshes[inst.id] || []).push(o);
            // Per-part edge overlay (same as the single-part path): a line where adjacent facets
            // meet above 25deg. PARENT it to the mesh (o) rather than baking to world + adding to
            // scene, so under MOTION the edges move WITH the part (a scene-parented, world-baked
            // line would stay frozen at the rest pose while the mesh animates). The Edge toggle +
            // applyMode visibility still drive it via `edges[]`.
            const line = new THREE.LineSegments(
              new THREE.EdgesGeometry(o.geometry, 25),
              new THREE.LineBasicMaterial({ color: cssColor("--edge") }));
            line.visible = showEdges;
            o.add(line);
            edges.push(line);
          }
        });
        // Log the pickup point only when verbose (an explicit assemble), not on every re-select.
        if (verbose) {
          const p = inst.placement;
          log(`  ${inst.id} (${inst.part_name}): origin at [${p[3][0]}, ${p[3][1]}, ${p[3][2]}] m`);
        }
        pending--; finish();
      }, () => { pending--; toast("part glb failed: " + inst.part_glb, true); finish(); });
    }
    done = true; finish();
    renderInstanceTree(sceneDoc);
    renderAssemblyBom(sceneDoc);
    logInterference(sceneDoc, verbose);
  }).catch(err => {
    spinner.style.display = "none";
    toast("assembly load error: " + (err && err.message ? err.message : err), true);
    console.error(err);
  });
}

function loadPartGlb(glbName, cb, onErr) {
  if (partGlbCache[glbName]) { cb(partGlbCache[glbName]); return; }
  loader.load(modelUrl(glbName), gltf => { partGlbCache[glbName] = gltf.scene; cb(gltf.scene); },
    undefined, err => { console.error("part glb failed", glbName, err); if (onErr) onErr(err); });
}

// ---- Motion timeline playback (bucket 6.0) ----
// The motion sidecar <name>.motion.json holds per-frame per-instance placements (same row-major
// metres 4x4 as the static sidecar). We swap each instance node's matrix to the current frame and
// advance in the animate() loop. Frame 0 is the rest pose, so a motion-less assembly is unchanged
// and the bar stays hidden.
const motionBar = document.getElementById("motion-bar");
const motionPlayBtn = document.getElementById("motion-play");
const motionScrub = document.getElementById("motion-scrub");
const motionReadout = document.getElementById("motion-readout");
const PLAY_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
const PAUSE_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';
let motion = null;         // {frames, driver} or null when no motion
let motionNodes = {};      // instanceId -> node for the active motion
let motionFrame = 0;       // current frame index
let motionPlaying = false;
let motionAccum = 0;       // ms accumulated toward the next frame
// Loop mode: "loop" restarts at frame 0 each cycle (the default); "bounce" ping-pongs forward then
// reverse, so a one-way stroke (a rack sliding, a follower rising) reads as a seamless there-and-
// back loop in the recorded video. `motionDir` is the current step direction under bounce.
let motionLoopMode = localStorage.getItem("ncad.motionLoop") || "loop";
let motionDir = 1;
// PLAYBACK RATE only (how fast you watch the same trajectory); it never re-solves. Solve resolution
// is the motion document's driver `steps` (or `fps`+`duration`). 1x = 30 fps (a 1/30 s frame
// interval); the ladder multiplies that rate. Beyond ~2x the ~60 fps render loop advances several
// frames per tick (advanceMotion's while-loop handles it), so the high multipliers act as fast
// preview/scrub. The [-]/[+] buttons + the "[" / "]" keys step along the ladder; choice persists.
const MOTION_BASE_FRAME_MS = 1000 / 30;   // 1x = 30 fps
const MOTION_SPEEDS = [0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128];
const motionSlowerBtn = document.getElementById("motion-slower");
const motionFasterBtn = document.getElementById("motion-faster");
const motionSpeedReadout = document.getElementById("motion-speed-readout");
let motionSpeedIdx = (() => {
  const saved = parseFloat(localStorage.getItem("ncad.motionSpeed"));
  const i = MOTION_SPEEDS.indexOf(saved);
  return i >= 0 ? i : MOTION_SPEEDS.indexOf(1);   // default 1x
})();
function motionSpeed() { return MOTION_SPEEDS[motionSpeedIdx]; }
function motionFrameMs() { return MOTION_BASE_FRAME_MS / motionSpeed(); }
function renderMotionSpeed() {
  // Only the middle readout shows the number (<n>x); the -/+ buttons stay iconic.
  motionSpeedReadout.textContent = fmtSpeed(motionSpeed());
  motionSlowerBtn.disabled = motionSpeedIdx === 0;
  motionFasterBtn.disabled = motionSpeedIdx === MOTION_SPEEDS.length - 1;
}
function setMotionSpeedIdx(i) {
  motionSpeedIdx = Math.max(0, Math.min(MOTION_SPEEDS.length - 1, i));
  localStorage.setItem("ncad.motionSpeed", String(motionSpeed()));
  renderMotionSpeed();
}
motionSlowerBtn.addEventListener("click", () => setMotionSpeedIdx(motionSpeedIdx - 1));
motionFasterBtn.addEventListener("click", () => setMotionSpeedIdx(motionSpeedIdx + 1));
renderMotionSpeed();

// Loop-mode toggle (loop <-> bounce). Bounce plays forward then reverse for a seamless video loop.
const motionLoopBtn = document.getElementById("motion-loop");
const LOOP_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46A7.93 7.93 0 0 0 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74A7.93 7.93 0 0 0 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg>';
const BOUNCE_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M8 7l-5 5 5 5v-3h8v3l5-5-5-5v3H8z"/></svg>';
function renderLoopMode() {
  motionLoopBtn.innerHTML = motionLoopMode === "bounce" ? BOUNCE_ICON : LOOP_ICON;
  motionLoopBtn.classList.toggle("active", motionLoopMode === "bounce");
  motionLoopBtn.title = motionLoopMode === "bounce"
    ? "Bounce: forward then reverse ( L )" : "Loop: restart each cycle ( L )";
}
function toggleLoopMode() {
  motionLoopMode = motionLoopMode === "bounce" ? "loop" : "bounce";
  motionDir = 1;   // restart the direction so a fresh bounce goes forward first
  localStorage.setItem("ncad.motionLoop", motionLoopMode);
  renderLoopMode();
}
motionLoopBtn.addEventListener("click", toggleLoopMode);
renderLoopMode();
// "[" slower, "]" faster - only when a motion is loaded and the user is not typing in a field.
document.addEventListener("keydown", ev => {
  if (motionBar.hidden) return;
  const t = ev.target;
  if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT")) return;
  if (ev.key === "[") { setMotionSpeedIdx(motionSpeedIdx - 1); ev.preventDefault(); }
  else if (ev.key === "]") { setMotionSpeedIdx(motionSpeedIdx + 1); ev.preventDefault(); }
  // P (and the space bar, the media convention) toggles play/pause, matching the widget's button.
  else if (ev.key === "p" || ev.key === "P" || ev.key === " ") {
    toggleMotionPlay(); ev.preventDefault();
  }
  // L toggles the loop mode (loop <-> bounce).
  else if (ev.key === "l" || ev.key === "L") { toggleLoopMode(); ev.preventDefault(); }
  // 0 rewinds to the start frame and pauses (a clean reset before recording a fresh loop).
  else if (ev.key === "0") {
    motionPlaying = false; motionPlayBtn.innerHTML = PLAY_ICON;
    motionDir = 1; motionAccum = 0; showMotionFrame(0);
    ev.preventDefault();
  }
});

function resetMotion() {
  motion = null; motionNodes = {}; motionFrame = 0; motionPlaying = false; motionAccum = 0;
  motionBar.hidden = true;
  motionPlayBtn.innerHTML = PLAY_ICON;
  // Trace lines are children of modelRoot (cleared with the scene in clearModel); just drop refs.
  traceLines = [];
  renderMeasures(null);
  renderClashMarks([], 0);
  // Physics rides the motion state; drop the joint picker + Robot inspector with the scene too.
  const pbar = document.getElementById("physics-bar");
  if (pbar) pbar.hidden = true;
  if (typeof renderRobotTree === "function") renderRobotTree(null);
}

function renderClashMarks(events, frameCount) {
  // Red ticks on the scrubber at interfering frame indices (motion-time interference, 6.3).
  const host = document.getElementById("motion-clash-marks");
  if (!host) return;
  host.innerHTML = "";
  if (!events.length || frameCount < 2) return;
  const seen = new Set();
  for (const ev of events) {
    if (seen.has(ev.frame)) continue;
    seen.add(ev.frame);
    const tick = document.createElement("div");
    tick.className = "clash-tick";
    tick.style.left = (100 * ev.frame / (frameCount - 1)) + "%";
    tick.title = `clash: ${ev.a} <> ${ev.b} (frame ${ev.frame})`;
    host.appendChild(tick);
  }
  log(`motion interference: ${seen.size} frame(s) with contact`, "warn");
}

function setupMotion(name, instanceNodes) {
  resetMotion();
  // The timeline is a Motion-mode feature; in Assemblies mode a driven assembly still loads, just
  // without playback (that is what the Motion tab is for).
  if (viewMode !== "motion") return;
  fetch(apiUrl(`/motion/${encodeURIComponent(name)}`)).then(r => {
    if (!r.ok) return null;   // 404: this assembly has no motion, leave the bar hidden
    return r.json();
  }).then(doc => {
    if (!doc || !(doc.frames || []).length) return;
    // The trajectory records its source .motion.hocon, so Regenerate works after a page reload (the
    // in-memory motionSources map alone would be empty on a fresh page).
    if (doc.source) motionSources[name] = doc.source;
    motion = doc; motionNodes = instanceNodes;
    motionScrub.max = String(doc.frames.length - 1);
    motionScrub.value = "0";
    motionBar.hidden = false;
    buildTraceLines(doc.traces || []);   // motion outputs (bucket 6.1); no-op if none declared
    renderMeasures(doc.measures || []);
    renderMobility(doc.dof || null);
    renderClashMarks(doc.interference || [], doc.frames.length);   // motion-time interference (6.3)
    showMotionFrame(0);
    log(`motion: ${doc.frames.length} frames, driver ${doc.driver ? doc.driver.joint : "?"}`, "info");
  }).catch(() => { /* motion is optional; a fetch error just means no timeline */ });
}

// ---- Physics (robotics) mode ----
// Physics mode reuses the assembly scene + the motion playback path: the robot's per-actuated-joint
// sweep has the same {frames:[{driver_value, placements:{id:4x4}}]} shape as a motion trajectory, so
// selecting a joint just loads its sweep into the motion state and the scrubber/play controls drive
// it unchanged. One joint at a time (the precomputed-sweep tradeoff). The physics-bar joint picker
// and the Robot inspector tab are the only physics-specific UI.
const physicsBar = document.getElementById("physics-bar");
const physicsJointSelect = document.getElementById("physics-joint");
let physicsSweeps = {};    // {jointName: {from, to, frames}} for the active robot
let physicsNodes = {};     // instanceId -> node for the active robot (same shape as motionNodes)

function setupPhysics(name, instanceNodes) {
  resetMotion();
  physicsBar.hidden = true;
  physicsSweeps = {};
  if (viewMode !== "physics") return;
  // The tree (.robot.json) drives the Robot inspector; the sweeps (.robot_sweeps.json) drive the
  // joint sliders. Both are optional (sweeps only exist when `ncad physics --sweeps` was run).
  fetch(apiUrl(`/robot/${encodeURIComponent(name)}`)).then(r => r.ok ? r.json() : null)
    .then(tree => {
      renderRobotTree(tree);
      return fetch(apiUrl(`/robot-sweeps/${encodeURIComponent(name)}`)).then(r => r.ok ? r.json() : {});
    })
    .then(sweeps => {
      physicsSweeps = sweeps || {};
      physicsNodes = instanceNodes;
      populateJointSelect();
    })
    .catch(() => { /* physics sidecars are optional */ });
}

function populateJointSelect() {
  const joints = Object.keys(physicsSweeps);
  physicsJointSelect.innerHTML = "";
  if (!joints.length) {
    // No sweeps: the robot is inspectable (tree tab) but not articulable. Say so in the log.
    log("physics: no joint sweeps (run `ncad physics --sweeps` to enable sliders)", "info");
    return;
  }
  for (const j of joints) {
    const opt = document.createElement("option");
    opt.value = j; opt.textContent = j;
    physicsJointSelect.appendChild(opt);
  }
  physicsBar.hidden = false;
  loadJointSweep(joints[0]);
}

function loadJointSweep(jointName) {
  const sweep = physicsSweeps[jointName];
  if (!sweep || !(sweep.frames || []).length) return;
  // Feed the joint sweep into the shared motion-playback state; the scrubber/play controls + the
  // showMotionFrame apply path are then identical to Motion mode.
  motion = {frames: sweep.frames, driver: {joint: jointName}};
  motionNodes = physicsNodes;
  motionScrub.max = String(sweep.frames.length - 1);
  motionScrub.value = "0";
  motionBar.hidden = false;
  showMotionFrame(0);
  log(`physics: joint ${jointName}, ${sweep.frames.length} frames`, "info");
}

physicsJointSelect.addEventListener("change", () => loadJointSweep(physicsJointSelect.value));

// The Robot inspector tab: the kinematic tree (base -> links) + per-link computed mass/inertia and
// per-joint type/limits from .robot.json. Read-only; surfaces the computed inertia visually.
function renderRobotTree(tree) {
  const robotBtn = document.getElementById("tab-robot-btn");
  const body = document.getElementById("robot-body");
  if (!tree || !(tree.links || []).length) {
    robotBtn.hidden = true;
    body.innerHTML = '<div class="panel-empty">no robot</div>';
    return;
  }
  robotBtn.hidden = false;
  const rows = [];
  rows.push(`<div class="robot-section">base: <b>${escapeHtml(tree.base_link || "?")}</b></div>`);
  rows.push('<div class="robot-section">links</div>');
  for (const link of tree.links) {
    const i = link.inertia || {};
    const diag = ["ixx", "iyy", "izz"].map(k => (+(i[k] || 0)).toExponential(2)).join(", ");
    rows.push(`<div class="robot-row"><span class="robot-name">${escapeHtml(link.name)}</span>` +
      `<span class="robot-meta">${(+link.mass).toFixed(3)} kg &middot; I[${diag}]</span></div>`);
  }
  rows.push('<div class="robot-section">joints</div>');
  for (const j of tree.joints || []) {
    const lim = (j.limit && j.limit[0] != null && j.limit[1] != null)
      ? ` [${(+j.limit[0]).toFixed(2)}, ${(+j.limit[1]).toFixed(2)}]` : "";
    const tags = [j.actuated ? "actuated" : "", j.loop_closure ? "loop" : ""].filter(Boolean).join(", ");
    rows.push(`<div class="robot-row"><span class="robot-name">${escapeHtml(j.name)}</span>` +
      `<span class="robot-meta">${escapeHtml(j.type)}${lim}${tags ? " &middot; " + tags : ""}</span>` +
      `<span class="robot-chain">${escapeHtml(j.parent)} &rarr; ${escapeHtml(j.child)}</span></div>`);
  }
  body.innerHTML = rows.join("");
}

// ---- Export control (context-sensitive download) ----
// Each tab offers the formats its document kind can produce; picking one re-exports via ncad on the
// server (from the recorded source, so B-rep/robot formats stay faithful) and downloads the file.
const EXPORT_FORMATS = {
  parts: ["glb", "step", "iges", "stl", "3mf", "obj", "ply"],
  assemblies: ["step", "glb", "stl"],
  motion: ["step", "glb", "stl"],
  physics: ["urdf", "mjcf", "sdf"],
};
const _MODE_KIND = { parts: "part", assemblies: "assembly", motion: "motion", physics: "physics" };
const exportControl = document.getElementById("export-control");
const exportBtn = document.getElementById("export-btn");
const exportMenu = document.getElementById("export-menu");

function syncExportControl() {
  // The control shows in any mode that has export formats; it is DISABLED (greyed) until a model is
  // selected, so the affordance stays discoverable but does nothing without a source to export.
  const formats = EXPORT_FORMATS[viewMode] || [];
  exportControl.hidden = !formats.length;
  exportBtn.disabled = !activeModel;
  exportBtn.title = activeModel ? "Export the model" : "Select a model to export";
  exportMenu.hidden = true;
}

function toggleExportMenu() {
  if (!activeModel) return;   // disabled: nothing selected to export
  if (!exportMenu.hidden) { exportMenu.hidden = true; return; }
  const formats = EXPORT_FORMATS[viewMode] || [];
  exportMenu.innerHTML = "";
  for (const fmt of formats) {
    const item = document.createElement("button");
    item.type = "button"; item.setAttribute("role", "menuitem");
    item.textContent = fmt.toUpperCase();
    item.addEventListener("click", () => { exportMenu.hidden = true; exportModel(fmt); });
    exportMenu.appendChild(item);
  }
  exportMenu.hidden = false;
}

function exportModel(fmt) {
  if (!activeModel) { toast("no model to export", true); return; }
  const kind = _MODE_KIND[viewMode] || "part";
  spinner.style.display = "block";
  fetch(apiUrl("/export"), { method: "POST", headers: { "Content-Type": "application/json" },
                             body: JSON.stringify({ name: activeModel, kind, format: fmt }) })
    .then(async r => {
      if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.error || "export failed"); }
      const disposition = r.headers.get("Content-Disposition") || "";
      const match = /filename="([^"]+)"/.exec(disposition);
      const filename = match ? match[1] : `${activeModel}.${fmt}`;
      return r.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
      // Trigger a browser download to the default location (no out/ write on the server).
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = filename; document.body.appendChild(a); a.click();
      document.body.removeChild(a); URL.revokeObjectURL(url);
      log(`exported ${activeModel} to ${filename}`, "info");
    })
    .catch(e => toast(e.message, true))
    .finally(() => { spinner.style.display = "none"; });
}

exportBtn.addEventListener("click", ev => { ev.stopPropagation(); toggleExportMenu(); });
// Click anywhere else closes the menu.
document.addEventListener("click", () => { exportMenu.hidden = true; });

function showMotionFrame(i) {
  if (!motion) return;
  const frames = motion.frames;
  motionFrame = ((i % frames.length) + frames.length) % frames.length;
  const frame = frames[motionFrame];
  for (const id in frame.placements) {
    const node = motionNodes[id];
    if (!node) continue;
    node.matrix.copy(matrixFromRowMajor(frame.placements[id]));
    node.matrix.decompose(node.position, node.quaternion, node.scale);
    node.updateMatrixWorld(true);
  }
  motionScrub.value = String(motionFrame);
  const unit = degreesLikelyDriver() ? "°" : "";
  motionReadout.textContent = `${(+frame.driver_value).toFixed(1)}${unit}`;
  updateMeasureValues(motionFrame);
}

// Build a THREE.Line for each declared trace polyline (world metres), added to modelRoot so it
// clears with the scene and rides the model's framing shift. Colored from the trace palette,
// visibility follows the Traces toggle. No-op when no traces are declared.
function buildTraceLines(traces) {
  traceLines = [];
  traces.forEach((t, i) => {
    const pts = (t.polyline || []).map(p => new THREE.Vector3(p[0], p[1], p[2]));
    if (pts.length < 2) return;
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color: TRACE_COLORS[i % TRACE_COLORS.length] }));
    line.userData.isGizmo = true;   // excluded from picking/bbox like the other overlays
    line.visible = showTraces;
    if (modelRoot) modelRoot.add(line);
    traceLines.push(line);
  });
}

// Render the measures panel (a compact numeric readout, one row per measure). Called on load
// (measures list) and reset (null clears it). The per-frame live value is filled by
// updateMeasureValues.
function renderMeasures(measures) {
  const panel = document.getElementById("measures-body");
  if (!panel) return;
  if (!measures || !measures.length) {
    panel.innerHTML = '<div class="panel-empty">no measures</div>';
    document.getElementById("tab-measures-btn").hidden = !measures;
    return;
  }
  document.getElementById("tab-measures-btn").hidden = false;
  panel.innerHTML = "";
  for (const m of measures) {
    const row = document.createElement("div");
    row.className = "measure-row";
    const extra = m.value != null ? ` &middot; total ${(+m.value).toFixed(2)} ${m.unit}` : "";
    row.innerHTML =
      `<span class="measure-id">${m.id}</span>` +
      `<span class="measure-val" data-measure="${m.id}">-</span>` +
      `<span class="measure-range">[${(+m.min).toFixed(1)} .. ${(+m.max).toFixed(1)}] ${m.unit}${extra}</span>`;
    panel.appendChild(row);
  }
}

// Add a mobility (DoF) line to the hierarchy panel, next to the static solve-status line: the
// planar Gruebler mobility + the rest-pose solver DoF. Green when mobile, amber when locked.
// Prepended to the hierarchy body (which renderInstanceTree filled from the assembly scene).
function renderMobility(dof) {
  const existing = document.getElementById("mobility-line");
  if (existing) existing.remove();
  if (!dof) return;
  const body = document.getElementById("hierarchy-body");
  if (!body) return;
  const line = document.createElement("div");
  line.id = "mobility-line";
  line.className = "mate-status " + (dof.status === "mobile" ? "mate-status-ok" : "mate-status-warn");
  line.textContent = `mobility: ${dof.gruebler} DoF (planar Gruebler ${dof.gruebler}, ` +
    `rest solve ${dof.solver})`;
  line.title = "Mechanism mobility from the joint graph (Gruebler) next to the static rest-pose " +
    "free DoF (0 for a well-constrained rest).";
  body.insertBefore(line, body.firstChild);
}

// Fill each measure row's live value from the current frame's series entry.
function updateMeasureValues(frameIdx) {
  if (!motion || !motion.measures) return;
  for (const m of motion.measures) {
    const el = document.querySelector(`.measure-val[data-measure="${m.id}"]`);
    if (!el) continue;
    const v = (m.series || [])[frameIdx];
    el.textContent = v == null ? "-" : `${(+v).toFixed(2)} ${m.unit}`;
  }
}

function degreesLikelyDriver() {
  // A rotation driver reads in degrees; a slider in mm. We do not carry the joint type in the
  // sidecar, so infer: a range that spans a full turn (>= 360 total) is almost certainly degrees.
  if (!motion || !motion.frames.length) return true;
  const span = Math.abs(motion.frames[motion.frames.length - 1].driver_value
                        - motion.frames[0].driver_value);
  return span >= 180;
}

function toggleMotionPlay() {
  if (!motion) return;
  motionPlaying = !motionPlaying;
  motionPlayBtn.innerHTML = motionPlaying ? PAUSE_ICON : PLAY_ICON;
}

function advanceMotion(dtMs) {
  if (!motionPlaying || !motion) return;
  motionAccum += dtMs;
  const frameMs = motionFrameMs();
  while (motionAccum >= frameMs) {
    motionAccum -= frameMs;
    stepMotion();
  }
}

function stepMotion() {
  // Loop mode wraps forward (modulo). Bounce mode ping-pongs: step by motionDir and flip direction
  // at either end so the trajectory plays forward then reverse (a there-and-back loop for video).
  const last = motion.frames.length - 1;
  if (motionLoopMode !== "bounce") { showMotionFrame(motionFrame + 1); return; }
  let next = motionFrame + motionDir;
  if (next > last) { motionDir = -1; next = last - 1; }
  else if (next < 0) { motionDir = 1; next = 1; }
  if (next < 0) next = 0;   // a single-frame trajectory stays put
  showMotionFrame(next);
}

motionPlayBtn.addEventListener("click", toggleMotionPlay);
motionScrub.addEventListener("input", () => {
  motionPlaying = false; motionPlayBtn.innerHTML = PLAY_ICON;
  showMotionFrame(parseInt(motionScrub.value, 10) || 0);
});

// Build the 3D joint-freedom overlay (bucket 5.5): a signature-keyed glyph at each joint's side-A
// connector world frame, plus a dashed line between each coupling's two joints. Each glyph is
// PARENTED to its side-A instance node (in the node's local frame), so under MOTION it rides the
// moving part instead of freezing at the rest pose. The coupling links stay on `root` (they span
// two joints). All are pushed to `jointGizmos` for the Joints toggle and clear with the scene.
function buildJointOverlay(sceneDoc, root, instanceNodes) {
  const frameOf = {};   // instanceId -> { connectorId -> {origin,x,y,z} }
  const restInvOf = {}; // instanceId -> rest placement inverse (world -> node-local)
  for (const inst of (sceneDoc.instances || [])) {
    frameOf[inst.id] = {};
    for (const c of (inst.connectors || [])) frameOf[inst.id][c.id] = c;
    restInvOf[inst.id] = matrixFromRowMajor(inst.placement).clone().invert();
  }
  // One glyph size for the whole assembly, from the scene bbox (computed once here).
  const box = new THREE.Box3().setFromObject(root);
  const sz = box.getSize(new THREE.Vector3());
  const jointSize = Math.max(sz.x, sz.y, sz.z, 0.001) * 0.08;
  const jointAnchor = {};   // jointId -> THREE.Vector3 (its glyph origin), for coupling links
  for (const j of (sceneDoc.joints || [])) {
    const a = (j.between || [])[0];
    const frame = a && frameOf[a.instance] ? frameOf[a.instance][a.connector] : null;
    if (!frame) continue;  // unresolved connector: skip gracefully
    const glyph = buildJointGlyph(j, frame, jointSize);
    glyph.visible = showJoints;
    jointGizmos.push(glyph);
    // Parent to side-A's node in its local frame (rest^-1 . glyph) so it follows the part; fall
    // back to `root` if the node is missing (an unresolved instance).
    const node = a && instanceNodes ? instanceNodes[a.instance] : null;
    if (node && restInvOf[a.instance]) {
      glyph.applyMatrix4(restInvOf[a.instance]);
      node.add(glyph);
    } else {
      root.add(glyph);
    }
    jointAnchor[j.id] = new THREE.Vector3(frame.origin[0], frame.origin[1], frame.origin[2]);
  }
  for (const c of (sceneDoc.couplings || [])) {
    const pts = (c.between || []).map(jid => jointAnchor[jid]).filter(Boolean);
    if (pts.length !== 2) continue;
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineDashedMaterial({ color: 0xaaaaaa, dashSize: jointSize * 0.3, gapSize: jointSize * 0.3 }));
    line.computeLineDistances();
    line.userData.isGizmo = true;
    line.visible = showJoints;
    jointGizmos.push(line);
    root.add(line);
  }
}

function renderInstanceTree(sceneDoc) {
  const body = document.getElementById("hierarchy-body");
  if (!body) return;
  body.innerHTML = "";
  const instances = sceneDoc.instances || [];
  const mates = sceneDoc.mates || [];
  const joints = sceneDoc.joints || [];
  const couplings = sceneDoc.couplings || [];
  // A coupling references joint ids; each joint references instances via its `between`. Map joint id
  // -> its instances so a coupling chip can show under any instance in either coupled joint.
  const jointInstances = {};
  for (const j of joints) jointInstances[j.id] = (j.between || []).map(b => b.instance);
  // Instances in an `interfering` pair get a red CLASH badge (bucket 5.6).
  const clashing = new Set();
  for (const f of (sceneDoc.interference || [])) {
    if (f.status === "interfering") { clashing.add(f.a); clashing.add(f.b); }
  }
  const solve = sceneDoc.solve || null;
  // Solved-status line (bucket 5.3): four states - green well-constrained, red over-constrained
  // (failing ids), amber redundant (removable ids) / under-constrained (free DoF). The DoF
  // accounting explanation is the tooltip. Only shown when the assembly carries a solve block.
  if (solve) {
    const line = document.createElement("div");
    const cls = solve.status === "well_constrained" ? "mate-status-ok"
      : solve.status === "over_constrained" ? "mate-status-bad" : "mate-status-warn";
    line.className = "mate-status " + cls;
    let text;
    if (solve.status === "over_constrained") {
      text = `over-constrained: [${(solve.failing_ids || []).join(", ")}]`;
    } else if (solve.status === "redundant") {
      text = `redundant: [${(solve.redundant_ids || []).join(", ")}]`;
    } else {
      text = `${solve.status.replace("_", "-")} - ${solve.dof} free DoF`;
    }
    line.textContent = text;
    if (solve.explanation) line.title = solve.explanation;
    body.appendChild(line);
  }
  // An instance is "floating" only if NO mate AND NO joint references it (a joint-only instance is
  // still connected, not floating).
  const inRelation = id => mates.some(m => (m.between || []).some(b => b.instance === id))
    || joints.some(j => (j.between || []).some(b => b.instance === id));
  const firstId = instances.length ? instances[0].id : null;
  for (const inst of instances) {
    const row = document.createElement("div");
    row.className = "tree-row";
    row.textContent = `${inst.id}  (${inst.part_name})`;
    // Click a row to select+highlight that instance in 3D (bidirectional with the 3D pick).
    row.dataset.instance = inst.id;
    row.style.cursor = "pointer";
    row.addEventListener("click", () => selectInstance(inst.id));
    // GROUND badge for the anchor (first instance or lock:true); floating if no mate or joint.
    if (inst.id === firstId || inst.lock) {
      const badge = document.createElement("span");
      badge.className = "tree-badge"; badge.textContent = "GROUND";
      row.appendChild(badge);
    } else if (!inRelation(inst.id)) {
      const badge = document.createElement("span");
      badge.className = "tree-badge"; badge.textContent = "floating";
      row.appendChild(badge);
    }
    if (clashing.has(inst.id)) {
      const badge = document.createElement("span");
      badge.className = "tree-badge tree-badge-bad"; badge.textContent = "CLASH";
      row.appendChild(badge);
    }
    body.appendChild(row);
    // One chip per mate this instance participates in: "type -- other.connector [id]".
    for (const m of mates) {
      const sides = m.between || [];
      const mine = sides.findIndex(b => b.instance === inst.id);
      if (mine < 0) continue;
      const other = sides[mine === 0 ? 1 : 0];
      const chip = document.createElement("div");
      const roleCls = m.role === "failing" ? " mate-chip-bad"
        : m.role === "redundant" ? " mate-chip-redundant" : "";
      chip.className = "mate-chip" + roleCls;
      const otherLabel = other ? `${other.instance}.${other.connector}` : "(self)";
      chip.textContent = `${m.type} -- ${otherLabel} [${m.id}]`;
      if (m.role === "failing") chip.title = "over-constrained / failing mate";
      else if (m.role === "redundant") chip.title = "redundant - removable without changing the result";
      // Click a mate chip to highlight the two instances it connects.
      chip.style.cursor = "pointer";
      chip.addEventListener("click", ev => {
        ev.stopPropagation();
        selectInstances((m.between || []).map(b => b.instance));
      });
      body.appendChild(chip);
    }
    // One joint chip per joint this instance participates in (bucket 5.4a): distinct accent, shows
    // the joint type + its DoF signature (the free motion it leaves) + the static value if set.
    for (const j of joints) {
      const sides = j.between || [];
      const mine = sides.findIndex(b => b.instance === inst.id);
      if (mine < 0) continue;
      const other = sides[mine === 0 ? 1 : 0];
      const chip = document.createElement("div");
      const roleCls = j.role === "failing" ? " mate-chip-bad"
        : j.role === "redundant" ? " mate-chip-redundant" : "";
      chip.className = "joint-chip" + roleCls;
      const sig = (j.signature || []).map(a => {
        const m = a.motion === "rotation" ? "rot" : a.motion === "translation" ? "trans" : "screw";
        return a.pitch != null ? `${m} ${a.axis} p${a.pitch}` : `${m} ${a.axis}`;
      }).join(", ");
      const otherLabel = other ? `${other.instance}.${other.connector}` : "(self)";
      const val = (j.value !== null && j.value !== undefined) ? ` = ${j.value}` : "";
      chip.textContent = `${j.type}${sig ? " [" + sig + "]" : ""} -- ${otherLabel} [${j.id}]${val}`;
      // Click a joint chip to highlight the two instances it joins.
      chip.style.cursor = "pointer";
      chip.addEventListener("click", ev => {
        ev.stopPropagation();
        selectInstances((j.between || []).map(b => b.instance));
      });
      body.appendChild(chip);
    }
    // Coupling chips (bucket 5.4b): a declared joint-to-joint relation (gear/belt/...), dashed +
    // muted to read as "enforced in motion (Phase 6)". Shown under any instance in either coupled joint.
    for (const c of couplings) {
      const involves = (c.between || []).some(jid => (jointInstances[jid] || []).includes(inst.id));
      if (!involves) continue;
      const chip = document.createElement("div");
      chip.className = "coupling-chip";
      const ratio = (c.ratio != null) ? ` x${c.ratio}` : "";
      const others = (c.between || []).join(" <> ");
      chip.textContent = `${c.type}${ratio} -- ${others} [${c.id}]`;
      chip.title = "enforced during motion (Phase 6)";
      // Click a coupling chip to highlight the instances of both coupled joints.
      chip.style.cursor = "pointer";
      chip.addEventListener("click", ev => {
        ev.stopPropagation();
        const ids = [];
        for (const jid of (c.between || [])) ids.push(...(jointInstances[jid] || []));
        selectInstances(ids);
      });
      body.appendChild(chip);
    }
  }
}

// Assembly BOM + roll-up mass in the BOM panel (bucket 5.6): part-grouped line items (part | qty |
// material | total mass) + a roll-up total mass + COG. Parts-mode per-part BOM is unaffected.
function renderAssemblyBom(sceneDoc) {
  const body = document.getElementById("bom-body");
  if (!body) return;
  const bom = sceneDoc.bom, mass = sceneDoc.mass;
  if (!bom || !(bom.items || []).length) {
    body.innerHTML = '<div class="panel-empty">no BOM for this assembly</div>';
    return;
  }
  body.innerHTML = "";
  for (const it of bom.items) {
    const row = document.createElement("div"); row.className = "bom-row";
    const massTxt = it.total_mass != null ? `${it.total_mass.toFixed(4)} kg` : "-";
    row.innerHTML = `<span class="k">${it.part} x${it.quantity}` +
      `${it.material ? " (" + it.material + ")" : ""}</span>` +
      `<span class="v">${massTxt}</span>`;
    body.appendChild(row);
  }
  if (mass) {
    const row = document.createElement("div"); row.className = "bom-row";
    row.innerHTML = `<span class="k">total</span>` +
      `<span class="v">${(mass.total_mass || 0).toFixed(4)}<span class="u">kg</span></span>`;
    body.appendChild(row);
  }
}

// Log interference findings (bucket 5.6): interfering pairs as errors (with volume), clearances as
// info. Touching pairs (expected mates) are only logged when verbose, to avoid noise.
function logInterference(sceneDoc, verbose) {
  for (const f of (sceneDoc.interference || [])) {
    if (f.status === "interfering") {
      log(`interference ${f.a} <> ${f.b}: vol ${f.volume} mm3`, "error");
    } else if (f.status === "clearance" && verbose) {
      log(`clearance ${f.a} <> ${f.b}: ${f.distance} mm`, "info");
    }
  }
}

function setViewMode(next) {
  viewMode = next;
  localStorage.setItem("ncad.viewMode", next);
  document.getElementById("mode-parts").classList.toggle("active", next === "parts");
  document.getElementById("mode-assemblies").classList.toggle("active", next === "assemblies");
  document.getElementById("mode-motion").classList.toggle("active", next === "motion");
  document.getElementById("mode-physics").classList.toggle("active", next === "physics");
  // The physics joint picker belongs to Physics mode only; leaving physics hides it.
  if (next !== "physics") document.getElementById("physics-bar").hidden = true;
  syncAssemblyControls();
  // Switching mode must NOT open the spec dropdown (renderSpecTree un-hides it); clear the
  // search and keep the tree hidden. It re-renders (mode-filtered) on the input's focus/input.
  const search = document.getElementById("spec-search");
  search.value = "";
  syncSpecClear();
  document.getElementById("spec-tree").hidden = true;
  activeModel = null;
  syncExportControl();   // show the export control for this mode, disabled until a model selects
  // Switching mode restores that mode's saved last-viewed model (falling back to the first
  // available), matching the page-refresh behavior.
  if (next === "assemblies") {
    refreshAssemblies().then(names => {
      if (!names || !names.length) return;
      selectAssembly(bootModel(names, "assemblies", null) || names[0]);
    });
  } else if (next === "motion") {
    // Motion mode lists only assemblies that have a motion trajectory sidecar; selecting one loads
    // that assembly (its parts) and reveals the timeline (the timeline shows only in Motion mode).
    refreshMotions().then(names => {
      if (!names || !names.length) return;
      selectMotion(bootModel(names, "motion", null) || names[0]);
    });
  } else if (next === "physics") {
    // Physics mode lists robots (assemblies with a .robot.json); selecting one loads the scene, the
    // joint picker, and the Robot inspector.
    refreshRobots().then(names => {
      if (!names || !names.length) return;
      selectRobot(bootModel(names, "physics", null) || names[0]);
    });
  } else {
    refreshModels().then(models => {
      if (!models || !models.length) return;
      const names = models.map(m => m.name);
      selectModel(bootModel(names, "parts", null) || names[0]);
    });
  }
}

function build(spec) {
  if (!spec) { toast("select a spec first", true); return; }
  spinner.style.display = "block";
  const t0 = performance.now();
  fetch(apiUrl("/build"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ spec }) })
    .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "build failed"); return d; })
    .then(d => {
      renderModelList(d.models); const first = (d.built || [])[0]; if (first) selectModel(first);
      // Timing split (build vs render): server build_ms + client render (total - build) + total.
      const total = performance.now() - t0;
      if (d.build_ms != null) {
        const render = Math.max(total - d.build_ms, 0);
        const line = `build ${fmtDuration(d.build_ms)} + render ${fmtDuration(render)} = ${fmtDuration(total)}`;
        toast("built " + (d.built || []).join(", ") + " - " + line);
        log(line, "info");
      } else {
        toast("built " + (d.built || []).join(", "));
      }
    })
    .catch(e => toast(e.message, true))
    .finally(() => { spinner.style.display = "none"; });
}

function regenerate(model) {
  if (!model.source) { toast("no source recorded for " + model.name, true); return; }
  build(model.source);
}

function removeModel(name) {
  // No confirmation prompt: delete is cheap and reversible (rebuild from the spec), and the
  // toast reports what happened. The delete action only appears on row hover, so it is hard
  // to trigger by accident.
  fetch(apiUrl("/models/" + encodeURIComponent(name) + "/delete"), { method: "POST" })
    .then(r => r.json())
    .then(d => { if (activeModel === name) { activeModel = null; clearActive("parts"); clearModel(); } renderModelList(d.models); toast("deleted " + name); })
    .catch(() => toast("could not delete " + name, true));
}

const specSearchEl = document.getElementById("spec-search");
const specClearEl = document.getElementById("spec-clear");

function syncSpecClear() {
  specClearEl.hidden = specSearchEl.value === "";
}

specSearchEl.addEventListener("input", ev => { renderSpecTree(ev.target.value); syncSpecClear(); });
specSearchEl.addEventListener("focus", ev => renderSpecTree(ev.target.value));
specSearchEl.addEventListener("blur", () => setTimeout(() => { document.getElementById("spec-tree").hidden = true; }, 150));
specClearEl.addEventListener("mousedown", ev => {
  // mousedown (not click) so it fires before the input's blur hides the tree.
  ev.preventDefault();
  specSearchEl.value = "";
  selectedSpec = null;
  syncSpecClear();
  renderSpecTree("");
  specSearchEl.focus();
});
document.getElementById("spec-build").addEventListener("click", () => {
  // Dispatch by mode: Parts builds a part spec; Assemblies composes an .asm.hocon; Motion builds a
  // .motion.hocon study (drives its referenced assembly + writes the trajectory).
  if (viewMode === "motion") motionBuildSpec(selectedSpec);
  else if (viewMode === "physics") physicsBuildSpec(selectedSpec);
  else if (viewMode === "assemblies") assembleSpec(selectedSpec);
  else build(selectedSpec);
});

// ---- Color theme: one toggle cycling light -> system -> dark (persisted) ----
const THEME_ORDER = ["light", "system", "dark"];
const THEME_ICONS = {
  light: '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>',
  system: '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M8 20h8M12 16v4"/></svg>',
  dark: '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8 8 0 0 1 9.5 4 7 7 0 1 0 20 14.5Z"/></svg>',
};
const themeBtn = document.getElementById("theme-toggle");
const themeIcon = document.getElementById("theme-icon");
const darkMedia = window.matchMedia("(prefers-color-scheme: dark)");
let themeChoice = localStorage.getItem("ncad.theme") || "system";

function resolvedTheme() {
  return themeChoice === "system" ? (darkMedia.matches ? "dark" : "light") : themeChoice;
}
function applyTheme() {
  document.documentElement.setAttribute("data-theme", resolvedTheme());
  themeIcon.innerHTML = THEME_ICONS[themeChoice];
  themeBtn.title = "Theme: " + themeChoice[0].toUpperCase() + themeChoice.slice(1) + " (click to change)";
  applySceneTheme();
}
themeBtn.addEventListener("click", () => {
  themeChoice = THEME_ORDER[(THEME_ORDER.indexOf(themeChoice) + 1) % THEME_ORDER.length];
  localStorage.setItem("ncad.theme", themeChoice);
  applyTheme();
});
// When following the system and the OS theme flips, update live.
darkMedia.addEventListener("change", () => { if (themeChoice === "system") applyTheme(); });
applyTheme();

loadSpecs();
document.getElementById("mode-parts").addEventListener("click", () => setViewMode("parts"));
document.getElementById("mode-assemblies").addEventListener("click", () => setViewMode("assemblies"));
document.getElementById("mode-motion").addEventListener("click", () => setViewMode("motion"));
document.getElementById("mode-physics").addEventListener("click", () => setViewMode("physics"));
document.getElementById("mode-parts").classList.toggle("active", viewMode === "parts");
document.getElementById("mode-assemblies").classList.toggle("active", viewMode === "assemblies");
document.getElementById("mode-motion").classList.toggle("active", viewMode === "motion");
document.getElementById("mode-physics").classList.toggle("active", viewMode === "physics");
syncAssemblyControls();
syncExportControl();   // show the export control for the boot mode (disabled until a model loads)
// Pick the model to show on boot for a mode. Priority: an explicit URL-path request >> the
// saved last-viewed model (page-refresh restore) >> the first available. Returns null when
// nothing was ever selected and nothing was requested (show nothing, per the refresh spec);
// but if the saved model is gone (deleted since), fall back to the first available.
function bootModel(names, mode, requested) {
  if (requested && names.includes(requested)) return requested;
  const saved = savedActive(mode);
  if (saved !== null) return names.includes(saved) ? saved : names[0];
  if (requested) return names[0];  // requested-but-missing still shows something
  return null;                     // nothing selected before >> show nothing
}
if (viewMode === "assemblies") {
  refreshAssemblies().then(names => {
    if (!names || !names.length) return;
    const initial = bootModel(names, "assemblies", null);
    if (initial) selectAssembly(initial);
  });
} else if (viewMode === "motion") {
  refreshMotions().then(names => {
    if (!names || !names.length) return;
    const initial = bootModel(names, "motion", null);
    if (initial) selectMotion(initial);
  });
} else if (viewMode === "physics") {
  refreshRobots().then(names => {
    if (!names || !names.length) return;
    const initial = bootModel(names, "physics", null);
    if (initial) selectRobot(initial);
  });
} else {
  refreshModels().then(models => {
    if (!models || !models.length) return;
    // Deep link: /<model>.glb (stdlib ncad view) or /viewer/<model>.glb (ncad serve). Strip either
    // leading prefix so the requested name resolves the same way under both servers.
    const requested = decodeURIComponent(location.pathname.replace(/^\/viewer\//, "").replace(/^\//, ""));
    const names = models.map(m => m.name);
    const initial = bootModel(names, "parts", requested);
    if (initial) selectModel(initial);
  });
}

function fitRendererToStage() {
  camera.aspect = stage.clientWidth / stage.clientHeight; camera.updateProjectionMatrix();
  renderer.setSize(stage.clientWidth, stage.clientHeight);
  // TrackballControls caches the viewport rect and must be told when it changes.
  if (controls && controls.handleResize) controls.handleResize();
}

window.addEventListener("resize", fitRendererToStage);

// ---- Resizable sidebar (width persisted in localStorage) ----
const SIDEBAR_WIDTH_KEY = "ncad.sidebar.width";
const SIDEBAR_MIN = 220, SIDEBAR_MAX = 560;
const sidebarEl = document.getElementById("sidebar");
const resizerEl = document.getElementById("sidebar-resizer");

function applySidebarWidth(px) {
  // Never let the sidebar crowd out the stage: cap at the smaller of SIDEBAR_MAX and
  // (window width minus a minimum stage width), so the 3D viewport always stays visible.
  const maxByWindow = window.innerWidth - 360;
  const upper = Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, maxByWindow));
  const clamped = Math.max(SIDEBAR_MIN, Math.min(upper, px));
  sidebarEl.style.width = clamped + "px";
  return clamped;
}

const storedWidth = parseInt(localStorage.getItem(SIDEBAR_WIDTH_KEY), 10);
if (!Number.isNaN(storedWidth)) applySidebarWidth(storedWidth);

resizerEl.addEventListener("mousedown", ev => {
  ev.preventDefault();
  resizerEl.classList.add("dragging");
  document.body.classList.add("resizing-sidebar");
  const onMove = e => { applySidebarWidth(e.clientX - sidebarEl.getBoundingClientRect().left); fitRendererToStage(); };
  const onUp = () => {
    resizerEl.classList.remove("dragging");
    document.body.classList.remove("resizing-sidebar");
    localStorage.setItem(SIDEBAR_WIDTH_KEY, parseInt(sidebarEl.style.width, 10));
    window.removeEventListener("mousemove", onMove);
    window.removeEventListener("mouseup", onUp);
  };
  window.addEventListener("mousemove", onMove);
  window.addEventListener("mouseup", onUp);
});

// Double-click the separator to reset to the default width.
resizerEl.addEventListener("dblclick", () => {
  sidebarEl.style.width = "";
  localStorage.removeItem(SIDEBAR_WIDTH_KEY);
  fitRendererToStage();
});

// Dev-only debug handle so automated tests (Playwright) can drive the view deterministically. Gated
// on window.NCAD_DEV, so it is never attached in production (zero cost, no surface). setView orients
// the main camera FROM a named direction in the Z-up world (reusing the ViewCube's orientCameraTo);
// seekFrame scrubs the motion to a frame or a fraction 0..1; state() reports what is loaded.
if (typeof window !== "undefined" && window.NCAD_DEV) {
  const VIEW_DIRS = {
    front: [0, -1, 0], back: [0, 1, 0], right: [1, 0, 0], left: [-1, 0, 0],
    top: [0, 0, 1], bottom: [0, 0, -1], iso: [1, -1, 1],
  };
  window.NCAD_VIEWER = {
    camera, controls, scene,
    setView(name) {
      const d = VIEW_DIRS[name];
      if (!d) throw new Error(`unknown view '${name}'; expected one of ${Object.keys(VIEW_DIRS)}`);
      orientCameraTo(new THREE.Vector3(d[0], d[1], d[2]));
      return name;
    },
    fit() { if (modelRoot) frameModel(); },
    seekFrame(indexOrFraction) {
      if (!motion || !motion.frames.length) return null;
      const n = motion.frames.length;
      const i = Number.isInteger(indexOrFraction) && indexOrFraction >= 1
        ? indexOrFraction : Math.round(indexOrFraction * (n - 1));
      motionPlaying = false; motionPlayBtn.innerHTML = PLAY_ICON;
      showMotionFrame(i);
      return { frame: motionFrame, driver_value: motion.frames[motionFrame].driver_value };
    },
    state() {
      return {
        viewMode, hasModel: !!modelRoot,
        frames: motion ? motion.frames.length : 0, frame: motionFrame,
      };
    },
  };
}

let _lastFrameMs = null;
(function animate(now) {
  requestAnimationFrame(animate);
  if (_lastFrameMs != null && now != null) advanceMotion(now - _lastFrameMs);
  _lastFrameMs = now;
  controls.update();
  renderer.render(scene, camera);
  renderGizmo();
})();
