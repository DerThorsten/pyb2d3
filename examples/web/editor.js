// Code pane of the sandbox page: edit the sample sources (the archive mounted
// at /examples) with Monaco and run them without reloading the page.
//
// * file tree: the sample code (/examples/pyb2d3_samples)
// * one editor model per opened file: edits survive switching files / samples
// * Run (Ctrl/Cmd+Enter or Ctrl/Cmd+S): writes the changed files into the file
//   system, the frontend re-imports them + the sample's module and starts the
//   sample (WebglFrontend.reload_code). Which sample: the one whose class the
//   cursor is in, else the running one (if in this file), else the file's first;
//   files without samples (helpers) restart the running sample. The button
//   shows it ("Run Category / Name").
// * the frontend announces the current sample (event "pyb2d3-sample": its
//   source file + line) and errors of the sample ("pyb2d3-error": the traceback)

const MONACO = "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2";
// the file tree shows the sample code only (its contents at the top level),
// not the sandbox / its frontends (the other pyb2d3_* packages in /examples)
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

/** monaco (from cdnjs), or null if it cannot be loaded */
async function loadMonaco() {
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
    return await new Promise((resolve, reject) =>
      window.require(["vs/editor/editor.main"], () => resolve(window.monaco), reject)
    );
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
      ta.focus();
    },
    value(path) { return path === current ? ta.value : docs.get(path); },
    set(path, text) { if (path === current) ta.value = text; else docs.set(path, text); },
    paths() { if (current !== null) docs.set(current, ta.value); return [...docs.keys()]; },
    onChange(fn) { ta.addEventListener("input", fn); },
    cursorLine() { return ta.value.slice(0, ta.selectionStart).split("\n").length; },
    onCursor(fn) { for (const ev of ["keyup", "click", "input"]) ta.addEventListener(ev, fn); },
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
      editor.focus();
    },
    value(path) { return models.get(path)?.getValue(); },
    set(path, text) { models.get(path)?.setValue(text); },
    paths() { return [...models.keys()]; },
    onChange(fn) { editor.onDidChangeModelContent(fn); },
    cursorLine() { return editor.getPosition()?.lineNumber ?? 1; },
    onCursor(fn) { editor.onDidChangeCursorPosition(fn); },
  };
}

/** the code pane; call before the sandbox starts (it announces the first sample) */
export function setupEditor(pyjs) {
  const pane = $("code");
  const fs = pyjs.FS;
  const original = new Map(); // path -> text from the archive (Revert)
  const saved = new Map(); // path -> text in the file system
  let editor = null; // created on first open
  let opening = null;
  let currentFile = null;
  let sample = { key: null, file: null, line: 0 }; // announced by the frontend
  const fileSamples = new Map(); // path -> [{key, first, last}] (sample classes in the file)

  const read = (path) => fs.readFile(path, { encoding: "utf8" });
  const isDir = (path) => fs.isDir(fs.stat(path).mode);

  /** show a python error (or hide the box with null) */
  function showError(text) {
    $("code-error").textContent = text || "";
    $("code-error").hidden = !text;
  }

  /** mark the changed files in the tree */
  function markModified() {
    for (const el of document.querySelectorAll("#code-tree .file")) {
      const value = editor?.value(el.dataset.path);
      el.classList.toggle("modified", value !== undefined && value !== original.get(el.dataset.path));
    }
  }

  /** the tree of ROOT (folders: <details>, files: clickable rows) */
  function buildTree(dir, parent, depth) {
    const names = fs.readdir(dir).filter((n) => n !== "." && n !== ".." && n !== "__pycache__").sort();
    const dirs = names.filter((n) => isDir(`${dir}/${n}`));
    const files = names.filter((n) => !isDir(`${dir}/${n}`) && /\.(py|glsl|vert|frag|txt|md)$/.test(n));
    for (const name of dirs) {
      const details = document.createElement("details");
      details.dataset.path = `${dir}/${name}`;
      const summary = document.createElement("summary");
      summary.textContent = name;
      details.append(summary);
      parent.append(details);
      buildTree(`${dir}/${name}`, details, depth + 1);
    }
    for (const name of files) {
      const row = document.createElement("div");
      row.className = "file";
      row.textContent = name;
      row.dataset.path = `${dir}/${name}`;
      row.title = row.dataset.path;
      row.addEventListener("click", () => openFile(row.dataset.path, 0));
      parent.append(row);
    }
  }

  /** open `path` in the editor (scrolled to `line`), select it in the tree */
  function openFile(path, line) {
    // only sample code (e.g. not a sample class defined in the sandbox itself)
    if (!path || !editor || !path.startsWith(ROOT + "/")) return;
    if (!original.has(path)) {
      const text = read(path);
      original.set(path, text);
      saved.set(path, text);
    }
    currentFile = path;
    editor.open(path, saved.get(path), line);
    $("code-file").textContent = path.slice(ROOT.length + 1);
    for (const el of document.querySelectorAll("#code-tree .file")) {
      el.classList.toggle("current", el.dataset.path === path);
    }
    for (const details of document.querySelectorAll("#code-tree details")) {
      if (path.startsWith(details.dataset.path + "/")) details.open = true;
    }
    document.querySelector("#code-tree .file.current")?.scrollIntoView({ block: "nearest" });
    updateRunLabel();
  }

  /** the registered samples defined in `path` (asked once per file and run) */
  function samplesIn(path) {
    if (!fileSamples.has(path)) {
      const json = pyjs.eval(`_sandbox_frontend.samples_in_file(${JSON.stringify(path)})`);
      fileSamples.set(path, JSON.parse(String(json)));
    }
    return fileSamples.get(path);
  }

  /** the sample Run starts: the one whose class the cursor is in; else the
   * running sample if this file defines it, else the file's first sample; a
   * file without samples (a helper): the running sample */
  function runTarget() {
    const samples = currentFile ? samplesIn(currentFile) : [];
    if (!samples.length) return sample.key;
    const line = editor.cursorLine();
    const inside = samples.find((s) => line >= s.first && line <= s.last);
    if (inside) return inside.key;
    if (samples.some((s) => s.key === sample.key)) return sample.key;
    return samples[0].key;
  }

  /** the Run button says which sample it starts */
  function updateRunLabel() {
    const key = editor ? runTarget() : sample.key;
    $("code-run").textContent = key ? `▶ Run ${key.replace("/", " / ")}` : "▶ Run";
  }

  /** write the changed files, re-import them, start the sample of runTarget() */
  function run() {
    if (!editor) return;
    const changed = [];
    for (const path of editor.paths()) {
      const text = editor.value(path);
      if (text !== undefined && text !== saved.get(path)) {
        fs.writeFile(path, text);
        saved.set(path, text);
        changed.push(path);
      }
    }
    const target = runTarget();
    for (const path of changed) fileSamples.delete(path); // class line ranges changed
    showError(null);
    const key = target ? JSON.stringify(target) : "None";
    pyjs.exec(`_sandbox_frontend.reload_code(${JSON.stringify(changed)}, ${key})`);
  }

  /** back to the original of the current file (in the editor; Run applies it) */
  function revert() {
    if (currentFile && editor) editor.set(currentFile, original.get(currentFile));
    markModified();
  }

  /** show the pane; the first time: load monaco, build the tree */
  async function open() {
    pane.hidden = false;
    $("code-toggle").classList.add("active");
    if (!editor) {
      opening ??= (async () => {
        $("code-file").textContent = "loading the editor…";
        const monaco = await loadMonaco();
        editor = monaco ? monacoEditor(monaco, $("code-editor"), run) : textareaEditor($("code-editor"), run);
        editor.onChange(markModified);
        editor.onCursor(updateRunLabel);
        buildTree(ROOT, $("code-tree"), 0);
      })();
      await opening;
    }
    openFile(sample.file ?? currentFile, sample.line);
    window.dispatchEvent(new Event("resize")); // the canvas got narrower
  }

  function close() {
    pane.hidden = true;
    $("code-toggle").classList.remove("active");
    window.dispatchEvent(new Event("resize"));
  }

  $("code-toggle").addEventListener("click", () => (pane.hidden ? open() : close()));
  $("code-close").addEventListener("click", close);
  $("code-run").addEventListener("click", run);
  $("code-revert").addEventListener("click", revert);

  window.addEventListener("pyb2d3-sample", (e) => {
    sample = e.detail;
    showError(null);
    if (!pane.hidden && editor && sample.file && sample.file !== currentFile) openFile(sample.file, sample.line);
    updateRunLabel();
  });
  window.addEventListener("pyb2d3-error", (e) => {
    showError(e.detail);
    if (pane.hidden) open();
  });
}
