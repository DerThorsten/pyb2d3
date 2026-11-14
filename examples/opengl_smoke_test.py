"""Run every registered sample for a few frames in the real OpenGL frontend (``pixi run smoke-opengl``).

Catches errors the headless tests cannot: the OpenGL debug draw and the imgui widgets need a
window. Exceptions while stepping, drawing or showing a sample's widgets are recorded per
sample and the run moves on to the next one; exits with 1 if any sample failed.

    python examples/opengl_smoke_test.py [--frames N] [--category Restitution]
"""

import argparse
import sys
import traceback
from pathlib import Path

examples_dir = Path(__file__).resolve().parent
module_dir = examples_dir.parent / "src" / "module"
sys.path.insert(0, str(examples_dir))
if any((module_dir / "pyb2d3").glob("_pyb2d3*")):
    sys.path.insert(0, str(module_dir))

import pyb2d3_samples  # noqa: E402,F401  (registers the samples)
from pyb2d3_sandbox import registry, run_sample_browser  # noqa: E402
from pyb2d3_sandbox_opengl import OpenglFrontend  # noqa: E402


def make_driver(frames_per_sample, entries, errors, visited):
    class DriverFrontend(OpenglFrontend):
        """One physics step per frame, the next sample every `frames_per_sample` frames."""

        _frames = 0

        def _key(self):
            entry = registry.find(self.sample_class)
            return entry.key if entry else str(self.sample_class)

        def _guard(self, where, fn):
            try:
                fn()
            except Exception:
                key = self._key()
                if key not in errors:
                    errors[key] = f"[{where}]\n{traceback.format_exc()}"
                    print(f"ERROR in {key} ({where})", flush=True)
                self._frames = frames_per_sample  # move on

        def on_pre_new_frame(self):
            self._frames += 1
            if self._frames >= frames_per_sample:
                self._frames = 0
                key = self._key()
                if key not in visited:
                    visited.append(key)
                    print(f"{len(visited):3d}/{len(entries)} {key}", flush=True)
                if len(visited) >= len(entries):
                    self.runner_params.app_shall_exit = True
                    return
                self.next_sample()

            def step():
                self.update_frontend_logic()
                if self.sample is not None:
                    self.update_physics_single_step()

            self._guard("step", step)

        def once_per_frame(self):
            self._guard("draw", super().once_per_frame)

        def samples_ui_gui_function(self):
            self._guard("widgets", super().samples_ui_gui_function)

    return DriverFrontend


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frames", type=int, default=30, help="frames per sample (default 30)")
    parser.add_argument("--category", help="only the samples of this category, e.g. Restitution")
    args = parser.parse_args()

    # a category's samples are consecutive in the registry, so next_sample walks through them
    entries = [entry for entry in registry if args.category in (None, entry.category)]
    if not entries:
        sys.exit(f"no samples in category {args.category!r}, categories: {registry.categories()}")
    errors, visited = {}, []
    driver = make_driver(args.frames, entries, errors, visited)
    run_sample_browser(
        start=entries[0].key,
        frontend_class=driver,
        frontend_settings=driver.Settings(canvas_shape=(1400, 900)),
    )

    for key, text in errors.items():
        print(f"\n=== {key}\n{text}")
    print(f"\nvisited {len(visited)} of {len(entries)} samples, {len(errors)} with errors")
    return 1 if errors or len(visited) < len(entries) else 0


if __name__ == "__main__":
    sys.exit(main())
