# this file
from pathlib import Path
import sys
import os

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
    "jupyterlite_sphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for jupyterlite_sphinx ---------------------------------------------
jupyterlite_contents = ["../examples/notebooks/"]


#  WASM_ENV_PREFIX=$MAMBA_ROOT_PREFIX/envs/pyb2d3wasm
# get the env variable from the environment
mamba_root_prefix = os.environ.get("MAMBA_ROOT_PREFIX", "")
if not mamba_root_prefix:
    raise RuntimeError("The environment variable MAMBA_ROOT_PREFIX is not set. ")
wasm_env_name = "pyb2d3wasm"
wasm_env_prefix = os.path.join(mamba_root_prefix, "envs", wasm_env_name)

print("Using WASM environment prefix:", wasm_env_prefix)


jupyterlite_build_command_options = {"XeusAddon.prefix": wasm_env_prefix}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
