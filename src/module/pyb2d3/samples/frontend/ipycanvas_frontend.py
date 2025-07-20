from .frontend_base import FrontendBase
import sys

is_emscripten = sys.platform.startswith("emscripten")
if not is_emscripten:
    from ipyevents import Event


import pyb2d3 as b2d
import time
import sys
import numpy as np
import traceback

from ...debug_draw import DebugDraw
from ..._pyb2d3 import transform_point
import math

from ipycanvas.compat import Canvas
from ipycanvas.call_repeated import set_render_loop

# display from IPython
from IPython.display import display

# output widget from ipywidgets
from ipywidgets import Output


def html_color(color):
    if isinstance(color, int):
        return "#{:06X}".format(color_int)
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


class IpycanvasDebugDraw(DebugDraw):
    def __init__(self, transform, canvas, output_widget):
        self.canvas = canvas
        self.output_widget = output_widget

        self.transform = transform
        super().__init__()

        self._in_debug_draw = False

        self._draw_polygon_points = []
        self._draw_polygon_sizes = []
        self._draw_polygon_colors = []
        self._draw_polygon_line_widths = []
        self._draw_polygon_width_in_pixels = []
        self._draw_solid_polygon_points = []

        self._draw_solid_polygon_points = []
        self._draw_solid_polygon_sizes = []
        self._draw_solid_polygon_colors = []

        self._draw_circle_centers = []
        self._draw_circle_radii = []
        self._draw_circle_colors = []
        self._draw_circle_line_widths = []
        self._draw_circle_width_in_pixels = []

        self._draw_solid_circle_centers = []
        self._draw_solid_circle_radii = []
        self._draw_solid_circle_colors = []

        self._draw_line_points = []
        self._draw_line_colors = []
        self._draw_line_widths = []
        self._draw_line_width_in_pixels = []

    def world_to_canvas(self, world_point):
        return self.transform.world_to_canvas(world_point)

    def begin_draw(self):

        self._in_debug_draw = True

    def end_draw(self):
        self._in_debug_draw = False

        # draw solid polygons
        solid_polygon_points = np.concatenate(self._draw_solid_polygon_points)
        solid_polygon_points = self.transform.batch_world_to_canvas(
            solid_polygon_points
        )
        solid_polygon_colors = hex_to_rgb_array(
            np.array(self._draw_solid_polygon_colors)
        )

        self.canvas.fill_styled_polygons(
            points=solid_polygon_points,
            color=solid_polygon_colors,
            points_per_polygon=self._draw_solid_polygon_sizes,
        )

        # clear the lists
        self._draw_polygon_points = []
        self._draw_polygon_sizes = []
        self._draw_polygon_colors = []
        self._draw_polygon_line_widths = []
        self._draw_polygon_width_in_pixels = []
        self._draw_solid_polygon_points = []

        self._draw_solid_polygon_points = []
        self._draw_solid_polygon_sizes = []
        self._draw_solid_polygon_colors = []

        self._draw_circle_centers = []
        self._draw_circle_radii = []
        self._draw_circle_colors = []
        self._draw_circle_line_widths = []
        self._draw_circle_width_in_pixels = []

        self._draw_solid_circle_centers = []
        self._draw_solid_circle_radii = []
        self._draw_solid_circle_colors = []

        self._draw_line_points = []
        self._draw_line_colors = []
        self._draw_line_widths = []
        self._draw_line_width_in_pixels = []

    def draw_polygon(self, points, color, line_width, width_in_pixels=False):
        if self._in_debug_draw:
            self._draw_polygon_points.append(points)
            self._draw_polygon_sizes.append(len(points))
            self._draw_polygon_colors.append(color)
            self._draw_polygon_line_widths.append(line_width)
            self._draw_polygon_width_in_pixels.append(width_in_pixels)
        else:
            self.canvas.stroke_style = html_color(color)
            if not width_in_pixels:
                line_width = self.transform.scale_world_to_canvas(line_width)
            self.canvas.line_width = line_width
            self.canvas.stroke_polygon([self.world_to_canvas(v) for v in points])

    def draw_solid_polygon(self, points, color):
        if self._in_debug_draw:
            self._draw_solid_polygon_points.append(points)
            self._draw_solid_polygon_sizes.append(len(points))
            self._draw_solid_polygon_colors.append(color)
        else:
            self.canvas.fill_style = html_color(color)
            self.canvas.fill_polygon([self.world_to_canvas(v) for v in points])

    def draw_circle(self, center, radius, line_width, color, width_in_pixels=False):
        if self._in_debug_draw:
            self._draw_circle_centers.append(center)
            self._draw_circle_radii.append(radius)
            self._draw_circle_colors.append(color)
            self._draw_circle_line_widths.append(line_width)
            self._draw_circle_width_in_pixels.append(width_in_pixels)
        else:
            self.canvas.stroke_style = html_color(color)
            if not width_in_pixels:
                line_width = self.transform.scale_world_to_canvas(line_width)
            self.canvas.line_width = line_width
            self.canvas.stroke_circle(
                *self.world_to_canvas(center),
                self.transform.scale_world_to_canvas(radius),
            )

    def draw_solid_circle(self, center, radius, color):
        if self._in_debug_draw:
            self._draw_solid_circle_centers.append(center)
            self._draw_solid_circle_radii.append(radius)
            self._draw_solid_circle_colors.append(color)
        else:
            self.canvas.fill_style = html_color(color)
            self.canvas.fill_circle(
                *self.world_to_canvas(center),
                self.transform.scale_world_to_canvas(radius),
            )

    def draw_line(self, p1, p2, line_width, color, width_in_pixels=False):
        if self._in_debug_draw:
            self._draw_line_points.append((p1, p2))
            self._draw_line_colors.append(color)
            self._draw_line_widths.append(line_width)
            self._draw_line_width_in_pixels.append(width_in_pixels)
        else:
            self.canvas.stroke_style = html_color(color)
            if not width_in_pixels:
                line_width = self.transform.scale_world_to_canvas(line_width)
            self.canvas.line_width = line_width
            self.canvas.stroke_line(
                *self.world_to_canvas(p1), *self.world_to_canvas(p2)
            )


class IpycanvasFrontend(FrontendBase):

    Settings = FrontendBase.Settings

    def __init__(self, settings):
        try:
            super().__init__(settings)

            self.canvas = Canvas(
                width=self.settings.canvas_shape[0],
                height=self.settings.canvas_shape[1],
            )
            self.output_widget = Output()

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
            _last_canvas_mouse_pos = (
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
                self.canvas.clear()
                self.update_and_draw(dt)
            except Exception as e:
                self.output_widget.append_stdout(
                    f"Error in main loop: {traceback.format_exc()}\n"
                )
                self.cancel_loop()

        self.cancel_loop = set_render_loop(self.canvas, f, fps=self.settings.fps)

    def _dispatch_events(self, event):

        try:
            if event["type"] == "mousemove":
                mouse_pos = (event["relativeX"], event["relativeY"])
                # get the delta \
                if self._last_canvas_mouse_pos is None:
                    self._last_canvas_mouse_pos = mouse_pos
                delta = (
                    mouse_pos[0] - self._last_canvas_mouse_pos[0],
                    mouse_pos[1] - self._last_canvas_mouse_pos[1],
                )
                # convert delta to world coordinates
                delta = (
                    self.transform.scale_canvas_to_world(delta[0]),
                    -self.transform.scale_canvas_to_world(delta[1]),
                )
                self._last_canvas_mouse_pos = mouse_pos
                world_pos = self.transform.canvas_to_world(mouse_pos)
                self.sample.on_mouse_move(world_pos, delta)

            elif event["type"] == "mouseenter":
                self.sample.on_mouse_enter()

            elif event["type"] == "mouseleave":
                self.sample.on_mouse_leave()

            elif event["type"] == "mousedown":
                mouse_pos = (event["relativeX"], event["relativeY"])
                self._last_canvas_mouse_pos = mouse_pos
                world_pos = self.transform.canvas_to_world(mouse_pos)

                self._multi_click_handler.handle_click(world_pos)
                self.sample.on_mouse_down(world_pos)
            elif event["type"] == "mouseup":
                world_pos = self.transform.canvas_to_world(
                    (event["relativeX"], event["relativeY"])
                )
                self.sample.on_mouse_up(world_pos)

            elif event["type"] == "wheel":
                self.sample.on_mouse_wheel(event["deltaY"] / 10.0)

        except Exception as e:
            self.output_widget.append_stdout(f"Exception in event handler: {e}\n")
            self.output_widget.append_stdout(traceback.format_exc())
            self.cancel_loop()
