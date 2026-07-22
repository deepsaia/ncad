// Panel placement controller for the floating viewport-controls bar: a corner anchor picker plus
// free drag with edge snapping (position persisted in localStorage). The geometry functions stay
// pure of the 3D scene - they touch only the controls element, the stage element, and localStorage
// - so this is a safe slice out of app.js. controlsEl + stage are injected by initPanelPlacement
// (app.js owns them; the show-text toggle also uses controlsEl, so it stays declared there). Each
// function/comment is kept verbatim from app.js.

// ---- Panel placement: corner anchor picker + free drag with edge snapping ----
const CORNER_KEY = "ncad.vc.corner", POS_KEY = "ncad.vc.pos";
const MARGIN = 16;

// The floating viewport-controls element and the stage element, injected by initPanelPlacement.
let controlsEl = null;
let stage = null;

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

// Wire the corner picker + the free-drag grip, then restore the saved placement. Called once by
// app.js after the viewport-controls element exists.
export function initPanelPlacement(controlsElArg, stageArg) {
  controlsEl = controlsElArg;
  stage = stageArg;
  const cornerBtn = document.getElementById("vc-corner");
  const cornerPop = document.getElementById("vc-corner-pop");

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
}
