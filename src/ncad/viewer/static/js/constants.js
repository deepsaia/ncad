// Pure viewer data tables: ViewCube face map, material/BOM/export/lighting/theme presets, palettes,
// and the inline SVG icon strings. All are literals with no behavior and no module state (nothing
// here closes over the 3D scene), so they are a safe slice out of app.js. Each constant keeps its
// original comment(s). Imported by app.js (and future viewer modules).

// Face labels by outward direction, and the BoxGeometry material-group index of that outward face
// (group order is +X, -X, +Y, -Y, +Z, -Z).
export const CUBE_FACES = [
  { dir: [1, 0, 0], label: "RIGHT", group: 0 },
  { dir: [-1, 0, 0], label: "LEFT", group: 1 },
  { dir: [0, 1, 0], label: "BACK", group: 2 },
  { dir: [0, -1, 0], label: "FRONT", group: 3 },
  { dir: [0, 0, 1], label: "TOP", group: 4 },
  { dir: [0, 0, -1], label: "BOTTOM", group: 5 },
];

// Material presets for "Material" mode.
export const MATERIALS = [
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

// A stable palette for trace curves (distinct from the material palette).
export const TRACE_COLORS = [0xff5aa0, 0x5aff9a, 0xffd166, 0x9a7cff, 0x5ad1ff, 0xff8c42];

export const BOM_FIELDS = [
  { key: "floor_area", label: "Floor area", unit: "m²", digits: 1 },
  { key: "roof_area", label: "Roof area", unit: "m²", digits: 1 },
  { key: "wall_volume", label: "Wall volume", unit: "m³", digits: 2 },
  { key: "wall_face_area", label: "Wall face area", unit: "m²", digits: 1 },
  { key: "door_count", label: "Doors", unit: "", digits: 0 },
  { key: "window_count", label: "Windows", unit: "", digits: 0 },
];

// Each preset has its own icon so they are distinct at a glance.
export const LIGHT_ORDER = ["sun", "natural", "studio", "spotlight", "overcast"];
export const LIGHT_NAMES = { sun: "Sun", natural: "Natural", studio: "Studio", spotlight: "Spotlight", overcast: "Overcast" };
export const LIGHT_ICONS = {
  sun: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  natural: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3.5"/><path d="M12 2.5v1.6M12 19.9v1.6M2.5 12h1.6M19.9 12h1.6M5.2 5.2l1.1 1.1M17.7 17.7l1.1 1.1M18.8 5.2l-1.1 1.1M6.3 17.7l-1.1 1.1"/></svg>',
  studio: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="7" r="2.3"/><circle cx="5" cy="16" r="2.3"/><circle cx="19" cy="16" r="2.3"/><path d="M12 9.3v3M9.8 13.8 6.9 15M14.2 13.8l2.9 1.2"/></svg>',
  spotlight: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6l3 6H6L9 3Z"/><path d="M8 9c0 4 1.5 7 4 12 2.5-5 4-8 4-12"/></svg>',
  overcast: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M7 18h9a4 4 0 0 0 .4-8 5.5 5.5 0 0 0-10.6 1.3A3.5 3.5 0 0 0 7 18Z"/></svg>',
};

export const REGEN_SVG = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/></svg>';
export const DELETE_SVG = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>';

export const PLAY_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
export const PAUSE_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';

export const LOOP_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46A7.93 7.93 0 0 0 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74A7.93 7.93 0 0 0 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg>';
export const BOUNCE_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M8 7l-5 5 5 5v-3h8v3l5-5-5-5v3H8z"/></svg>';

// Each tab offers the formats its document kind can produce; picking one re-exports via ncad on the
// server (from the recorded source, so B-rep/robot formats stay faithful) and downloads the file.
export const EXPORT_FORMATS = {
  parts: ["glb", "step", "iges", "stl", "3mf", "obj", "ply"],
  assemblies: ["step", "glb", "stl"],
  motion: ["step", "glb", "stl"],
  physics: ["urdf", "mjcf", "sdf"],
};
export const _MODE_KIND = { parts: "part", assemblies: "assembly", motion: "motion", physics: "physics" };

export const THEME_ORDER = ["light", "system", "dark"];
export const THEME_ICONS = {
  light: '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>',
  system: '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M8 20h8M12 16v4"/></svg>',
  dark: '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8 8 0 0 1 9.5 4 7 7 0 1 0 20 14.5Z"/></svg>',
};
