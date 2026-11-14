// Starts the pyb2d3 sandbox in the browser with pyjs: the WebGL frontend
// (pyb2d3_sandbox_webgl: the instanced GL shaders via PyOpenGL, HTML panel).
// config.json is written by build_page.py.
// URL parameter `sample` selects the first sample, e.g. ?sample=Joints/Ragdoll

const statusEl = document.getElementById("status");

/** show a progress / error message below the canvas */
function status(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

/** the python code starting the sandbox (the sources are mounted at /examples) */
function startScript(sample) {
  return `
import sys, glob
sys.path.insert(0, "/examples")

# which pyb2d3 build was installed (local channel or published)
import json, pyb2d3
for meta in glob.glob("/conda-meta/pyb2d3-*.json") + glob.glob(sys.prefix + "/conda-meta/pyb2d3-*.json"):
    with open(meta) as f:
        info = json.load(f)
    print("pyb2d3 conda package:", meta, info.get("build"), info.get("channel"), info.get("url"))
print("pyb2d3 module:", pyb2d3.__file__, "has cast_ray_circle:", hasattr(pyb2d3, "cast_ray_circle"))
print("pyb2d3 dist-info:", glob.glob("/lib/python3.14/site-packages/pyb2d3*.dist-info"))

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

  status("starting the sandbox…");
  const sample = new URLSearchParams(location.search).get("sample");
  await pyjs.async_exec_eval(startScript(sample));
  status("");
}

main().catch((e) => {
  console.error(e);
  status(`error: ${e?.message ?? e}`, true);
});
