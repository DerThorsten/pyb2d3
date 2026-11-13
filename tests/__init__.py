from pathlib import Path
import sys

this_dir = Path(__file__).resolve().parent
repo_root = this_dir.parent

# the sandbox, its frontends and the samples live in examples/ (not installed packages)
sys.path.insert(0, str(repo_root / "examples"))

# prefer an in-place build (cmake copies _pyb2d3 next to the python sources);
# otherwise the installed package is used
module_dir = repo_root / "src" / "module"
if any((module_dir / "pyb2d3").glob("_pyb2d3*")):
    sys.path.insert(0, str(module_dir))
