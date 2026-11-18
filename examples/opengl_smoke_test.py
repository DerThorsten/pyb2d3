"""Run every registered sample for a few frames in the real OpenGL frontend (``pixi run smoke-opengl``).

Catches errors the headless tests cannot: the OpenGL debug draw and the imgui widgets need a
window. Exceptions while stepping, drawing or showing a sample's widgets are recorded per
sample and the run moves on to the next one; exits with 1 if any sample failed.

    python examples/opengl_smoke_test.py [--frames N] [--category Restitution]
    python examples/opengl_smoke_test.py --record smoke.mp4   # a screencast of the canvas

--record writes every frame of the simulation view (not the panel) into an mp4 (ffmpeg,
h264, 60 fps, 720 px wide): the sandbox tour on the docs' start page (`pixi run smoke-video`,
then `gh release upload media build/sandbox_tour.mp4 --clobber`; the docs download it).
"""

import argparse
import subprocess
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

        def panel_gui_function(self):
            self._guard("panel", super().panel_gui_function)

    return DriverFrontend


class Recorder:
    """The simulation view of every frame into an mp4: the area is taken while the view is
    drawn (`canvas`), the pixels just before the window is shown (incl. the samples' text,
    which imgui draws). Starts once the layout has settled (the panel docks first)."""

    def __init__(self, path, width=720):
        self.path, self.width = path, width
        self.rect = None  # x, top, width, height of the view in window pixels
        self.size, self.stable, self.encoder = None, 0, None

    def canvas(self):
        """call inside the simulation window: remember its area below the tab bar"""
        from imgui_bundle import imgui

        pos, size = imgui.get_window_pos(), imgui.get_window_size()
        bar = int(imgui.get_frame_height())
        self.rect = (int(pos.x), int(pos.y) + bar, int(size.x), int(size.y) - bar)

    def capture(self):
        """hello_imgui's before_swap callback: the view's pixels into ffmpeg"""
        from OpenGL import GL as gl

        if self.rect is None:
            return
        x, top, w, h = self.rect
        w, h = w - w % 2, h - h % 2  # h264 wants even sizes
        if self.encoder is None:
            self.stable = self.stable + 1 if self.size == (w, h) else 0
            self.size = (w, h)
            if self.stable < 10:
                return
            self.encoder = subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24"]
                + ["-s", f"{w}x{h}", "-r", "60", "-i", "-", "-vf", f"vflip,scale={self.width}:-2"]
                + ["-c:v", "libx264", "-crf", "28", "-pix_fmt", "yuv420p", str(self.path)],
                stdin=subprocess.PIPE,
            )
        if (w, h) != self.size:
            return  # the window was resized: the video keeps its size
        display_h = int(gl.glGetIntegerv(gl.GL_VIEWPORT)[3])
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
        self.encoder.stdin.write(
            gl.glReadPixels(x, display_h - (top + h), w, h, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        )

    def close(self):
        if self.encoder is not None:
            self.encoder.stdin.close()
            self.encoder.wait()
            print(f"recorded {self.path}")


def recording(driver, recorder):
    """`driver` with every frame of its simulation view recorded"""

    class RecordingFrontend(driver):
        def main_loop(self):
            self.runner_params.callbacks.before_swap = recorder.capture
            super().main_loop()

        def once_per_frame(self):
            recorder.canvas()
            super().once_per_frame()

    return RecordingFrontend


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frames", type=int, default=30, help="frames per sample (default 30)")
    parser.add_argument("--category", help="only the samples of this category, e.g. Restitution")
    parser.add_argument("--record", type=Path, metavar="MP4", help="record the canvas into a video")
    args = parser.parse_args()

    # a category's samples are consecutive in the registry, so next_sample walks through them
    entries = [entry for entry in registry if args.category in (None, entry.category)]
    if not entries:
        sys.exit(f"no samples in category {args.category!r}, categories: {registry.categories()}")
    errors, visited = {}, []
    driver = make_driver(args.frames, entries, errors, visited)
    recorder = Recorder(args.record) if args.record else None
    if recorder:
        driver = recording(driver, recorder)
    run_sample_browser(
        start=entries[0].key,
        frontend_class=driver,
        frontend_settings=driver.Settings(canvas_shape=(1400, 900)),
    )
    if recorder:
        recorder.close()

    for key, text in errors.items():
        print(f"\n=== {key}\n{text}")
    print(f"\nvisited {len(visited)} of {len(entries)} samples, {len(errors)} with errors")
    return 1 if errors or len(visited) < len(entries) else 0


if __name__ == "__main__":
    sys.exit(main())
