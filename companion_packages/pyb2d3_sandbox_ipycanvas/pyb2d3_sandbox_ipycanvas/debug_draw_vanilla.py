from pyb2d3_sandbox.frontend_base import (
    FrontendDebugDraw,
)


# output widget from ipywidgets

# display from IPython

import pyb2d3 as b2d
import numpy as np


X_AXIS = b2d.Vec2(1.0, 0.0)
Y_AXIS = b2d.Vec2(0.0, 1.0)


def ensure_hex(color):
    """Ensure color is a hex integer"""
    if isinstance(color, int):
        return color
    elif isinstance(color, tuple) and len(color) == 3:
        return b2d.rgb_to_hex_color(*color)
    else:
        raise ValueError("Color must be an int or a tuple of (R, G, B) values.")


def hex_to_rgb_array(hex_colors):
    """Convert a hexadecimal color (as integer) to an RGB array."""
    r = (hex_colors >> 16) & 0xFF
    g = (hex_colors >> 8) & 0xFF
    b = hex_colors & 0xFF
    return np.stack((r, g, b), axis=-1)


class BatchPolygons:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.points = []
        self.colors = []
        self.sizes = []

    def add(self, points, color):
        self.points.append(points)
        self.colors.append(color)
        self.sizes.append(len(points))

    def draw(self):
        if not self.points:
            return

        points = np.concatenate(self.points)
        points = self.transform.batch_world_to_canvas(points)
        colors = hex_to_rgb_array(np.array(self.colors))

        self.canvas.line_width = 1
        self.canvas.stroke_styled_polygons(
            points=points,
            color=colors,
            points_per_polygon=self.sizes,
        )

        self._reset()


class BatchSolidPolygons:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.points = []
        self.colors = []
        self.sizes = []

    def add(self, points, color):
        self.points.append(points)
        self.colors.append(color)
        self.sizes.append(len(points))

    def draw(self):
        if not self.points:
            return

        points = np.concatenate(self.points)
        points = self.transform.batch_world_to_canvas(points)
        colors = hex_to_rgb_array(np.array(self.colors))

        self.canvas.fill_styled_polygons(
            points=points,
            color=colors,
            points_per_polygon=self.sizes,
        )

        self._reset()


class BatchLines:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.points = []
        self.colors = []

    def add(self, p1, p2, color):
        self.points.append((p1, p2))
        self.colors.append(color)

    def draw(self):
        if not self.points:
            return

        points = np.array(self.points)
        points = self.transform.batch_world_to_canvas(points.reshape(-1, 2))
        colors = hex_to_rgb_array(np.array(self.colors))

        self.canvas.line_width = 1
        self.canvas.stroke_styled_line_segments(
            points=points,
            color=colors,
            points_per_line_segment=np.ones(len(self.points), dtype=np.int32) * 2,
        )

        self._reset()


class BatchSolidCircles:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.centers = []
        self.radii = []
        self.colors = []

    def add(self, center, radius, color):
        self.centers.append(center)
        self.radii.append(radius)
        self.colors.append(color)

    def draw(self):
        if not self.centers:
            return

        centers = np.array(self.centers)
        radii = np.array(self.radii)
        colors = hex_to_rgb_array(np.array(self.colors))

        centers = self.transform.batch_world_to_canvas(centers)

        self.canvas.fill_styled_circles(
            x=centers[:, 0],
            y=centers[:, 1],
            radius=radii * self.transform.ppm,
            color=colors,
        )

        self._reset()


class BatchCircles:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset()

    def _reset(self):
        self.centers = []
        self.radii = []
        self.colors = []

    def add(self, center, radius, color):
        self.centers.append(center)
        self.radii.append(radius)
        self.colors.append(color)

    def draw(self):
        if not self.centers:
            return

        centers = np.array(self.centers)
        radii = np.array(self.radii) * self.transform.ppm
        colors = hex_to_rgb_array(np.array(self.colors))

        centers = self.transform.batch_world_to_canvas(centers)

        self.canvas.stroke_styled_circles(
            x=centers[:, 0], y=centers[:, 1], radius=radii, color=colors
        )

        self._reset()


class IpycanvasDebugDraw(FrontendDebugDraw):
    def __init__(self, frontend, transform, canvas, output_widget):
        self.frontend = frontend
        self.canvas = canvas
        self.output_widget = output_widget

        self.transform = transform
        super().__init__()

        self._in_debug_draw = False

        self._batch_polygons = BatchPolygons(canvas, transform)
        self._batch_solid_polygons = BatchSolidPolygons(canvas, transform)
        self._batch_lines = BatchLines(canvas, transform)
        self._batch_solid_circles = BatchSolidCircles(canvas, transform)
        self._batch_circles = BatchCircles(canvas, transform)

    def reset(self):
        self._batch_polygons._reset()
        self._batch_solid_polygons._reset()
        self._batch_lines._reset()
        self._batch_solid_circles._reset()
        self._batch_circles._reset()

    def world_to_canvas(self, world_point):
        return self.transform.world_to_canvas(world_point)

    def begin_draw(self):
        self._in_debug_draw = True

    def end_draw(self):
        self._in_debug_draw = False

        self._batch_solid_polygons.draw()
        self._batch_solid_circles.draw()
        self._batch_circles.draw()
        self._batch_lines.draw()
        self._batch_polygons.draw()

    def draw_polygon(self, points, color):
        self.output_widget.append_stdout(
            f"Drawing polygon with {len(points)} points and color {color}\n"
        )
        self._batch_polygons.add(points, ensure_hex(color))

    def draw_solid_polygon(self, transform, points, radius, color):
        # self.output_widget.append_stdout(
        #     f"Drawing solid polygon with {len(points)} points, radius {radius}, and color {color}\n"
        # )
        color = ensure_hex(color)
        if radius <= 0:
            world_points = [transform.transform_point(v) for v in points]
            self._batch_solid_polygons.add(world_points, color)
        else:
            # this has really bad performance. A better way should be implemented
            self._poor_mans_draw_solid_rounded_polygon(
                points=points, transform=transform, radius=radius, color=color
            )

    def draw_circle(self, center, radius, color):
        self._batch_circles.add(center, radius, ensure_hex(color))

    def draw_solid_circle(self, transform, radius, color):
        self._batch_solid_circles.add(transform.p, radius, ensure_hex(color))

    def draw_transform(self, transform):
        world_pos = transform.p
        world_x_axis = world_pos + transform.transform_point(X_AXIS)
        world_y_axis = world_pos + transform.transform_point(Y_AXIS)
        self._batch_lines.add(world_pos, world_x_axis, color=0xFF0000)  # red for x-axis
        self._batch_lines.add(world_pos, world_y_axis, color=0x00FF00)  # green for y-axis

    def draw_point(self, p, size, color):
        pass
        # # here size is is in **PIXEL** coordinates.
        # # so we need to inflate it to world coordinates (st. we can use the same batch)
        # world_radius = (size / self.transform.ppm) / 2  # radius in world coordinates
        # self._batch_circles.add(p, world_radius, ensure_hex(color))

    def draw_segment(self, p1, p2, color):
        # Draw a line segment between two points
        self._batch_lines.add(p1, p2, ensure_hex(color))

    def draw_solid_capsule(self, p1, p2, radius, color):
        self._poor_mans_draw_solid_capsule(p1=p1, p2=p2, radius=radius, color=ensure_hex(color))
