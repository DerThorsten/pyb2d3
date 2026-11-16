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

// ---- the unpacked archives, cached in IndexedDB ---------------------------------------
// (key: the archive's name, value: {hash, files: {path: bytes}}; a new build has a new
// hash and replaces the entry)

const CACHE_DB = "pyb2d3-sandbox";
const CACHE_STORE = "archives";

/** the cache database, or null if the browser has none (e.g. some private windows) */
async function openCache() {
  try {
    return await new Promise((resolve, reject) => {
      const request = indexedDB.open(CACHE_DB, 1);
      request.onupgradeneeded = () => request.result.createObjectStore(CACHE_STORE);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  } catch (e) {
    console.warn("no IndexedDB cache:", e);
    return null;
  }
}

/** run `action(store)` in a transaction, resolve with the result of its request */
function cacheTransaction(db, mode, action) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(CACHE_STORE, mode);
    const request = action(transaction.objectStore(CACHE_STORE));
    transaction.oncomplete = () => resolve(request.result);
    transaction.onerror = () => reject(transaction.error);
  });
}

/** the bytes at `url`, reporting the fraction downloaded (`expected`: the size) */
async function download(url, expected, onProgress) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  const reader = response.body.getReader();
  const chunks = [];
  let received = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.length;
    onProgress(Math.min(received / expected, 1));
  }
  return new Blob(chunks);
}

/** unpack an archive ({name, url, path, hash, size} from config.json) into the file
 * system: from the cache if it has this build of it, else downloaded, unpacked by pyjs,
 * cached */
async function unpackArchive(pyjs, db, archive, onProgress) {
  const cached = db && (await cacheTransaction(db, "readonly", (s) => s.get(archive.name)).catch(() => null));
  if (cached?.hash === archive.hash) {
    for (const [path, data] of Object.entries(cached.files)) {
      pyjs.FS.mkdirTree(path.slice(0, path.lastIndexOf("/")) || "/");
      pyjs.FS.writeFile(path, data);
    }
    onProgress(1);
    return "cache";
  }
  const blob = await download(new URL(archive.url, location.href).href, archive.size, onProgress);
  // pyjs picks the decompression by the url's ending: keep it after the blob url
  const blobUrl = URL.createObjectURL(blob);
  const paths = await pyjs.unpackArchive({ url: `${blobUrl}#${archive.url}`, path: archive.path });
  URL.revokeObjectURL(blobUrl);
  if (db) {
    const files = Object.fromEntries(paths.map((path) => [path, pyjs.FS.readFile(path)]));
    await cacheTransaction(db, "readwrite", (s) => s.put({ hash: archive.hash, files }, archive.name)).catch((e) =>
      console.warn(`not cached: ${archive.url}`, e),
    );
  }
  return "download";
}

/** the python code starting the sandbox (the sources are mounted at /examples) */
function startScript(sample, maxPixelRatio, options) {
  const settings = maxPixelRatio > 0 ? `WebglFrontend.Settings(max_pixel_ratio=${maxPixelRatio})` : "None";
  return `
import sys
sys.path.insert(0, "/examples")
# no .pyc files: code edited in the page (editor.js) is re-imported, a cached
# .pyc with the same mtime (1 s resolution) + size could win over the source
sys.dont_write_bytecode = True

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

/** compile the shared libraries of the archives ahead of time, as pyjs does for the
 * packages it installs: browsers refuse to compile a large one (libopenblas: ~9 MB)
 * synchronously, on import. Plain libraries first, global and by name (the name the
 * extension modules ask for), then the extension modules (by path, as python opens them) */
async function preloadSharedLibs(pyjs, paths, onProgress) {
  const isModule = (path) => /cpython-3\d+-wasm(32|64)-emscripten\.so$/.test(path);
  const libs = new Map(paths.filter((p) => !isModule(p)).map((p) => [p.slice(p.lastIndexOf("/") + 1), p]));
  const fs = {
    findObject: (path, dontResolve) => pyjs.FS.findObject(libs.get(path) ?? path, dontResolve),
    readFile: (path) => pyjs.FS.readFile(libs.get(path) ?? path),
  };
  const flags = { loadAsync: true, nodelete: true, allowUndefined: true, fs };
  let loaded = 0;
  for (const name of libs.keys()) {
    await pyjs.loadDynamicLibrary(name, { ...flags, global: true });
    onProgress(++loaded / paths.length);
  }
  for (const path of paths.filter(isModule)) {
    await pyjs.loadDynamicLibrary(path, { ...flags, global: false });
    onProgress(++loaded / paths.length);
  }
}

/** load pyjs, unpack the archives (sources, packages), start the sandbox; logs how
 * long each part took */
async function main() {
  const start = performance.now();
  const times = {};
  const lap = (name) => (times[name] = ((performance.now() - start) / 1000).toFixed(2));

  // revalidated on every load: it names this build's archives (content hashes)
  const config = await (await fetch("config.json", { cache: "no-cache" })).json();
  const absolute = (url) => new URL(url, location.href).href;

  // the progress bar: pyjs 5%, python 25%, the archives 55% (by size), the shared
  // libraries 10%, the sandbox 5%
  progress(0);
  status("loading pyjs…");
  const cache = openCache(); // meanwhile
  const { initializePyjsRuntime } = await import(absolute(config.pyjs));
  lap("pyjs loaded");
  progress(0.05);
  status("starting python…");
  // no extra packages: pyjs starts its packed environment, no package install (mamba)
  const pyjs = await initializePyjsRuntime({
    logger: { log: (msg) => status(String(msg)), warn: console.warn, error: console.error },
  });
  globalThis.pyjs = pyjs; // for the browser console
  lap("python running");
  progress(0.3);

  // the archives (sources, packed packages): from the cache or downloaded
  const db = await cache;
  const total = config.archives.reduce((sum, a) => sum + a.size, 0);
  let done = 0;
  const sources = [];
  for (const archive of config.archives) {
    status(`loading ${archive.name}…`);
    const share = archive.size / total;
    sources.push(await unpackArchive(pyjs, db, archive, (f) => progress(0.3 + 0.55 * (done + f * share))));
    done += share;
  }
  pyjs.exec("import importlib\nimportlib.invalidate_caches()");
  lap(`archives (${sources.join(", ")})`);

  status("preloading shared libraries…");
  await preloadSharedLibs(pyjs, config.shared_libs, (f) => progress(0.85 + 0.1 * f));
  lap("shared libraries");

  const editor = setupEditor(pyjs); // before the start: the frontend announces the first sample
  status("starting the sandbox…");
  const params = new URLSearchParams(location.search);
  const dpr = parseFloat(params.get("dpr")); // NaN without the parameter
  const options = Object.fromEntries([...params].filter(([name]) => name !== "sample" && name !== "dpr"));
  await pyjs.async_exec_eval(startScript(params.get("sample"), dpr, options));
  lap("sandbox running");
  progress(null);
  status("");
  console.info("pyb2d3 sandbox loading times (s since start):", times);
  editor.preload(); // the code pane opens instantly later (monaco: several MB)
}

setupLayout();
setupKeyFocus();
main().catch((e) => {
  console.error(e);
  status(`error: ${e?.message ?? e}`, true);
});
