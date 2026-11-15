// Code pane of the sandbox page: edit the source file of the running sample
// (from the archive mounted at /examples) with Monaco, run it without reloading
// the page.
//
// * the pane always shows the file of the running sample (the frontend announces
//   it: event "pyb2d3-sample" with its source file + line); one editor model per
//   file, so edits survive switching samples
// * Run (Ctrl/Cmd+Enter or Ctrl/Cmd+S): writes the file into the file system,
//   the frontend re-imports it and restarts the running sample
//   (WebglFrontend.reload_code)
// * errors of the sample ("pyb2d3-error": the traceback) show below the editor

const MONACO = "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2";
// only the sample code is shown, not the sandbox / its frontends (the other
// pyb2d3_* packages in /examples)
const ROOT = "/examples/pyb2d3_samples";

const $ = (id) => document.getElementById(id);

/** load a classic script (the monaco AMD loader) */
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error(`cannot load ${src}`));
    document.head.appendChild(s);
  });
}

let monacoLoading = null;

/** monaco (from cdnjs), or null if it cannot be loaded; loaded once (several MB:
 * preloaded in the background after the sandbox started, see setupEditor) */
function loadMonaco() {
  monacoLoading ??= fetchMonaco();
  return monacoLoading;
}

async function fetchMonaco() {
  try {
    await loadScript(`${MONACO}/min/vs/loader.min.js`);
    // the worker comes from another origin: start it via a data url
    window.MonacoEnvironment = {
      getWorkerUrl: () =>
        "data:text/javascript;charset=utf-8," +
        encodeURIComponent(
          `self.MonacoEnvironment = { baseUrl: "${MONACO}/min/" };` +
          `importScripts("${MONACO}/min/vs/base/worker/workerMain.js");`
        ),
    };
    window.require.config({ paths: { vs: `${MONACO}/min/vs` } });
    return await new Promise((resolve, reject) => {
      // the AMD loader may neither succeed nor fail (a stalled request): give up after a minute
      setTimeout(() => reject(new Error("loading monaco timed out")), 60_000);
      window.require(["vs/editor/editor.main"], () => resolve(window.monaco), reject);
    });
  } catch (e) {
    console.warn("monaco not available, using a textarea", e);
    return null;
  }
}

/** a textarea with the editor interface used below (fallback without monaco) */
function textareaEditor(parent, onRun) {
  const ta = document.createElement("textarea");
  ta.className = "code-fallback";
  ta.spellcheck = false;
  parent.appendChild(ta);
  ta.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && (e.key === "Enter" || e.key === "s")) { e.preventDefault(); onRun(); }
    if (e.key === "Tab") { e.preventDefault(); ta.setRangeText("    ", ta.selectionStart, ta.selectionEnd, "end"); }
  });
  const docs = new Map(); // path -> text
  let current = null;
  return {
    open(path, text, line) {
      if (current !== null) docs.set(current, ta.value);
      current = path;
      ta.value = docs.has(path) ? docs.get(path) : text;
      if (line) {
        const offset = ta.value.split("\n").slice(0, line - 1).join("\n").length;
        ta.setSelectionRange(offset, offset);
      }
    },
    focus() { ta.focus(); },
    value(path) { return path === current ? ta.value : docs.get(path); },
    set(path, text) { if (path === current) ta.value = text; else docs.set(path, text); },
    onChange(fn) { ta.addEventListener("input", fn); },
  };
}

/** a monaco editor with one model per file */
function monacoEditor(monaco, parent, onRun) {
  monaco.editor.defineTheme("pyb2d3", {
    base: "vs-dark", inherit: true, rules: [],
    colors: { "editor.background": "#1b1d21" },
  });
  const editor = monaco.editor.create(parent, {
    language: "python", theme: "pyb2d3", automaticLayout: true,
    minimap: { enabled: false }, fontSize: 13, scrollBeyondLastLine: false, tabSize: 4,
  });
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, onRun);
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, onRun);
  const models = new Map(); // path -> model
  return {
    open(path, text, line) {
      if (!models.has(path)) {
        models.set(path, monaco.editor.createModel(text, "python", monaco.Uri.file(path)));
      }
      editor.setModel(models.get(path));
      if (line) {
        editor.revealLineNearTop(line);
        editor.setPosition({ lineNumber: line, column: 1 });
      }
    },
    focus() { editor.focus(); },
    value(path) { return models.get(path)?.getValue(); },
    set(path, text) { models.get(path)?.setValue(text); },
    onChange(fn) { editor.onDidChangeModelContent(fn); },
  };
}

const WIDTH_KEY = "pyb2d3-code-width"; // localStorage: the pane width the user dragged

/** the handle on the code pane's left edge: drag (mouse or finger) to widen /
 * narrow the pane; the canvas keeps at least 120 px; the width is remembered */
function setupResizer(pane) {
  const handle = $("code-resizer");
  const clamp = (width) => Math.max(280, Math.min(width, window.innerWidth - 120));
  try {
    const saved = parseFloat(localStorage.getItem(WIDTH_KEY));
    if (saved > 0) pane.style.width = `${clamp(saved)}px`;
  } catch (e) { /* no storage (private mode): the default width */ }
  // the dragging pointer is tracked here and the moves are taken from window: pointer
  // capture of touches differs between browsers (iPad Safari), window always gets them
  let dragging = null;
  handle.addEventListener("pointerdown", (e) => {
    dragging = e.pointerId;
    try { handle.setPointerCapture(e.pointerId); } catch (err) { /* not needed */ }
    handle.classList.add("dragging");
    e.preventDefault();
  });
  window.addEventListener("pointermove", (e) => {
    if (e.pointerId !== dragging) return;
    // the pane is on the right: its width is the distance from the pointer to the right edge
    pane.style.width = `${clamp(window.innerWidth - e.clientX)}px`;
    e.preventDefault();
  }, { passive: false });
  const done = (e) => {
    if (e.pointerId !== dragging) return;
    dragging = null;
    handle.classList.remove("dragging");
    try { localStorage.setItem(WIDTH_KEY, String(pane.getBoundingClientRect().width)); } catch (err) { /* ignore */ }
  };
  window.addEventListener("pointerup", done);
  window.addEventListener("pointercancel", done);
}

/** the code pane; call before the sandbox starts (it announces the first sample) */
export function setupEditor(pyjs) {
  const pane = $("code");
  const fs = pyjs.FS;
  const original = new Map(); // path -> text from the archive (Revert)
  const saved = new Map(); // path -> text in the file system
  let editor = null; // created on first open
  let opening = null;
  let currentFile = null; // the file in the editor (null: the sample has no editable code)
  let sample = { key: null, file: null, line: 0 }; // announced by the frontend
  let shownKey = null; // the sample whose file is shown

  const read = (path) => fs.readFile(path, { encoding: "utf8" });

  /** show a python error (or hide the box with null) */
  function showError(text) {
    $("code-error").textContent = text || "";
    $("code-error").hidden = !text;
  }

  /** the file name in the bar, with a dot while it differs from the original */
  function updateLabel() {
    const label = $("code-file");
    if (!currentFile) {
      label.textContent = sample.key ? "this sample has no editable code" : "";
      return;
    }
    const modified = editor.value(currentFile) !== original.get(currentFile);
    label.textContent = currentFile.slice(ROOT.length + 1) + (modified ? " ●" : "");
    label.title = currentFile;
  }

  /** show the file of the running sample (scrolled to its class) */
  function showSample() {
    if (!editor) return;
    // only sample code (e.g. not a sample class defined in the sandbox itself)
    const path = sample.file?.startsWith(ROOT + "/") ? sample.file : null;
    if (path && !original.has(path)) {
      const text = read(path);
      original.set(path, text);
      saved.set(path, text);
    }
    // a new sample: scroll to its class; the same one again (after Run): keep the cursor
    if (path && (path !== currentFile || sample.key !== shownKey)) {
      editor.open(path, saved.get(path), sample.line);
    }
    currentFile = path;
    shownKey = sample.key;
    $("code-editor").hidden = !path;
    $("code-run").disabled = !path;
    $("code-revert").disabled = !path;
    updateLabel();
  }

  /** write the file (if edited), re-import it, restart the running sample */
  function run() {
    if (!editor || !currentFile) return;
    const text = editor.value(currentFile);
    const changed = [];
    if (text !== saved.get(currentFile)) {
      fs.writeFile(currentFile, text);
      saved.set(currentFile, text);
      changed.push(currentFile);
    }
    showError(null);
    pyjs.exec(`_sandbox_frontend.reload_code(${JSON.stringify(changed)})`);
  }

  /** back to the original of the current file (in the editor; Run applies it) */
  function revert() {
    if (currentFile && editor) editor.set(currentFile, original.get(currentFile));
    updateLabel();
  }

  /** show the pane; the first time: load monaco */
  async function open() {
    pane.hidden = false;
    $("code-toggle").classList.add("active");
    if (!editor) {
      $("code-file").textContent = "loading the editor…";
      opening ??= (async () => {
        const monaco = await loadMonaco();
        editor = monaco ? monacoEditor(monaco, $("code-editor"), run) : textareaEditor($("code-editor"), run);
        editor.onChange(updateLabel);
      })().catch((e) => {
        opening = null; // the next open tries again
        throw e;
      });
      try {
        await opening;
      } catch (e) {
        console.error(e);
        $("code-file").textContent = "the editor could not be created";
        showError(String(e?.stack ?? e));
        return;
      }
    }
    if (!pane.hidden) {
      // (closed while loading: shown on the next open)
      showSample();
      // the user opened the pane: type right away (switching samples doesn't take
      // the focus: the keys stay with the sample)
      if (currentFile) editor.focus();
    }
    window.dispatchEvent(new Event("resize")); // the canvas got narrower
  }

  /** fetch monaco in the background (the first open is then instant) */
  function preload() {
    const idle = window.requestIdleCallback ?? ((fn) => setTimeout(fn, 1000));
    idle(() => loadMonaco());
  }

  function close() {
    pane.hidden = true;
    $("code-toggle").classList.remove("active");
    window.dispatchEvent(new Event("resize"));
  }

  setupResizer(pane);
  $("code-toggle").addEventListener("click", () => (pane.hidden ? open() : close()));
  $("code-close").addEventListener("click", close);
  $("code-run").addEventListener("click", run);
  $("code-revert").addEventListener("click", revert);

  window.addEventListener("pyb2d3-sample", (e) => {
    sample = e.detail;
    showError(null);
    if (!pane.hidden) showSample();
  });
  window.addEventListener("pyb2d3-error", (e) => {
    showError(e.detail);
    if (pane.hidden) open();
  });
  return { preload };
}
