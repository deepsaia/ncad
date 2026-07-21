// A self-contained 3D showcase viewer for the docs site. It renders an ncad assembly scene the same
// way the ncad viewer does: load each instance's per-part glb, place it by the assembly sidecar's
// row-major placement matrix, and (for a motion mechanism) swap each instance's matrix per frame from
// the motion sidecar. Product-neutral, no server: everything is fetched as static files under
// assets/models/<name>/. Three.js is loaded from a CDN import map declared on the page.
//
// Data conventions (identical to src/ncad/viewer/viewer_page.html, the source of truth):
//  - <name>.assembly.json: { instances: [ { id, part_glb, placement, material, appearance_color } ] }
//  - <name>.motion.json:    { frames: [ { placements: { <id>: 4x4 }, driver_value } ] }
//  - a placement is a ROW-MAJOR 4x4 in metres, ROW-VECTOR convention (p_world = p_local . M): the
//    3x3 rotation block holds basis images as ROWS, so three.js (column-vector M . p) needs it
//    TRANSPOSED. Translation is row m[3] -> the 4th column.
//  - each part glb is modeled Y-up; an inner Rx(+90 deg) group lifts it into the scene's Z-up frame.

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

// A small palette so distinct instances read apart even without authored per-body colors. Keyed by
// load order; product-neutral engineering greys/blues, not tied to any material library.
const PALETTE = [
  0xb0b7c3, 0x8fa8c8, 0xc8a26b, 0x9fb08a, 0xc78f8f, 0x8fc7bd, 0xb79fc7, 0xc7bd8f,
];

// ncad placement (row-major, row-vector) -> three.js Matrix4 (column-vector): transpose the 3x3.
function matrixFromRowMajor(m) {
  const M = new THREE.Matrix4();
  M.set(m[0][0], m[1][0], m[2][0], m[3][0],
        m[0][1], m[1][1], m[2][1], m[3][1],
        m[0][2], m[1][2], m[2][2], m[3][2],
        0, 0, 0, 1);
  return M;
}

class ShowcaseViewer {
  constructor(container, modelBase) {
    this.container = container;
    this.modelBase = modelBase;                 // assets/models/<name>
    this.name = modelBase.split("/").pop();
    this.nodes = {};                             // instanceId -> placement Group
    this.motion = null;                          // { frames } or null
    this.frame = 0;
    this.accum = 0;
    this.last = null;
    this.playing = true;
    this.loader = new GLTFLoader();
    this._initScene();
    this._load();
  }

  _initScene() {
    const w = this.container.clientWidth || 640;
    const h = this.container.clientHeight || 420;
    this.scene = new THREE.Scene();
    this.scene.background = null;                // transparent: sits on the page background
    this.camera = new THREE.PerspectiveCamera(45, w / h, 0.001, 100);
    this.camera.position.set(0.16, -0.16, 0.12);
    this.camera.up.set(0, 0, 1);                 // Z-up, matching the modeled frame
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(w, h);
    this.container.appendChild(this.renderer.domElement);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.autoRotate = false;
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x444455, 1.1));
    const key = new THREE.DirectionalLight(0xffffff, 1.4);
    key.position.set(0.3, -0.4, 0.6);
    this.scene.add(key);
    this.root = new THREE.Group();
    this.scene.add(this.root);
    window.addEventListener("resize", () => this._resize());
    this._animate = this._animate.bind(this);
    requestAnimationFrame(this._animate);
  }

  _resize() {
    const w = this.container.clientWidth || 640;
    const h = this.container.clientHeight || 420;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  async _load() {
    const scene = await fetch(`${this.modelBase}/${this.name}.assembly.json`).then(r => r.json());
    // Motion is optional: a static assembly (a house) has no motion sidecar and simply sits still.
    this.motion = await fetch(`${this.modelBase}/${this.name}.motion.json`)
      .then(r => (r.ok ? r.json() : null)).catch(() => null);
    let pending = 0;
    const instances = scene.instances || [];
    instances.forEach((inst, i) => {
      pending++;
      this.loader.load(`${this.modelBase}/${inst.part_glb}`, gltf => {
        const node = new THREE.Group();
        node.matrixAutoUpdate = false;
        node.matrix.copy(matrixFromRowMajor(inst.placement));
        const inner = new THREE.Group();
        inner.rotation.x = Math.PI / 2;          // glb Y-up -> scene Z-up
        inner.add(gltf.scene);
        node.add(inner);
        this._paint(gltf.scene, inst, i);
        this.nodes[inst.id] = node;
        this.root.add(node);
        this.root.updateMatrixWorld(true);
        if (--pending === 0) this._frameCamera();
      }, undefined, () => { pending--; });
    });
  }

  // Give each instance a solid engineering appearance: its authored color if present, else a stable
  // palette entry by load order, so the mechanism reads as distinct parts.
  _paint(obj, inst, i) {
    const c = inst.appearance_color;
    const color = Array.isArray(c)
      ? new THREE.Color(c[0], c[1], c[2])
      : new THREE.Color(PALETTE[i % PALETTE.length]);
    obj.traverse(o => {
      if (o.isMesh) {
        o.material = new THREE.MeshStandardMaterial({ color, metalness: 0.25, roughness: 0.55 });
      }
    });
  }

  // Fit the camera to the loaded scene bounds so every mechanism frames itself regardless of scale.
  _frameCamera() {
    const box = new THREE.Box3().setFromObject(this.root);
    if (box.isEmpty()) return;
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const radius = Math.max(size.x, size.y, size.z) * 0.5 || 0.05;
    this.controls.target.copy(center);
    const dist = radius / Math.tan((this.camera.fov * Math.PI) / 360) * 1.6;
    const dir = new THREE.Vector3(0.7, -0.8, 0.55).normalize();
    this.camera.position.copy(center.clone().add(dir.multiplyScalar(dist)));
    this.camera.near = dist / 100;
    this.camera.far = dist * 100;
    this.camera.updateProjectionMatrix();
    this.controls.update();
  }

  _advance(dt) {
    if (!this.motion || !this.playing) return;
    const frames = this.motion.frames || [];
    if (frames.length < 2) return;
    const fps = 30;                               // playback rate; independent of the solve step count
    this.accum += dt;
    while (this.accum >= 1000 / fps) {
      this.accum -= 1000 / fps;
      this.frame = (this.frame + 1) % frames.length;
    }
    const placements = frames[this.frame].placements || {};
    for (const id in placements) {
      const node = this.nodes[id];
      if (node) node.matrix.copy(matrixFromRowMajor(placements[id]));
    }
  }

  _animate(t) {
    const dt = this.last == null ? 0 : t - this.last;
    this.last = t;
    this._advance(dt);
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
    requestAnimationFrame(this._animate);
  }

  setPlaying(p) { this.playing = p; }
}

// Auto-wire: every element with data-ncad-model becomes a viewer. A small play/pause button rides
// the corner for motion mechanisms. Kept declarative so a docs page just drops a <div>. Guarded with
// a data flag so a re-scan (Material instant navigation) never double-initialises the same element.
function initShowcases() {
  document.querySelectorAll("[data-ncad-model]").forEach(el => {
    if (el.dataset.ncadReady === "1") return;
    el.dataset.ncadReady = "1";
    const base = el.getAttribute("data-ncad-model");
    const viewer = new ShowcaseViewer(el, base);
    if (el.getAttribute("data-ncad-motion") === "true") {
      const btn = document.createElement("button");
      btn.className = "ncad-play";
      btn.textContent = "Pause";
      btn.addEventListener("click", () => {
        viewer.playing = !viewer.playing;
        btn.textContent = viewer.playing ? "Pause" : "Play";
      });
      el.appendChild(btn);
    }
  });
}

// Material for MkDocs swaps page content without a full reload (navigation.instant). Its document$
// observable emits on every page load AND swap; subscribe when present so viewers wire up on any
// page. Fall back to DOMContentLoaded when the theme's document$ is unavailable.
if (typeof window.document$ !== "undefined" && window.document$.subscribe) {
  window.document$.subscribe(() => initShowcases());
} else if (document.readyState !== "loading") {
  initShowcases();
} else {
  document.addEventListener("DOMContentLoaded", initShowcases);
}
