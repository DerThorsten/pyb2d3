from pathlib import Path
import sys

this_dir = Path(__file__).resolve().parent
repo_root = this_dir.parent
companion_packages = repo_root / "companion_packages"
pyb2d3_sandbox = companion_packages / "pyb2d3_sandbox"

# add to sys.path
sys.path.insert(0, str(pyb2d3_sandbox))
