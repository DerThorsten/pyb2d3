# this file
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doc_tools


# create sample videos
doc_tools.create_sample_videos()


project = "pyb2d3"
copyright = "2025, Dr. Thorsten Beier"
author = "Dr. Thorsten Beier"
release = "0.5.6"

# import the package we want to document


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # 'sphinx_rtd_theme',
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    # video from contrib
    "sphinxcontrib.video",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
