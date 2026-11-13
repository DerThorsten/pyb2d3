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
