import numpy as np
import pyb2d3 as b2d
from pyb2d3 import ensure_hex_color, rgb_to_hex_color

from pyb2d3_sandbox.frontend_base import (
    FrontendDebugDraw,
)


X_AXIS = b2d.Vec2(1, 0)
Y_AXIS = b2d.Vec2(0, 1)

RED = rgb_to_hex_color(255, 0, 0)
GREEN = rgb_to_hex_color(0, 255, 0)


class Circles:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data_float = []
        self.data_int = [0]  # THE NUMBER OF ELEMENTS, TO BE CHANGED LATER

    def add(self, center, radius, color):
        assert radius > 0, "Radius must be greater than 0"
        self.data_float.extend([center[0], center[1], radius])
        self.data_int.append(color)

    def draw(self):
        self.data_int[0] = len(self.data_float) // 3  # Update the number of elements
        return np.array(self.data_float, dtype=np.float32), np.array(self.data_int, dtype=np.int32)


class SolidCircles:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data_float = []
        self.data_int = [0]

    def add(self, transform, radius, color):
        self.data_float.extend(
            [transform.p[0], transform.p[1], transform.q.s, transform.q.c, radius]
        )
        self.data_int.append(color)

    def draw(self):
        self.data_int[0] = len(self.data_float) // 5  # Update the number of elements
        return np.array(self.data_float, dtype=np.float32), np.array(self.data_int, dtype=np.int32)


class Polygons:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data_float = []
        self.data_int = [0]

    def add(self, points, color):
        self.data_float.extend(points.ravel())
        self.data_int.append(len(points))
        self.data_int.append(color)

    def draw(self):
        self.data_int[0] = (len(self.data_int) - 1) // 2
        if not self.data_float:
            return np.array([], dtype=np.float32), np.array(self.data_int, dtype=np.int32)
        return np.concatenate(self.data_float, dtype=np.float32, axis=0), np.array(
            self.data_int, dtype=np.int32
        )


class SolidPolygons:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data_float = []
        self.data_int = [0]

    def add(self, transform, points, radius, color):
        self.data_float.append(
            [
                radius,
                transform.p[0],
                transform.p[1],
                transform.q.s,
                transform.q.c,
            ]
        )
        # append the points as a flat array
        self.data_float.append(points.ravel())
        self.data_int.append(len(points))
        self.data_int.append(color)

    def draw(self):
        self.data_int[0] = (len(self.data_int) - 1) // 2
        if not self.data_float:
            return np.array([], dtype=np.float32), np.array(self.data_int, dtype=np.int32)
        return np.concatenate(self.data_float, dtype=np.float32, axis=0), np.array(
            self.data_int, dtype=np.int32
        )


class Segments:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data_float = []
        self.data_int = [0]

    def add(self, p1, p2, color):
        self.data_float.extend([p1[0], p1[1], p2[0], p2[1]])
        self.data_int.append(color)

    def draw(self):
        self.data_int[0] = len(self.data_int) - 1
        return np.array(self.data_float, dtype=np.float32), np.array(self.data_int, dtype=np.int32)


class SolidCapsules:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data_float = []
        self.data_int = [0]

    def add(self, p1, p2, radius, color):
        self.data_float.extend([p1[0], p1[1], p2[0], p2[1], radius])
        self.data_int.append(color)

    def draw(self):
        self.data_int[0] = len(self.data_int) - 1
        return np.array(self.data_float, dtype=np.float32), np.array(self.data_int, dtype=np.int32)


class Points:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.data_float = []
        self.data_int = [0]

    def add(self, p, size, color):
        self.data_float.extend([p[0], p[1], size])
        self.data_int.append(color)

    def draw(self):
        self.data_int[0] = len(self.data_int) - 1
        return np.array(self.data_float, dtype=np.float32), np.array(self.data_int, dtype=np.int32)


class JupyterDebugDraw(FrontendDebugDraw):
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

        self.all_things = [
            self.solid_circles,
            self.solid_polygons,
            self.solid_capsules,
            self.points,
            self.polygons,
            self.circles,
            self.segments,
        ]

    def reset(self):
        for thing in self.all_things:
            thing._reset()

    def begin_draw(self):
        # nothing to do here
        pass

    def end_draw(self):
        all_floats = [[self.transform.ppm, self.transform.offset[0], self.transform.offset[1]]]
        all_ints = [[0]]  # the mode
        for thing in self.all_things:
            floats, ints = thing.draw()
            if len(floats) > 0:
                all_floats.append(floats)
            if len(ints) > 0:
                all_ints.append(ints)

        all_floats = np.concatenate(all_floats, axis=0, dtype=np.float32)
        all_ints = np.concatenate(all_ints, axis=0, dtype=np.int32)

        self.canvas.send([all_ints, all_floats])

        for thing in self.all_things:
            thing._reset()

    def clear_canvas(self):
        # Clear the canvas by sending a message with mode 1
        self.canvas.send((np.array([1], dtype=np.int32),))

    def draw_polygon(self, points, color):
        self.polygons.add(points, ensure_hex_color(color))

    def draw_solid_polygon(self, transform, points, radius, color):
        self.solid_polygons.add(transform, points, radius, ensure_hex_color(color))

    def draw_circle(self, center, radius, color):
        self.circles.add(center, radius, ensure_hex_color(color))

    def draw_solid_circle(self, transform, radius, color):
        self.solid_circles.add(transform, radius, ensure_hex_color(color))

    def draw_solid_capsule(self, p1, p2, radius, color):
        self.solid_capsules.add(p1, p2, radius, ensure_hex_color(color))

    def draw_segment(self, p1, p2, color):
        self.segments.add(p1, p2, ensure_hex_color(color))

    def draw_transform(self, transform):
        pos = transform.p
        world_x_axis = pos + transform.transform_point(X_AXIS)
        world_y_axis = pos + transform.transform_point(Y_AXIS)

        self.segments.add(pos, world_x_axis, RED)
        self.segments.add(pos, world_y_axis, GREEN)

    def draw_point(self, p, size, color):
        self.points.add(p, size, ensure_hex_color(color))

    def draw_string(self, x, y, string):
        pass

    def draw_aabb(self, aabb, color):
        pass
