from pathlib import Path
import os
import sys

this_dir = Path(__file__).resolve().parent
repo_root = this_dir.parent

# the sandbox, its frontends and the samples live in examples/ (not installed packages)
sys.path.insert(0, str(repo_root / "examples"))

# prefer an in-place build (cmake copies _pyb2d3 next to the python sources); otherwise, or
# with PYB2D3_TEST_INSTALLED=1 (`pixi run test-installed`), the installed package is used
module_dir = repo_root / "src" / "module"
use_installed = os.environ.get("PYB2D3_TEST_INSTALLED", "0") not in ("", "0")
if not use_installed and any((module_dir / "pyb2d3").glob("_pyb2d3*")):
    sys.path.insert(0, str(module_dir))
