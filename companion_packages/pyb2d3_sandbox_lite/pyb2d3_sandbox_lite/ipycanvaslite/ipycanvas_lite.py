from .offscreen_canvas import OffscreenCanvas
from contextlib import contextmanager
import pyjs
import numpy as np

from pathlib import Path


@contextmanager
def _no_ctx():
    yield None


def _managed_attribute(js_name):
    @property
    def prop(self):
        return getattr(self._ctx, js_name)

    @prop.setter
    def prop(self, value):
        setattr(self._ctx, js_name, value)

    return prop


@contextmanager
def hold_canvas(canvas):
    yield None


def _exec_js_file(filename):
    try:
        with open(filename, "r") as f:
            js_code = f.read()

        pyjs.js.Function(js_code)()
    except Exception as e:
        raise RuntimeError(f"Error executing JavaScript file {filename}: {e}") from e


def _extend_js():
    THIS_DIR = Path(__file__).parent
    # get parent dir of THIS_DIR
    PARENT = THIS_DIR.parent

    _exec_js_file(PARENT / "init.js")


_extend_js()
del _extend_js


# class LinearGradient(object):
#     def __init__(self, x0, y0, x1, y1):
#         self.x0 = x0
#         self.y0 = y0
#         self.x1 = x1
#         self.y1 = y1

#     def add_color_stop(self, offset, color):
#         pass


class Canvas(OffscreenCanvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        initial_buffer_size = 10
        n_buffers = 7  # max number of args / buffers we need at the same time
        self._buffers = [np.zeros(initial_buffer_size, dtype=np.float32) for _ in range(n_buffers)]
        self._js_buffers = [
            pyjs.buffer_to_js_typed_array(fbuffer, view=True) for fbuffer in self._buffers
        ]

    def _ensure_size(self, index, size):
        buffer_size = len(self._buffers[index])
        if size > buffer_size:
            # resize the buffer
            new_size = max(size, buffer_size * 2)
            new_buffer = np.zeros(new_size, dtype=np.float32)
            self._buffers[index] = new_buffer
            self._js_buffers[index] = pyjs.buffer_to_js_typed_array(new_buffer, view=True)

    def _points_to_buffer(self, index, points):
        """Convert a list of points to a float buffer."""
        points = np.require(points, requirements="C", dtype=np.float32)
        n_points = int(points.shape[0])
        n_points2 = 2 * n_points
        self._ensure_size(index, n_points2)
        self._buffers[index][:n_points2] = points.flatten()
        return n_points

    async def _ready(self):
        await super()._ready()
        self._ctx = self._canvas.getContext("2d")

    async def adisplay(self, *args, **kwargs):
        await super().adisplay(*args, **kwargs)
        self._ctx = self._canvas.getContext("2d")
