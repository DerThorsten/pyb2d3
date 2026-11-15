// Starts the pyb2d3 sandbox in the browser with pyjs: the WebGL frontend
// (pyb2d3_sandbox_webgl: the instanced GL shaders via PyOpenGL, HTML panel).
// config.json is written by build_page.py.
// URL parameter `sample` selects the first sample, e.g. ?sample=Joints/Ragdoll
// (the frontend keeps it up to date when switching samples); `dpr` caps the
// drawing buffer's pixels per CSS pixel (default 2), e.g. ?dpr=1 to check whether
// a slow device is limited by the GPU's fill rate

import { setupEditor } from "./editor.js";

const statusEl = document.getElementById("status");

/** show a progress / error message below the canvas */
function status(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

/** the python code starting the sandbox (the sources are mounted at /examples) */
function startScript(sample, maxPixelRatio) {
  const settings = maxPixelRatio > 0 ? `WebglFrontend.Settings(max_pixel_ratio=${maxPixelRatio})` : "None";
  return `
import sys
sys.path.insert(0, "/examples")
# no .pyc files: code edited in the page (editor.js) is re-imported, a cached
# .pyc with the same mtime (1 s resolution) + size could win over the source
sys.dont_write_bytecode = True

import pyb2d3_samples  # registers the samples
from pyb2d3_sandbox import run_sample_browser
from pyb2d3_sandbox_webgl import WebglFrontend

# returns right away (frames come from requestAnimationFrame); keep the
# frontend alive in a global
_sandbox_frontend = run_sample_browser(
    start=${sample ? JSON.stringify(sample) : "None"}, frontend_class=WebglFrontend,
    frontend_settings=${settings},
)
`;
}

/** compact screens (phones, small tablets; see index.html): the panel is a bottom
 * sheet (portrait) or a drawer (landscape) over the canvas, opened / closed by the
 * ☰ button or the sheet's grip (class panel-open on #app; the desktop layout
 * ignores it) */
function setupLayout() {
  const app = document.getElementById("app");
  const toggleButton = document.getElementById("panel-toggle");
  const toggle = () => {
    const open = app.classList.toggle("panel-open");
    toggleButton.classList.toggle("active", open);
  };
  toggleButton.addEventListener("click", toggle);
  document.getElementById("side-grip").addEventListener("click", toggle);
}

/** keys go to the focused canvas: give it the focus whenever a sample starts (after
 * the sample select / buttons / the first start), unless the user is in the code pane */
function setupKeyFocus() {
  const canvas = document.getElementById("canvas");
  const code = document.getElementById("code");
  window.addEventListener("pyb2d3-sample", () => {
    if (!code.contains(document.activeElement)) canvas.focus({ preventScroll: true });
  });
}

/** load pyjs + packages + sources, start the sandbox */
async function main() {
  const config = await (await fetch("config.json")).json();
  const absolute = (url) => new URL(url, location.href).href;

  status("loading pyjs…");
  const { initializePyjsRuntime } = await import(absolute(config.pyjs));
  status(`installing ${config.packages.join(", ")}…`);
  const pyjs = await initializePyjsRuntime({
    // local channels (copied into the page) first: they win over the public ones
    channels: [...config.local_channels.map(absolute), ...config.channels],
    extraPackages: config.packages,
    archives: config.archives, // unpacked with untarjs before python starts
    logger: { log: (msg) => status(String(msg)), warn: console.warn, error: console.error },
  });
  globalThis.pyjs = pyjs; // for the browser console

  const editor = setupEditor(pyjs); // before the start: the frontend announces the first sample
  status("starting the sandbox…");
  const params = new URLSearchParams(location.search);
  const dpr = parseFloat(params.get("dpr")); // NaN without the parameter
  await pyjs.async_exec_eval(startScript(params.get("sample"), dpr));
  status("");
  editor.preload(); // the code pane opens instantly later (monaco: several MB)
}

setupLayout();
setupKeyFocus();
main().catch((e) => {
  console.error(e);
  status(`error: ${e?.message ?? e}`, true);
});
