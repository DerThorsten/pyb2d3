"""Run the sample browser from a checkout (``pixi run sandbox``).

    python examples/sandbox.py                          # first sample, default frontend
    python examples/sandbox.py "Joints/Ragdoll"         # start at a sample
    python examples/sandbox.py --frontend pygame
    python examples/sandbox.py --list                   # all samples

Uses the in-place build (``cmake --build build``) if there is one, else the installed pyb2d3.
"""

import argparse
import os
import sys
from pathlib import Path

examples_dir = Path(__file__).resolve().parent
module_dir = examples_dir.parent / "src" / "module"

sys.path.insert(0, str(examples_dir))
if any((module_dir / "pyb2d3").glob("_pyb2d3*")):
    sys.path.insert(0, str(module_dir))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("sample", nargs="?", default="", help='start sample, e.g. "Games/Billiard"')
    parser.add_argument("--frontend", choices=["opengl", "pygame"], help="default: opengl if available")
    parser.add_argument("--list", action="store_true", help="list the samples and exit")
    args = parser.parse_args()

    if args.frontend:
        os.environ["PYB2D3_SANDBOX_DEFAULT_FRONTEND"] = args.frontend

    import pyb2d3_samples  # noqa: F401  (registers the samples)
    from pyb2d3_sandbox import registry, run_sample_browser

    if args.list:
        for entry in registry:
            print(entry.key)
        return
    run_sample_browser(start=args.sample or None)


if __name__ == "__main__":
    main()
