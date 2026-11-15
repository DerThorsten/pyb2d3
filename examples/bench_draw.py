"""Benchmark the drawing of many bodies in the real OpenGL frontend (``pixi run bench-draw``).

The OpenGL frontend draws with the same code as the browser sandbox (``GLDebugDraw`` +
``pyb2d3_sandbox_opengl/draw.py``), so changes to it are measured here. Runs the sample
"Batch API/Many Shapes" frozen (no physics steps) for every body count x shape type and
prints the time per frame of

* collect: ``world.draw`` -> box2d -> the python callbacks -> the ``add_*`` of draw.py
* upload:  ``GLDebugDraw.end_draw`` (instance arrays, upload, draw calls, ``glFinish``)

Needs a display (like ``pixi run smoke-opengl``).

    python examples/bench_draw.py [--counts 2000 5000] [--kinds mixed circles] [--frames 60] [--joints]
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

examples_dir = Path(__file__).resolve().parent
module_dir = examples_dir.parent / "src" / "module"
sys.path.insert(0, str(examples_dir))
if any((module_dir / "pyb2d3").glob("_pyb2d3*")):
    sys.path.insert(0, str(module_dir))

import pyb2d3_sandbox_opengl  # noqa: E402,F401  (first: PyOpenGL error checking off)
from OpenGL import GL as gl  # noqa: E402

import pyb2d3_samples  # noqa: E402,F401  (registers the samples)
from pyb2d3_samples.batch_many_shapes import SHAPE_TYPES  # noqa: E402
from pyb2d3_sandbox import run_sample_browser  # noqa: E402
from pyb2d3_sandbox_opengl import OpenglFrontend  # noqa: E402


def save_screenshot(path):
    """the current GL viewport (after drawing) as a PNG (visual check of the draw code)"""
    import numpy as np
    from PIL import Image

    x, y, w, h = (int(v) for v in gl.glGetIntegerv(gl.GL_VIEWPORT))
    gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
    data = gl.glReadPixels(x, y, w, h, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
    image = np.frombuffer(data, dtype=np.uint8).reshape(h, w, 3)[::-1]
    Image.fromarray(image).save(path)


def make_bench_frontend(configs, warmup, frames, results, joints=False, screenshot_dir=None):
    """an OpenglFrontend that runs every (count, kind) config and times its draws"""

    class BenchFrontend(OpenglFrontend):
        """walks through `configs`: set up, `warmup` frames, `frames` timed frames"""

        _config = -1
        _frame = 0
        _times = None

        def _next_config(self):
            """set up the next (count, kind) or exit when all are done"""
            self._config += 1
            if self._config >= len(configs):
                self.runner_params.app_shall_exit = True
                return
            count, kind = configs[self._config]
            s = self.sample
            s.count, s.kind, s.with_joints = count, kind, joints
            s.build()
            s.set_frozen(True)
            self.center_sample(10)
            self._frame = 0
            self._times = []

        def on_pre_new_frame(self):
            """count frames, switch configs (physics: frozen sample, nearly free)"""
            super().on_pre_new_frame()
            if self.sample is None:
                return
            if self._times is None:
                self._next_config()
                return
            self._frame += 1
            if self._frame == warmup + frames:
                results.append((*configs[self._config], self._times))
                self._next_config()

        def draw_physics(self):
            """FrontendBase.draw_physics, timed: collect (world.draw) / upload (end_draw)"""
            dd = self.debug_draw
            dd.begin_draw()
            self.sample.pre_debug_draw()
            t0 = time.perf_counter()
            self.draw_world()  # (C++ batch or per-shape callbacks, like the frontends)
            self.sample.post_debug_draw()
            t1 = time.perf_counter()
            dd.end_draw()
            gl.glFinish()
            t2 = time.perf_counter()
            if self._times is not None and self._frame >= warmup:
                self._times.append((t1 - t0, t2 - t1))
                if screenshot_dir is not None and self._frame == warmup:
                    count, kind = configs[self._config]
                    save_screenshot(
                        Path(screenshot_dir) / f"draw_{count}_{kind.replace(' ', '_')}.png"
                    )

    return BenchFrontend


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--counts", type=int, nargs="+", default=[2000, 5000, 10000])
    parser.add_argument("--kinds", nargs="+", default=SHAPE_TYPES, choices=SHAPE_TYPES)
    parser.add_argument("--frames", type=int, default=60, help="timed frames per config")
    parser.add_argument("--warmup", type=int, default=10, help="untimed frames per config")
    parser.add_argument(
        "--joints", action="store_true", help="link the bodies with joints (drawn too)"
    )
    parser.add_argument(
        "--screenshot", metavar="DIR", help="save the first timed frame of each config as PNG"
    )
    args = parser.parse_args()

    configs = [(count, kind) for count in args.counts for kind in args.kinds]
    results = []
    frontend = make_bench_frontend(
        configs, args.warmup, args.frames, results, args.joints, args.screenshot
    )
    run_sample_browser(
        start="Batch API/Many Shapes",
        frontend_class=frontend,
        frontend_settings=frontend.Settings(canvas_shape=(1400, 900)),
    )

    print(
        f"\n{'bodies':>7} {'shapes':<14} {'collect ms':>11} {'upload ms':>10} {'total ms':>9} {'us/body':>8}"
    )
    for count, kind, times in results:
        collect = statistics.median(t[0] for t in times) * 1000.0
        upload = statistics.median(t[1] for t in times) * 1000.0
        total = collect + upload
        print(
            f"{count:>7} {kind:<14} {collect:>11.2f} {upload:>10.2f} {total:>9.2f} {1000.0 * total / count:>8.2f}"
        )
    return 0 if len(results) == len(configs) else 1


if __name__ == "__main__":
    sys.exit(main())
