"""Browse all registered samples: ``python -m pyb2d3_samples [Category/Name]``."""

import sys

import pyb2d3_samples  # noqa: F401  (registers the samples)
from pyb2d3_sandbox import run_sample_browser

if __name__ == "__main__":
    run_sample_browser(start=sys.argv[1] if len(sys.argv) > 1 else None)
