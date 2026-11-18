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

import doc_tools  # noqa: E402

doc_tools.fetch_sandbox_tour()
if QUICK:
    # the gallery page without rendering videos (missing ones are not shown)
    (docs_dir / "_static").mkdir(exist_ok=True)
    doc_tools.write_gallery(sample_videos_rst)
else:
    doc_tools.create_sample_videos()


def _paths(name):
    """the os.pathsep separated paths of an environment variable"""
    return [Path(p) for p in os.environ.get(name, "").split(os.pathsep) if p]


# the sandbox in the browser (pyjs + WebGL frontend) at <html root>/sandbox/,
# opened from the sample gallery (_static/sandbox_links.js): the local emscripten
# build of this commit (`pixi run emscripten` first, the docs workflow does), packed
# with numpy, openblas and PyOpenGL, pyjs in the page (see examples/web/build_page.py);
# PYB2D3_SANDBOX_PYJS: a local pyjs npm package dir (dist/ + assets/) instead
sys.path.insert(0, str(docs_dir.parent / "examples" / "web"))
import build_page  # noqa: E402

sandbox_extra = docs_dir / "_build" / "sandbox_extra"
_sandbox_pyjs = next(iter(_paths("PYB2D3_SANDBOX_PYJS")), None)
_sandbox_pyb2d3 = build_page.build(sandbox_extra / "sandbox", pyjs_dir=_sandbox_pyjs)
# which builds the page uses (a forgotten environment variable is easy to miss)
_pyjs_source = _sandbox_pyjs or f"npm {build_page.PYJS_VERSION}"
print(f"sandbox: pyjs from {_pyjs_source}, {_sandbox_pyb2d3.name}")
html_extra_path = [str(sandbox_extra)]


project = "pyb2d3"
copyright = "2025, Dr. Thorsten Beier"
author = "Dr. Thorsten Beier"

# import the package we want to document
import pyb2d3  # noqa: E402

version = release = getattr(pyb2d3, "__version__", "")


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


# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "alabaster"
html_static_path = ["_static"]
# the same icon as the browser sandbox (a tiny sandbox scene)
html_favicon = "../examples/web/favicon.svg"
html_js_files = ["sandbox_links.js"]
html_css_files = ["sandbox_links.css"]
