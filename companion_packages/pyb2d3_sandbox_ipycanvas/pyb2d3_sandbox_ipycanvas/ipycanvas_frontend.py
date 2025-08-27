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
import asyncio
from .ui import TestbedUI
from .render_loop import set_render_loop
from ipycanvas.call_repeated import set_render_loop as ipycanvas_set_render_loop

# output widget from ipywidgets
from ipywidgets import Output

# display from IPython

import pyb2d3 as b2d
import traceback

from ipycanvas.compat import Canvas


def html_color(color):
    """Convert a color to a hex string"""
    if isinstance(color, int):
        return f"#{color:06x}"
    elif isinstance(color, tuple) and len(color) == 3:
        return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
    else:
        raise ValueError("Color must be an int or a tuple of (R, G, B) values.")


# has pyjs?
has_pyjs = False
try:
    import pyjs  # noqa: F401

    has_pyjs = True
except ImportError:
    has_pyjs = False
is_emscripten = sys.platform.startswith("emscripten")
use_offscreen = has_pyjs and is_emscripten

if not use_offscreen:
    from ipyevents import Event
    from .debug_draw_vanilla import IpycanvasDebugDraw
else:
    from .debug_draw_offscreen import IpycanvasDebugDraw


last_frontend = [None]


class IpycanvasFrontend(FrontendBase):
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

        self._ignore_these_keys = set("Control, Shift, Meta")

        super().__init__(settings)

        try:
            self.canvas = Canvas(
                width=self.settings.canvas_shape[0],
                height=self.settings.canvas_shape[1],
                # layout=Layout(width='100%')
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

            self.debug_draw = IpycanvasDebugDraw(
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

    def _connect_events(self):
        if not use_offscreen:
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
                    "keydown",
                    "keyup",
                ],
            )
            d.on_dom_event(self._dispatch_events)
        else:
            self.canvas.on_mouse_move(self.on_mouse_move)
            self.canvas.on_mouse_down(self.on_mouse_down)
            self.canvas.on_mouse_up(self.on_mouse_up)
            self.canvas.on_mouse_out(self.on_mouse_leave)
            self.canvas.on_mouse_enter(self.on_mouse_enter)
            self.canvas.on_mouse_wheel(self.on_mouse_wheel)
            self.canvas.on_key_down(self.on_key_down)
            self.canvas.on_key_up(self.on_key_up)

    def key_to_key_name(self, key):
        if key == "Control":
            return "ctrl"
        elif key == "Shift":
            return "shift"
        elif key == "Meta":
            return "meta"
        elif key == "Alt":
            return "alt"
        elif key == " ":
            return "space"
        return key.lower()

    def on_key_down(self, key, ctrl, shift, meta):
        return self._on_key_down(
            KeyDownEvent(key=self.key_to_key_name(key), ctrl=ctrl, shift=shift, meta=meta)
        )

    def on_key_up(self, key, ctrl, shift, meta):
        return self._on_key_up(KeyUpEvent(key=self.key_to_key_name(key)))

    def on_mouse_move(self, x, y):
        try:
            if self.is_paused():
                return
            mouse_pos = b2d.Vec2(x, y)
            # get the delta
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
        except Exception as e:
            self._handle_exception(e)

    def on_mouse_wheel(self, delta):
        try:
            if self.is_paused():
                return
            canvas_pos = self._last_canvas_mouse_pos
            world_pos = self.transform.canvas_to_world(canvas_pos)
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
            mouse_pos = b2d.Vec2(x, y)
            self._last_canvas_mouse_pos = mouse_pos
            world_pos = self.transform.canvas_to_world(mouse_pos)

            self._multi_click_handler.handle_click(world_position=world_pos)
            self.sample.on_mouse_down(MouseDownEvent(world_position=world_pos))
        except Exception as e:
            self._handle_exception(e)

    def on_mouse_up(self, x, y):
        try:
            if self.is_paused():
                return
            canvas_pos = b2d.Vec2(x, y)
            world_pos = self.transform.canvas_to_world(canvas_pos)
            self.sample.on_mouse_up(MouseUpEvent(world_position=world_pos))
        except Exception as e:
            self._handle_exception(e)

    def on_mouse_leave(self, x, y):
        try:
            if self.is_paused():
                return
            self.sample.on_mouse_leave(MouseLeaveEvent())
        except Exception as e:
            self._handle_exception(e)

    def on_mouse_enter(self, x, y):
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

    def _clear_canvas(self):
        if self.settings.debug_draw.draw_background:
            self.canvas.fill_style = html_color(self.settings.debug_draw.background_color)
            self.canvas.fill_rect(
                0,
                0,
                self.settings.canvas_shape[0],
                self.settings.canvas_shape[1],
            )
        else:
            self.canvas.clear()

    def _callback(self):
        try:
            self.update_frontend_logic()

            if self.sample.is_done():
                self.cancel_loop()
                self.sample.post_run()
                return

            self._clear_canvas()
            self.update_physics()
            self.draw_physics()

        except Exception:
            print("Error in main loop:", file=sys.stderr)
            self.output_widget.append_stdout(f"Error in main loop: {traceback.format_exc()}\n")
            self.cancel_loop()

    def main_loop_vanilla(self):
        self.ui_is_ready()
        self._connect_events()

        def f():
            self._callback()

        self.cancel_loop = set_render_loop(self.canvas, f)

    async def async_main_loop(self):
        try:
            await self.canvas.async_initialize()
            self.ui_is_ready()
            self._connect_events()

            def f(_):
                self._callback()

            # fps=0 means use requestAnimationFrame
            self.cancel_loop = ipycanvas_set_render_loop(self.canvas, f, fps=0)

        except Exception as e:
            self._handle_exception(e)
            return

    def main_loop_lite(self):
        # run self.async_main_loop in a a task
        asyncio.create_task(self.async_main_loop())

    def main_loop(self):
        if is_emscripten:
            self.main_loop_lite()
        else:
            self.main_loop_vanilla()

    def _dispatch_events(self, event):
        try:
            if self.is_paused():
                return
            if event["type"] == "keydown":
                my_event = KeyDownEvent(
                    key=event["key"],
                    alt=event["altKey"],
                    ctrl=event["ctrlKey"],
                    meta=event["metaKey"],
                    shift=event["shiftKey"],
                )
                self._on_key_down(my_event)
            elif event["type"] == "keyup":
                key = event["key"]
                my_event = KeyUpEvent(key=key)
                self._on_key_up(my_event)

            else:
                mouse_pos = b2d.Vec2(event["relativeX"], event["relativeY"])
                if event["type"] == "mousemove":
                    self.on_mouse_move(*mouse_pos)
                elif event["type"] == "mouseenter":
                    self.on_mouse_enter(*mouse_pos)
                elif event["type"] == "mouseleave":
                    self.on_mouse_leave(*mouse_pos)
                elif event["type"] == "mousedown":
                    self.on_mouse_down(*mouse_pos)
                elif event["type"] == "mouseup":
                    self.on_mouse_up(*mouse_pos)
                elif event["type"] == "wheel":
                    self.on_mouse_wheel(event["deltaY"])
        except Exception as e:
            self._handle_exception(e)
            return

        # elif event["type"] == "keydown":
        #     self._on_key_down(
        #         KeyDownEvent(key=event["key"])
        #     )
        # elif event["type"] == "keyup":
        #     self._on_key_up(
        #         KeyUpEvent(key=event["key"])
        #     )

    def pre_new_sample(self, sample_class, sample_settings):
        # make sure we reset the debug draw (ie clear the batches)
        self.debug_draw.reset()
        # make sure we remove all sample specific UI elements
        self.ui.remove_sample_ui_elements()

    def add_widget(self, element):
        self.ui.add_sample_ui_element(element)
