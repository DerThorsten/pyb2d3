# this file
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parent))

# prefer an in-place build (cmake copies _pyb2d3 next to the python sources)
_module_dir = Path(__file__).resolve().parent.parent / "src" / "module"
if any((_module_dir / "pyb2d3").glob("_pyb2d3*")):
    sys.path.insert(0, str(_module_dir))

# PYB2D3_DOCS_QUICK=1: skip rendering the sample videos,
# e.g. to check the pages locally: PYB2D3_DOCS_QUICK=1 sphinx-build -b html docs docs/_build
QUICK = os.environ.get("PYB2D3_DOCS_QUICK", "0") not in ("", "0")

docs_dir = Path(__file__).resolve().parent
sample_videos_rst = docs_dir / "src" / "samples" / "sample_videos.rst"

if QUICK:
    (docs_dir / "_static").mkdir(exist_ok=True)
    if not sample_videos_rst.exists():
        sample_videos_rst.write_text("(sample videos are not built in quick mode)\n")
else:
    import doc_tools

    # create sample videos
    doc_tools.create_sample_videos()


def _paths(name):
    """the os.pathsep separated paths of an environment variable"""
    return [Path(p) for p in os.environ.get(name, "").split(os.pathsep) if p]


# the sandbox in the browser (pyjs + WebGL frontend) at <html root>/sandbox/,
# opened from the sample gallery (_static/sandbox_links.js). pyb2d3 is the
# local emscripten build of this commit (`pixi run emscripten` first, the docs
# workflow does), pyjs comes from jsDelivr, the other conda packages from
# emscripten-forge. Overrides:
#   PYB2D3_SANDBOX_PYJS        a local pyjs npm package dir (dist/ + assets/)
#   PYB2D3_SANDBOX_LOCAL_PKGS  local conda packages (.tar.bz2), packed into the page
#                              (replaces the default: the local pyb2d3 build)
#   PYB2D3_SANDBOX_CHANNELS    local conda channels, copied into the page
sys.path.insert(0, str(docs_dir.parent / "examples" / "web"))
import build_page  # noqa: E402

def _local_pyb2d3_build():
    """the newest emscripten build of this version of pyb2d3 (`pixi run emscripten`,
    emscripten_forge/output), or None: the sandbox runs the code of this commit"""
    import tomllib

    pyproject = tomllib.loads((docs_dir.parent / "pyproject.toml").read_text())
    version = pyproject["project"]["version"]
    output = docs_dir.parent / "emscripten_forge" / "output" / "emscripten-wasm32"
    builds = sorted(output.glob(f"pyb2d3-{version}-*.tar.bz2"), key=lambda p: p.stat().st_mtime)
    if not builds:
        print(f"sandbox: WARNING no local emscripten build of pyb2d3 {version} in {output} "
              "(pixi run emscripten): the page installs the published pyb2d3")
    return builds[-1] if builds else None


sandbox_extra = docs_dir / "_build" / "sandbox_extra"
_sandbox_pyjs = next(iter(_paths("PYB2D3_SANDBOX_PYJS")), None)
if "PYB2D3_SANDBOX_LOCAL_PKGS" in os.environ:
    _sandbox_local_pkgs = _paths("PYB2D3_SANDBOX_LOCAL_PKGS")
else:
    _sandbox_local_pkgs = [p for p in [_local_pyb2d3_build()] if p is not None]
build_page.build(
    sandbox_extra / "sandbox",
    pyjs_dir=_sandbox_pyjs,
    pyjs_url=build_page.DEFAULT_PYJS_URL,
    channels=_paths("PYB2D3_SANDBOX_CHANNELS"),
    packages=build_page.CONDA_PACKAGES,
    local_pkgs=_sandbox_local_pkgs,
)
# which builds the page uses (a forgotten environment variable is easy to miss)
print(f"sandbox: pyjs from {_sandbox_pyjs or build_page.DEFAULT_PYJS_URL}")
print(f"sandbox: local packages: {[p.name for p in _sandbox_local_pkgs] or 'none (all from the channels)'}")
html_extra_path = [str(sandbox_extra)]


project = "pyb2d3"
copyright = "2025, Dr. Thorsten Beier"
author = "Dr. Thorsten Beier"

# import the package we want to document
import pyb2d3  # noqa: E402

version = release = getattr(pyb2d3, "__version__", "")


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    # video from contrib
    "sphinxcontrib.video",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "snippets"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
html_js_files = ["sandbox_links.js"]
html_css_files = ["sandbox_links.css"]
