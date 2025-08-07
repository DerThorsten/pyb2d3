import pyjs
from pathlib import Path
import numpy as np
import pyb2d3 as b2d

from pyb2d3_sandbox.frontend_base import (
    FrontendDebugDraw,
)


THIS_DIR = Path(__file__).parent


X_AXIS = b2d.Vec2(1, 0)
Y_AXIS = b2d.Vec2(0, 1)


# execute the init.js file to initialize the js environment
def _init_js():
    # helper function to execute a javascript file.
    def exec_js_file(filename):
        try:
            with open(filename, "r") as f:
                js_code = f.read()

            pyjs.js.Function(js_code)()
        except Exception as e:
            raise RuntimeError(f"Error executing JavaScript file {filename}: {e}") from e

    THIS_DIR = Path(__file__).parent
    exec_js_file(THIS_DIR / "init.js")


_init_js()
del _init_js


class Circles:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data = []

    def add(self, center, radius, color):
        assert radius > 0, "Radius must be greater than 0"
        self.data.extend([center[0], center[1], radius, color])

    def draw(self):
        if not self.data:
            return
        nd = np.array(self.data, dtype=np.float32)
        jnd = pyjs.buffer_to_js_typed_array(nd)
        self.canvas._ctx._draw_circles(jnd)
        self._reset()


def ensure_hex(color):
    """Ensure color is a hex integer"""
    if isinstance(color, int):
        return color
    elif isinstance(color, tuple) and len(color) == 3:
        return b2d.rgb_to_hex_color(*color)
    else:
        raise ValueError("Color must be an int or a tuple of (R, G, B) values.")


class SolidCircles:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data = []

    def add(self, transform, radius, color):
        self.data.extend(
            [transform.p[0], transform.p[1], transform.q.s, transform.q.c, radius, color]
        )

    def draw(self):
        if not self.data:
            return
        nd = np.array(self.data, dtype=np.float32)
        jnd = pyjs.buffer_to_js_typed_array(nd)
        self.canvas._ctx._draw_solid_circles(jnd)
        self._reset()


class Polygons:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data = []

    def add(self, points, color):
        self.data.append([len(points), color])
        self.data.append(points.ravel())

    def draw(self):
        if not self.data:
            return
        nd = np.concatenate(self.data, axis=0)
        n_polygons = len(self.data) // 2
        jnd = pyjs.buffer_to_js_typed_array(nd)
        self.canvas._ctx._draw_polygons(n_polygons, jnd)
        self._reset()


class SolidPolygons:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data = []

    def add(self, transform, points, radius, color):
        self.data.append(
            [
                len(points),
                radius,
                color,
                transform.p[0],
                transform.p[1],
                transform.q.s,
                transform.q.c,
            ]
        )
        # append the points as a flat array
        self.data.append(points.ravel())

    def draw(self):
        if not self.data:
            return
        nd = np.concatenate(self.data, axis=0)
        jnd = pyjs.buffer_to_js_typed_array(nd)
        n_polygons = len(self.data) // 2
        self.canvas._ctx._draw_solid_polygons(n_polygons, jnd)
        self._reset()


class Segments:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data = []

    def add(self, p1, p2, color):
        self.data.extend([p1[0], p1[1], p2[0], p2[1], color])

    def draw(self):
        if not self.data:
            return
        nd = np.array(self.data, dtype=np.float32)
        jnd = pyjs.buffer_to_js_typed_array(nd)
        self.canvas._ctx._draw_segments(jnd)
        self._reset()


class SolidCapsules:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data = []

    def add(self, p1, p2, radius, color):
        self.data.extend([p1[0], p1[1], p2[0], p2[1], radius, color])

    def draw(self):
        if not self.data:
            return
        nd = np.array(self.data, dtype=np.float32)
        jnd = pyjs.buffer_to_js_typed_array(nd)
        self.canvas._ctx._draw_solid_capsules(jnd)
        self._reset()


class Points:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data = []

    def add(self, p, size, color):
        self.data.extend([p[0], p[1], size, color])

    def draw(self):
        if not self.data:
            return
        nd = np.array(self.data, dtype=np.float32)
        jnd = pyjs.buffer_to_js_typed_array(nd)
        self.canvas._ctx._draw_points(jnd)
        self._reset()


class IpycanvasDebugDraw(FrontendDebugDraw):
    def __init__(self, frontend, transform, canvas, output_widget):
        self.frontend = frontend
        self.transform = transform
        self.canvas = canvas
        self.output_widget = output_widget
        self.transform = transform
        super().__init__()

        self.solid_circles = SolidCircles(self.canvas, self.transform)
        self.solid_polygons = SolidPolygons(self.canvas, self.transform)
        self.solid_capsules = SolidCapsules(self.canvas, self.transform)
        self.points = Points(self.canvas, self.transform)

        self.polygons = Polygons(self.canvas, self.transform)
        self.circles = Circles(self.canvas, self.transform)
        self.segments = Segments(self.canvas, self.transform)

    def reset(self):
        self.solid_circles._reset()
        self.solid_polygons._reset()
        self.solid_capsules._reset()
        self.points._reset()

        self.polygons._reset()
        self.circles._reset()
        self.segments._reset()

    def begin_draw(self):
        self.canvas._ctx._begin_draw(
            self.transform.ppm,
            self.transform.offset[0],
            self.transform.offset[1],
        )

    def end_draw(self):
        self.solid_circles.draw()
        self.solid_polygons.draw()
        self.solid_capsules.draw()
        self.circles.draw()
        self.polygons.draw()
        self.segments.draw()
        self.points.draw()

        self.canvas._ctx._end_draw()

    def draw_polygon(self, points, color):
        self.polygons.add(points, ensure_hex(color))

    def draw_solid_polygon(self, transform, points, radius, color):
        self.solid_polygons.add(transform, points, radius, ensure_hex(color))

    def draw_circle(self, center, radius, color):
        self.circles.add(center, radius, ensure_hex(color))

    def draw_solid_circle(self, transform, radius, color):
        self.solid_circles.add(transform, radius, ensure_hex(color))

    def draw_solid_capsule(self, p1, p2, radius, color):
        self.solid_capsules.add(p1, p2, radius, ensure_hex(color))

    def draw_segment(self, p1, p2, color):
        self.segments.add(p1, p2, ensure_hex(color))

    def draw_transform(self, transform):
        pos = transform.p
        world_x_axis = pos + transform.transform_point(X_AXIS)
        world_y_axis = pos + transform.transform_point(Y_AXIS)

        self.segments.add(pos, world_x_axis, b2d.rgb_to_hex_color(255, 0, 0))
        self.segments.add(pos, world_y_axis, b2d.rgb_to_hex_color(0, 255, 0))

    def draw_point(self, p, size, color):
        self.points.add(p, size, ensure_hex(color))

    def draw_string(self, x, y, string):
        pass

    def draw_aabb(self, aabb, color):
        pass
