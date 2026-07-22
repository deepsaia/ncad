// Scene lighting rig: the always-on ambient hemisphere plus a swappable directional/spot rig
// (sun / natural / studio / spotlight / overcast), and the shadow-frustum fitting that keeps the
// fixed-size shadow map sharp on the current model.
//
// Extracted from app.js. The rig owns its own ambient + lightRig group + presets; its couplings to
// the main viewer are the `scene` (a stable const, injected once so ambient/lightRig get added) and
// `modelRoot` (reassigned in app.js when a model loads, so read live via an injected accessor).
// setLighting (the Lighting control), fitShadowCameras (called by frameModel) and setShadowRadius
// (frameModel publishes the framed model radius here) are the public surface.
import * as THREE from "three";

// The scene (injected once by initLighting) and a live accessor for modelRoot (reassigned in
// app.js on model load, so read fresh each time).
let scene = null;
let getModelRoot = null;

// Ambient base, always on; the rig below provides the directional/spot character. The world is
// Z-UP (ground in XY), so a HemisphereLight's sky/ground axis must point up +Z (its default is
// +Y); position (0,0,1) reorients its gradient so "sky" is overhead, not sideways.
const ambient = new THREE.HemisphereLight(0xffffff, 0x2a3340, 0.45);
ambient.position.set(0, 0, 1);

// A swappable light rig. Each preset clears and rebuilds `lightRig`.
const lightRig = new THREE.Group();

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

export function setLighting(name) {
  lightRig.clear();
  const preset = LIGHT_PRESETS[name] || LIGHT_PRESETS.sun;
  preset().forEach(l => { lightRig.add(l); if (l.target) lightRig.add(l.target); });
  localStorage.setItem("ncad.light", name);
  if (getModelRoot()) fitShadowCameras();
}

// Size every shadow-casting light's ortho frustum to the current model so the fixed 2048 shadow
// map spends its texels on the model (a frustum many times the model size gives coarse, streaky
// shadows). Called from frameModel + setLighting. Uses the framed model radius; the model sits
// centered at the origin lifted by half its height on +Z.
let shadowRadius = 40;

// frameModel publishes the framed model radius here (previously a bare shared `let`).
export function setShadowRadius(r) {
  shadowRadius = r;
}

export function fitShadowCameras() {
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

// Add the ambient + light rig to the scene. Called once by app.js. `sceneArg` is the main scene;
// `getModelRootArg` returns the current modelRoot (reassigned in app.js on model load).
export function initLighting(sceneArg, getModelRootArg) {
  scene = sceneArg;
  getModelRoot = getModelRootArg;
  scene.add(ambient);
  scene.add(lightRig);
}
