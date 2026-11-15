// Starts the pyb2d3 sandbox in the browser with pyjs: the WebGL frontend
// (pyb2d3_sandbox_webgl: the instanced GL shaders via PyOpenGL, HTML panel).
// config.json is written by build_page.py.
// URL parameter `sample` selects the first sample, e.g. ?sample=Joints/Ragdoll
// (the frontend keeps it up to date when switching samples)

import { setupEditor } from "./editor.js";

const statusEl = document.getElementById("status");

/** show a progress / error message below the canvas */
function status(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

/** the python code starting the sandbox (the sources are mounted at /examples) */
function startScript(sample) {
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
    start=${sample ? JSON.stringify(sample) : "None"}, frontend_class=WebglFrontend
)
`;
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

  setupEditor(pyjs); // before the start: the frontend announces the first sample
  status("starting the sandbox…");
  const sample = new URLSearchParams(location.search).get("sample");
  await pyjs.async_exec_eval(startScript(sample));
  status("");
}

main().catch((e) => {
  console.error(e);
  status(`error: ${e?.message ?? e}`, true);
});
