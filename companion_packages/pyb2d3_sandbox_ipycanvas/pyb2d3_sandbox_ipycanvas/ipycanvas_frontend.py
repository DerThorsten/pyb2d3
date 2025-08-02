from pyb2d3_sandbox.frontend_base import (
    FrontendBase,
    FrontendDebugDraw,
    MouseDownEvent,
    MouseUpEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    MouseLeaveEvent,
    MouseEnterEvent,
)
import sys

# output widget from ipywidgets
from ipywidgets import Output

# display from IPython
from IPython.display import display

import pyb2d3 as b2d
import numpy as np
import traceback

from ipycanvas.compat import Canvas
# from ipycanvas.call_repeated import set_render_loop


is_emscripten = sys.platform.startswith("emscripten")
if not is_emscripten:
    from ipyevents import Event

X_AXIS = b2d.Vec2(1.0, 0.0)
Y_AXIS = b2d.Vec2(0.0, 1.0)

from .render_loop import set_render_loop


def html_color(color):
    if isinstance(color, int):
        return "#{:06X}".format(color)
    elif isinstance(color, tuple) and len(color) == 3:
        return "rgb({}, {}, {})".format(*color)
    else:
        raise ValueError("Color must be an integer or a tuple of RGB values.")


def hex_to_rgb_array(hex_colors):
    """Convert a hexadecimal color (as integer) to an RGB array."""
    r = (hex_colors >> 16) & 0xFF
    g = (hex_colors >> 8) & 0xFF
    b = hex_colors & 0xFF
    return np.stack((r, g, b), axis=-1)


def ensure_hex(color):
    """Ensure color is a hex integer"""
    if isinstance(color, int):
        return color
    elif isinstance(color, tuple) and len(color) == 3:
        return b2d.rgb_to_hex_color(*color)
    else:
        raise ValueError("Color must be an int or a tuple of (R, G, B) values.")


class BatchPolygons:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset_lists()

    def _reset_lists(self):
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

        self._reset_lists()


class BatchSolidPolygons:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset_lists()

    def _reset_lists(self):
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

        self._reset_lists()


class BatchLines:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset_lists()

    def _reset_lists(self):
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

        self._reset_lists()


class BatchSolidCircles:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset_lists()

    def _reset_lists(self):
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

        self._reset_lists()


class BatchCircles:
    def __init__(self, canvas, transform):
        self.canvas = canvas
        self.transform = transform
        self._reset_lists()

    def _reset_lists(self):
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

        self._reset_lists()


class IpycanvasDebugDraw(FrontendDebugDraw):
    def __init__(self, transform, canvas, output_widget):
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
        self._batch_lines.add(
            world_pos, world_y_axis, color=0x00FF00
        )  # green for y-axis

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
        self._poor_mans_draw_solid_capsule(
            p1=p1, p2=p2, radius=radius, color=ensure_hex(color)
        )


last_frontend = [None]


class IpycanvasFrontend(FrontendBase):
    Settings = FrontendBase.Settings

    def __del__(self):
        if self.cancel_loop is not None:
            self.cancel_loop()

    def __init__(self, settings):
        global last_frontend
        try:
            super().__init__(settings)

            self.canvas = Canvas(
                width=self.settings.canvas_shape[0],
                height=self.settings.canvas_shape[1],
            )
            self.output_widget = Output()

            # if a cell is re-executed, we need to cancel the previous loop,
            # otherwise we will have multiple loops running
            if (
                last_frontend[0] is not None
                and last_frontend[0].cancel_loop is not None
            ):
                last_frontend[0].cancel_loop()
            last_frontend[0] = self

            self.transform = b2d.CanvasWorldTransform(
                canvas_shape=self.settings.canvas_shape,
                ppm=self.settings.ppm,
                offset=(0, 0),
            )

            self.debug_draw = IpycanvasDebugDraw(
                transform=self.transform,
                canvas=self.canvas,
                output_widget=self.output_widget,
            )
            self.debug_draw.draw_shapes = settings.debug_draw.draw_shapes
            self.debug_draw.draw_joints = settings.debug_draw.draw_joints

            self.cancel_loop = None

            self._last_canvas_mouse_pos = None

            # display the canvas
            display(self.canvas, self.output_widget)

            if not is_emscripten:
                # use ipyevents to handle  events
                d = Event(
                    source=self.canvas,
                    watched_events=[
                        "mouseenter",
                        "mousedown",
                        "mouseup",
                        "mousemove",
                        "wheel",
                        "mouseleave",
                    ],
                )
                d.on_dom_event(self._dispatch_events)
            else:
                raise NotImplementedError("lite is not yet finished..stay tuned!")
                self.canvas.on_mouse_move(self.on_mouse_move)
                self.canvas.on_mouse_down(self.on_mouse_down)
                self.canvas.on_mouse_up(self.on_mouse_up)
                self.canvas.on_mouse_out(self.on_mouse_leave)
                self.canvas.on_mouse_enter(self.on_mouse_enter)
        except Exception as e:
            self.output_widget.append_stdout(
                f"Exception in IpycanvasFrontend.__init__: {e}\n"
            )
            self.output_widget.append_stdout(traceback.format_exc())
            raise e

    def center_sample(self, margin_px=10):
        # center the sample in the canvas
        self.center_sample_with_transform(self.transform, margin_px)

    def drag_camera(self, delta):
        # drag the camera by the given delta
        self.transform.offset = (
            self.transform.offset[0] + delta[0],
            self.transform.offset[1] + delta[1],
        )

    def change_zoom(self, delta):
        _last_canvas_mouse_pos = self._last_canvas_mouse_pos
        if self._last_canvas_mouse_pos is None:
            # use center of canvas as mouse position
            _last_canvas_mouse_pos = b2d.Vec2(
                self.settings.canvas_shape[0] // 2,
                self.settings.canvas_shape[1] // 2,
            )
        current_mouse_world_pos = self.transform.canvas_to_world(_last_canvas_mouse_pos)

        # change the zoom by the given delta
        new_ppm = self.transform.ppm + delta
        if new_ppm > 0:
            self.transform.ppm = new_ppm

        # new mouse world position after zoom
        new_mouse_world_pos = self.transform.canvas_to_world(_last_canvas_mouse_pos)

        delta = (
            new_mouse_world_pos[0] - current_mouse_world_pos[0],
            new_mouse_world_pos[1] - current_mouse_world_pos[1],
        )
        # adjust the offset to keep the mouse position in the same place
        self.transform.offset = (
            self.transform.offset[0] + delta[0],
            self.transform.offset[1] + delta[1],
        )

    def main_loop(self):
        def f(dt):
            try:
                if self.sample.is_done():
                    self.cancel_loop()
                    self.sample.post_run()
                    return

                if self.settings.debug_draw.draw_background:
                    self.canvas.fill_style = html_color(
                        self.settings.debug_draw.background_color
                    )
                    self.canvas.fill_rect(
                        0,
                        0,
                        self.settings.canvas_shape[0],
                        self.settings.canvas_shape[1],
                    )
                else:
                    self.canvas.clear()

                self.update_and_draw(dt)
            except Exception:
                self.output_widget.append_stdout(
                    f"Error in main loop: {traceback.format_exc()}\n"
                )
                self.cancel_loop()

        self.cancel_loop = set_render_loop(self.canvas, f, fps=self.settings.fps)

    def _dispatch_events(self, event):
        try:
            if event["type"] == "mousemove":
                mouse_pos = b2d.Vec2(event["relativeX"], event["relativeY"])
                # get the delta \
                if self._last_canvas_mouse_pos is None:
                    self._last_canvas_mouse_pos = mouse_pos
                delta = mouse_pos - self._last_canvas_mouse_pos
                # convert delta to world coordinates
                world_delta = (
                    self.transform.scale_canvas_to_world(delta[0]),
                    -self.transform.scale_canvas_to_world(delta[1]),
                )
                self._last_canvas_mouse_pos = mouse_pos
                world_pos = self.transform.canvas_to_world(mouse_pos)
                self.sample.on_mouse_move(
                    MouseMoveEvent(
                        world_position=world_pos,
                        world_delta=world_delta,
                    )
                )

            elif event["type"] == "mouseenter":
                self.sample.on_mouse_enter(MouseEnterEvent())

            elif event["type"] == "mouseleave":
                self.sample.on_mouse_leave(MouseLeaveEvent())

            elif event["type"] == "mousedown":
                mouse_pos = b2d.Vec2(event["relativeX"], event["relativeY"])
                self._last_canvas_mouse_pos = mouse_pos
                world_pos = self.transform.canvas_to_world(mouse_pos)

                self._multi_click_handler.handle_click(world_position=world_pos)
                self.sample.on_mouse_down(MouseDownEvent(world_position=world_pos))
            elif event["type"] == "mouseup":
                canvas_pos = b2d.Vec2(event["relativeX"], event["relativeY"])
                world_pos = self.transform.canvas_to_world(canvas_pos)
                self.sample.on_mouse_up(MouseUpEvent(world_position=world_pos))

            elif event["type"] == "wheel":
                canvas_pos = b2d.Vec2(event["relativeX"], event["relativeY"])
                world_pos = self.transform.canvas_to_world(canvas_pos)
                self.sample.on_mouse_wheel(
                    MouseWheelEvent(
                        world_position=world_pos,
                        delta=-event["deltaY"] / 30.0,
                    )
                )

        except Exception as e:
            self.output_widget.append_stdout(f"Exception in event handler: {e}\n")
            self.output_widget.append_stdout(traceback.format_exc())
            self.cancel_loop()
