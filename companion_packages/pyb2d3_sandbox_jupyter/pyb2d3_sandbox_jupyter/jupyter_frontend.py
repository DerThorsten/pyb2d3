from pyb2d3_sandbox.frontend_base import (
    FrontendBase,
    MouseDownEvent,
    MouseUpEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    MouseLeaveEvent,
    MouseEnterEvent,
    KeyDownEvent,
    KeyUpEvent,
)
import sys
from .ui import TestbedUI
from .render_loop import render_loop

# output widget from ipywidgets
from ipywidgets import Output

# display from IPython

import pyb2d3 as b2d
import traceback

from .canvas_widget import CanvasWidget
from .jupyter_debug_draw import JupyterDebugDraw


def html_color(color):
    """Convert a color to a hex string"""
    if isinstance(color, int):
        return f"#{color:06x}"
    elif isinstance(color, tuple) and len(color) == 3:
        return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
    else:
        raise ValueError("Color must be an int or a tuple of (R, G, B) values.")


last_frontend = [None]


class JupyterFrontend(FrontendBase):
    Settings = FrontendBase.Settings

    def __del__(self):
        if self.cancel_loop is not None:
            self.cancel_loop()

    def _handle_exception(self, e):
        """Handle exceptions in the frontend"""
        self.output_widget.append_stdout(f"Error: {traceback.format_exc()}\n")
        print(f"Error: {e}", file=sys.stderr)
        if self.cancel_loop is not None:
            self.cancel_loop()
        raise e

    def __init__(self, settings):
        global last_frontend, use_offscreen
        self.output_widget = Output()
        self.cancel_loop = None

        super().__init__(settings)

        try:
            self.canvas = CanvasWidget(
                width=self.settings.canvas_shape[0],
                height=self.settings.canvas_shape[1],
                layout=dict(width="100%"),
                output_widget=self.output_widget,
                frontend=self,
            )
            # if a cell is re-executed, we need to cancel the previous loop,
            # otherwise we will have multiple loops running
            if last_frontend[0] is not None and last_frontend[0].cancel_loop is not None:
                last_frontend[0].cancel_loop()
            last_frontend[0] = self

            self.transform = b2d.CanvasWorldTransform(
                canvas_shape=self.settings.canvas_shape,
                ppm=self.settings.ppm,
                offset=(0, 0),
            )

            self.debug_draw = JupyterDebugDraw(
                frontend=self,
                transform=self.transform,
                canvas=self.canvas,
                output_widget=self.output_widget,
            )

            self.debug_draw.draw_shapes = settings.debug_draw.draw_shapes
            self.debug_draw.draw_joints = settings.debug_draw.draw_joints

            self.ui = TestbedUI(self)

            self._last_canvas_mouse_pos = b2d.Vec2(0, 0)

            # display the canvas
            self.ui.display()

        except Exception as e:
            self._handle_exception(e)

    def on_key_down(self, key, ctrl, shift, meta, alt):
        self._on_key_down(KeyDownEvent(key, ctrl, shift, meta, alt))

    def on_key_up(self, key):
        self._on_key_up(KeyUpEvent(key))

    def on_mouse_move(self, x, y, dx, dy):
        try:
            if self.is_paused():
                return

            world_pos = b2d.Vec2(x, y)
            world_delta = b2d.Vec2(dx, dy)

            self.sample.on_mouse_move(
                MouseMoveEvent(
                    world_position=world_pos,
                    world_delta=world_delta,
                )
            )
        except Exception as e:
            self._handle_exception(e)

    def on_mouse_wheel(self, x, y, delta):
        try:
            if self.is_paused():
                return
            world_pos = b2d.Vec2(x, y)
            self.sample.on_mouse_wheel(
                MouseWheelEvent(
                    world_position=world_pos,
                    delta=-delta / 30.0,  # adjust the delta to a more reasonable value
                )
            )
        except Exception as e:
            self._handle_exception(e)

    def on_mouse_down(self, x, y):
        try:
            if self.is_paused():
                return
            world_pos = b2d.Vec2(x, y)

            self._multi_click_handler.handle_click(world_position=world_pos)
            self.sample.on_mouse_down(MouseDownEvent(world_position=world_pos))
        except Exception as e:
            self._handle_exception(e)

    def on_mouse_up(self, x, y):
        try:
            if self.is_paused():
                return
            world_pos = b2d.Vec2(x, y)
            self.sample.on_mouse_up(MouseUpEvent(world_position=world_pos))
        except Exception as e:
            self._handle_exception(e)

    def _clear_canvas(self):
        self.debug_draw.clear_canvas()

    def on_mouse_leave(self):
        try:
            if self.is_paused():
                return
            self.sample.on_mouse_leave(MouseLeaveEvent())
        except Exception as e:
            self._handle_exception(e)

    def on_mouse_enter(self):
        try:
            if self.is_paused():
                return
            self.sample.on_mouse_enter(MouseEnterEvent())
        except Exception as e:
            self._handle_exception(e)

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

    def _callback(self):
        try:
            self.update_frontend_logic()

            if self.sample.is_done():
                self.cancel_loop()
                self.sample.post_run()
                return

            self.update_physics()
            self.draw_physics()

        except Exception:
            print("Error in main loop:", file=sys.stderr)
            self.output_widget.append_stdout(f"Error in main loop: {traceback.format_exc()}\n")
            self.cancel_loop()

    def main_loop_vanilla(self):
        self.ui_is_ready()
        self.canvas._connect_events()

        def f():
            self._callback()

        self.cancel_loop = render_loop(self.canvas, f)

    def main_loop(self):
        self.main_loop_vanilla()

    def pre_new_sample(self, sample_class, sample_settings):
        # make sure we reset the debug draw (ie clear the batches)
        self.debug_draw.reset()
        # make sure we remove all sample specific UI elements
        self.ui.remove_sample_ui_elements()

    def add_widget(self, element):
        self.ui.add_sample_ui_element(element)
