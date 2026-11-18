// Starts the pyb2d3 sandbox in the browser with pyjs: the WebGL frontend
// (pyb2d3_sandbox_webgl: the instanced GL shaders via PyOpenGL, HTML panel).
// config.json is written by build_page.py.
// URL parameter `sample` selects the first sample, e.g. ?sample=Joints/Ragdoll
// (the frontend keeps it up to date when switching samples); `dpr` caps the
// drawing buffer's pixels per CSS pixel (default 2), e.g. ?dpr=1 to check whether
// a slow device is limited by the GPU's fill rate

import { setupEditor } from "./editor.js";

const statusEl = document.getElementById("status");
const progressEl = document.getElementById("progress");

/** show a progress / error message below the canvas */
function status(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

/** the loading progress bar: `value` in [0, 1], null hides it */
function progress(value) {
  progressEl.hidden = value === null;
  if (value !== null) progressEl.value = value;
}

/** loading progress of pyjs (`onProgress`): the downloads (bytes of the archives,
 * sizes from config.json) fill the bar up to 90%, the rest is unpacking / linking /
 * starting python; the status line names the phase */
function progressReporter(archives) {
  const total = archives.reduce((sum, a) => sum + a.size, 0) || 1;
  const received = new Map(); // archive url -> bytes downloaded
  const labels = { download: "loading", cached: "from cache", extract: "unpacking", link: "linking", start: "starting" };
  return ({ item, phase, done }) => {
    if (phase === "download") {
      received.set(item, done);
      const bytes = [...received.values()].reduce((sum, b) => sum + b, 0);
      progress(0.9 * Math.min(bytes / total, 1));
    } else if (phase === "start") {
      progress(0.95);
    }
    const name = item.split("/").pop().split("-")[0]; // examples-<hash>.tar.gz -> examples
    status(`${labels[phase] ?? phase} ${name}…`);
  };
}

/** the python code starting the sandbox (the sources are mounted at /examples) */
function startScript(sample, maxPixelRatio, options) {
  const settings = maxPixelRatio > 0 ? `WebglFrontend.Settings(max_pixel_ratio=${maxPixelRatio})` : "None";
  return `
import sys
sys.path.insert(0, "/examples")
# (bytecode is written: pyjs caches it for the next visit; reload_code drops the
# .pyc of edited files)

import pyb2d3_samples  # registers the samples
from pyb2d3_sandbox import run_sample_browser, set_extra_options
from pyb2d3_sandbox_webgl import WebglFrontend

# the other URL query parameters, for the samples (get_extra_options)
set_extra_options(${JSON.stringify(options)})

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

/** load pyjs, which unpacks the archives (sources, packed packages; cached by pyjs),
 * preloads their shared libraries and starts python; then start the sandbox. Logs how
 * long each part took */
async function main() {
  const start = performance.now();
  const times = {}; // seconds since start, and pyjs' own phases
  const lap = (name) => (times[name] = ((performance.now() - start) / 1000).toFixed(2));

  // revalidated on every load: it names this build's archives (content hashes)
  const config = await (await fetch("config.json", { cache: "no-cache" })).json();
  const absolute = (url) => new URL(url, location.href).href;

  progress(0);
  status("loading pyjs…");
  const { initializePyjsRuntime } = await import(absolute(config.pyjs));
  lap("pyjs loaded");
  const pyjs = await initializePyjsRuntime({
    // cache: unpacked files + bytecode kept by pyjs (>= 5.1), keyed by the hashed url
    archives: config.archives.map(({ url, path }) => ({ url: absolute(url), path, cache: true })),
    onProgress: progressReporter(config.archives),
  });
  globalThis.pyjs = pyjs; // for the browser console
  lap("python running");
  for (const [phase, ms] of Object.entries(pyjs.initTimings)) {
    times[`pyjs ${phase}`] = (ms / 1000).toFixed(2); // durations
  }
  navigator.storage?.persist?.().catch(() => {}); // keep pyjs' caches (best effort)

  const editor = setupEditor(pyjs); // before the start: the frontend announces the first sample
  status("starting the sandbox…");
  const params = new URLSearchParams(location.search);
  const dpr = parseFloat(params.get("dpr")); // NaN without the parameter
  const options = Object.fromEntries([...params].filter(([name]) => name !== "sample" && name !== "dpr"));
  await pyjs.async_exec_eval(startScript(params.get("sample"), dpr, options));
  lap("sandbox running");
  pyjs.saveBytecode(); // the sandbox's imports, for the next visit (else saved every few s)
  progress(null);
  status("");
  console.info("pyb2d3 sandbox loading times (s since start; pyjs phases: s each):", times);
  editor.preload(); // the code pane opens instantly later (monaco: several MB)
}

setupLayout();
setupKeyFocus();
main().catch((e) => {
  console.error(e);
  status(`error: ${e?.message ?? e}`, true);
});
