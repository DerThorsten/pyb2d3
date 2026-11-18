"""Sandbox frontend for the browser (pyjs, emscripten).

* rendering: the instanced GL renderers + shaders of pyb2d3_sandbox_opengl
  (GLDebugDraw) via PyOpenGL into a WebGL2 context on a <canvas>
* frames: `pyjs.request_animation_frame_loop`
* input: DOM pointer / wheel / key events of the canvas
* UI: plain HTML in a panel element (sample list, controls, debug draw
  options, the widgets of the sample), debug strings as HTML labels

The page provides the elements (ids configurable in `Settings`): a canvas, a
panel, and a label layer positioned over the canvas.
"""

import ctypes
import importlib
import importlib.util
import inspect
import json
import math
import os
import sys
import time
import traceback
from dataclasses import dataclass

import pyjs

import pyb2d3_sandbox_opengl  # noqa: F401 (first: switches PyOpenGL's per-call glGetError off)
from OpenGL import GL as gl
from pyb2d3 import Vec2

import pyb2d3_sandbox.widgets as widgets
from pyb2d3_sandbox.frontend_base import (
    FrontendBase,
    KeyDownEvent,
    KeyUpEvent,
    MouseDownEvent,
    MouseEnterEvent,
    MouseLeaveEvent,
    MouseWheelEvent,
)
from pyb2d3_sandbox_opengl.debug_draw_gl import Camera, GLDebugDraw

from .gestures import PointerGestures

# DOM `KeyboardEvent.key` -> sandbox key names (letters / digits: themselves)
KEY_NAMES = {
    " ": "space",
    "ArrowLeft": "left",
    "ArrowRight": "right",
    "ArrowUp": "up",
    "ArrowDown": "down",
    "Escape": "escape",
    "Enter": "enter",
    "Tab": "tab",
    "Control": "ctrl",
    "Shift": "shift",
    "Meta": "meta",
    "Alt": "alt",
}

# DOM keys switching to the previous / next sample (like the pygame frontend)
SAMPLE_KEYS = {"PageUp": -1, "PageDown": 1}

# URL query parameter with the current sample ("Category/Name"): the page
# starts with it, the frontend keeps it up to date (reload / share a link)
SAMPLE_QUERY_PARAMETER = "sample"

# the icons of the control buttons (︎: text style, not a colored emoji); the single
# step is an arrow to a bar (one step, then stop): skip icons mean "next sample" here
_TEXT = "︎"
ICONS = {
    "previous": "⏮" + _TEXT,  # ⏮
    "play": "▶" + _TEXT,  # ▶
    "pause": "⏸" + _TEXT,  # ⏸
    "step": "⇥",  # ⇥
    "reset": "↺",  # ↺
    "next": "⏭" + _TEXT,  # ⏭
}

DEBUG_DRAW_OPTIONS = [
    ("draw_shapes", "Shapes"),
    ("draw_joints", "Joints"),
    ("draw_joint_extras", "Joint extras"),
    ("draw_bounds", "Bounds"),
    ("draw_contacts", "Contacts"),
]


def key_name(dom_key):
    """sandbox key name of a DOM key, None for keys the sandbox does not know"""
    if dom_key in KEY_NAMES:
        return KEY_NAMES[dom_key]
    if len(dom_key) == 1 and dom_key.isalnum():
        return dom_key.lower()
    return None


def speed_from_slider(val):
    """slider value in [-4, 4] -> speed factor (0 -> 1x, 3 -> 4x, -3 -> 1/4x)"""
    if val > 0:
        return 1.0 + val
    if val == 0:
        return 1.0
    return 1.0 / abs(val - 1)


# WebGL2 context (emscripten's html5 API via ctypes: the GL functions PyOpenGL
# calls use emscripten's current context)
class _WebGLContextAttributes(ctypes.Structure):
    """`EmscriptenWebGLContextAttributes` (emscripten/html5_webgl.h)"""

    _fields_ = [
        ("alpha", ctypes.c_bool),
        ("depth", ctypes.c_bool),
        ("stencil", ctypes.c_bool),
        ("antialias", ctypes.c_bool),
        ("premultipliedAlpha", ctypes.c_bool),
        ("preserveDrawingBuffer", ctypes.c_bool),
        ("powerPreference", ctypes.c_int),
        ("failIfMajorPerformanceCaveat", ctypes.c_bool),
        ("majorVersion", ctypes.c_int),
        ("minorVersion", ctypes.c_int),
        ("enableExtensionsByDefault", ctypes.c_bool),
        ("explicitSwapControl", ctypes.c_bool),
        ("proxyContextToMainThread", ctypes.c_int),
        ("renderViaOffscreenBackBuffer", ctypes.c_bool),
        ("desynchronized", ctypes.c_bool),
    ]


def create_webgl2_context(canvas, antialias=True):
    """create a WebGL2 context on `canvas` and make it current (for PyOpenGL);
    `antialias`: multisampling (costly on mobile GPUs)"""
    pyjs.set_canvas(canvas)
    lib = ctypes.CDLL(None)
    attrs = _WebGLContextAttributes()
    lib.emscripten_webgl_init_context_attributes(ctypes.byref(attrs))
    attrs.majorVersion = 2
    attrs.minorVersion = 0
    attrs.alpha = False
    attrs.depth = False
    attrs.stencil = False
    attrs.antialias = bool(antialias)

    create = lib.emscripten_webgl_create_context
    create.restype = ctypes.c_size_t
    create.argtypes = [ctypes.c_char_p, ctypes.POINTER(_WebGLContextAttributes)]
    ctx = create(b"#canvas", ctypes.byref(attrs))
    if ctx == 0:
        raise RuntimeError("this browser cannot create a WebGL2 context")
    make_current = lib.emscripten_webgl_make_context_current
    make_current.argtypes = [ctypes.c_size_t]
    if make_current(ctx) != 0:
        raise RuntimeError("cannot make the WebGL2 context current")
    return ctx


# one listener per element + event; forwards the event to python. Pointer /
# key events are reduced to plain values in JS (fewer JS <-> python calls).
# cb(kind, x, y, a, b, key, flags, pointer id): pointer events carry the pointer id
# and its type in `key` ("mouse" / "touch" / "pen", see gestures.py); enter / leave
# only for the mouse (touches have no hover); wheel: a = deltaY in px, flags 1 = ctrl
# (a trackpad pinch arrives as ctrl + wheel)
_CANVAS_EVENTS_JS = """
const mods = (e) => (e.ctrlKey ? 1 : 0) | (e.shiftKey ? 2 : 0) | (e.metaKey ? 4 : 0) | (e.altKey ? 8 : 0);
const pressed = (e) => e.pointerType !== "mouse" || (e.buttons & 1);
canvas.style.touchAction = "none";
canvas.addEventListener("pointerdown", (e) => {
  if (e.pointerType === "mouse" && e.button !== 0) return;
  canvas.setPointerCapture(e.pointerId);
  canvas.focus();
  cb("down", e.offsetX, e.offsetY, 0, 0, e.pointerType, 0, e.pointerId);
});
canvas.addEventListener("pointermove", (e) => {
  if (pressed(e)) cb("move", e.offsetX, e.offsetY, 0, 0, e.pointerType, 0, e.pointerId);
});
canvas.addEventListener("pointerup", (e) => {
  if (e.pointerType === "mouse" && e.button !== 0) return;
  cb("up", e.offsetX, e.offsetY, 0, 0, e.pointerType, 0, e.pointerId);
});
canvas.addEventListener("pointercancel", (e) => {
  cb("cancel", e.offsetX, e.offsetY, 0, 0, e.pointerType, 0, e.pointerId);
});
canvas.addEventListener("pointerenter", (e) => {
  if (e.pointerType === "mouse") cb("enter", 0, 0, 0, 0, "mouse", 0, e.pointerId);
});
canvas.addEventListener("pointerleave", (e) => {
  if (e.pointerType === "mouse") cb("leave", 0, 0, 0, 0, "mouse", 0, e.pointerId);
});
canvas.addEventListener("wheel", (e) => {
  e.preventDefault();
  const px = e.deltaMode === 1 ? 16 * e.deltaY : e.deltaY;  // lines -> px
  cb("wheel", e.offsetX, e.offsetY, px, 0, "", e.ctrlKey ? 1 : 0, 0);
}, { passive: false });
canvas.addEventListener("keydown", (e) => {
  if (e.repeat) return;
  if (e.key.startsWith("Arrow") || e.key.startsWith("Page") || e.key === " ") e.preventDefault();
  cb("keydown", 0, 0, 0, 0, e.key, mods(e), 0);
});
canvas.addEventListener("keyup", (e) => cb("keyup", 0, 0, 0, 0, e.key, 0, 0));
"""


class _Dom:
    """create elements and event listeners; keeps the JS callables of the
    listeners alive and frees them with `clear()`"""

    def __init__(self):
        self.document = pyjs.js.document
        self._handles = []

    def callable(self, fn):
        """a JS function calling `fn` (alive until `clear`)"""
        js_fn, handle = pyjs.create_callable(fn)
        self._handles.append(handle)
        return js_fn

    def on(self, element, event, fn):
        """element.addEventListener(event, fn(event))"""
        element.addEventListener(event, self.callable(fn))

    def el(self, tag, parent=None, text=None, cls=None, **attrs):
        """create `<tag>` with text / class / attributes, append it to `parent`"""
        element = self.document.createElement(tag)
        if text is not None:
            element.textContent = str(text)
        if cls is not None:
            element.className = cls
        for name, value in attrs.items():
            element.setAttribute(name.rstrip("_").replace("_", "-"), str(value))
        if parent is not None:
            parent.appendChild(element)
        return element

    def clear(self):
        """free the JS callables (their listeners must be gone: remove the elements first)"""
        for handle in self._handles:
            handle.delete()
        self._handles.clear()


class _Labels:
    """debug strings as absolutely positioned HTML labels in the label layer
    (a pool of <span>s, reused every frame)"""

    def __init__(self, dom, layer):
        self.dom = dom
        self.layer = layer
        self.spans = []
        self.used = 0

    def add(self, screen_pos, text, rgb):
        """`GLDebugDraw.draw_text`: one label at a canvas position (CSS px)"""
        if self.used == len(self.spans):
            self.spans.append(self.dom.el("span", self.layer, cls="pyb2d3-label"))
        span = self.spans[self.used]
        self.used += 1
        span.textContent = text
        r, g, b = (int(c * 255) for c in rgb)
        span.style.cssText = f"display:block;left:{screen_pos.x:.0f}px;top:{screen_pos.y:.0f}px;color:rgb({r},{g},{b})"

    def flush(self):
        """hide the labels not used in this frame"""
        for span in self.spans[self.used :]:
            span.style.display = "none"
        self.used = 0


class WebglFrontend(FrontendBase):
    @dataclass
    class Settings(FrontendBase.Settings):
        canvas_id: str = "canvas"
        panel_id: str = "panel"
        labels_id: str = "labels"
        # phones have devicePixelRatio 3: 2.25x more pixels for the shape shaders than
        # at 2, hardly visible; at >= 2 multisampling is switched off as well
        max_pixel_ratio: float = 2.0

    def __init__(self, settings):
        super().__init__(settings)
        self.camera = Camera()
        self.debug_draw = None
        self._dom = _Dom()  # page-lifetime elements (panel, canvas events)
        self._sample_dom = _Dom()  # the widgets of the current sample
        self._labels = None
        self._loop = None
        self._single_step = False
        self._pixel_size = (0, 0)
        self._fps_frames = 0
        self._fps_t0 = time.perf_counter()
        self._physics_s = 0.0  # time in physics / drawing since the last fps update
        self._draw_s = 0.0
        self._gestures = PointerGestures(self)  # pointers -> mouse events, pinch zoom
        self._fit_zoom = None  # the zoom of the fitted view (center_sample)
        self._landscape = None  # canvas orientation: re-fit when it flips

    def main_loop(self):
        """create the WebGL2 context, the UI, the sample; start the frame loop
        (returns right away: frames come from requestAnimationFrame)"""
        document = pyjs.js.document
        self.canvas = document.getElementById(self.settings.canvas_id)
        self.panel = document.getElementById(self.settings.panel_id)
        labels_layer = document.getElementById(self.settings.labels_id)
        if self.canvas is None or self.panel is None or labels_layer is None:
            raise RuntimeError(
                "the page needs the elements "
                f"#{self.settings.canvas_id}, #{self.settings.panel_id}, #{self.settings.labels_id}"
            )
        self._labels = _Labels(self._dom, labels_layer)

        # multisampling only on low density screens (the shaders smooth the shape
        # edges themselves; MSAA is expensive on mobile GPUs)
        create_webgl2_context(self.canvas, antialias=self._pixel_ratio() < 2.0)
        self.debug_draw = GLDebugDraw(self.camera, draw_text=self._labels.add)
        # the canvas is ours alone: clear it instead of the full-screen noise shader
        self.debug_draw.background.use_clear = True
        self.debug_draw.draw_shapes = True
        self.debug_draw.draw_joints = True

        self._resize()
        self._build_panel()
        self._fps_overlay = self._create_fps_overlay()
        self._create_zoom_buttons()
        self._connect_canvas_events()
        self.ui_is_ready()  # creates the sample

        self._loop = pyjs.request_animation_frame_loop(self._frame)

    def stop_loop(self):
        """stop rendering (e.g. before the page starts another frontend)"""
        if self._loop is not None:
            self._loop.cancel()
            self._loop = None

    def _pixel_ratio(self):
        """drawing buffer pixels per CSS pixel: devicePixelRatio, capped at
        settings.max_pixel_ratio (fill rate on phones)"""
        return min(float(pyjs.js.devicePixelRatio or 1.0), self.settings.max_pixel_ratio)

    def _resize(self):
        """match the drawing buffer to the canvas' CSS size (x the pixel ratio)"""
        css_w = max(1, int(self.canvas.clientWidth))
        css_h = max(1, int(self.canvas.clientHeight))
        dpr = self._pixel_ratio()
        pixel_size = (max(1, round(css_w * dpr)), max(1, round(css_h * dpr)))
        if pixel_size != self._pixel_size:
            self._pixel_size = pixel_size
            self.canvas.width, self.canvas.height = pixel_size
        # the camera works in CSS px (the coordinates of the pointer events)
        self.camera.set_size(css_w, css_h)
        # the device was turned (portrait <-> landscape): fit the sample again, it
        # would be tiny or cut off in the other orientation
        landscape = css_w >= css_h
        if self._landscape is not None and landscape != self._landscape and self.sample is not None:
            self.center_sample(10)
        self._landscape = landscape

    def _frame(self, time_ms):
        """one animation frame: logic, physics, draw; False stops the loop"""
        self._resize()
        starting = self.change_sample_class_requested
        try:
            self.update_frontend_logic()
            if self.sample is not None:
                t0 = time.perf_counter()
                if self._single_step:
                    self._single_step = False
                    self.update_physics_single_step()
                elif not self._is_paused:
                    self.update_physics()
                t1 = time.perf_counter()

                gl.glViewport(0, 0, *self._pixel_size)
                self.draw_physics()
                self._labels.flush()
                self._physics_s += t1 - t0
                self._draw_s += time.perf_counter() - t1
        except Exception:
            # an error in the sample (e.g. code edited in the page): keep the
            # page alive, pause, show the error; "run" / another sample goes on
            if starting:
                self.sample = None  # its constructor failed
            self._set_paused_ui(True)
            self._report_error(traceback.format_exc())
        self._count_fps()
        return True

    # the page: events for the code editor (examples/web)
    def _dispatch(self, name, detail):
        """a CustomEvent `name` with the JSON-able `detail` on window"""
        init = pyjs.js.JSON.parse(json.dumps({"detail": detail}))
        pyjs.js.window.dispatchEvent(pyjs.js.CustomEvent.new(name, init))

    def _report_error(self, text):
        """an error of the sample: the console + event "pyb2d3-error" (detail: the traceback)"""
        pyjs.js.console.error(text)
        self._dispatch("pyb2d3-error", text)

    def _announce_sample(self, sample_class):
        """event "pyb2d3-sample" (detail: key, source file, line of the class)"""
        entry = self.sample_entry
        try:
            file = inspect.getsourcefile(sample_class)
            line = inspect.findsource(sample_class)[1] + 1
        except (OSError, TypeError):
            file, line = None, 0
        self._dispatch(
            "pyb2d3-sample", {"key": entry.key if entry else None, "file": file, "line": line}
        )

    def reload_code(self, paths=()):
        """re-import the modules of the python files `paths` (edited in the
        page and written to the file system) and restart the current sample with
        the new code; its own module is always re-imported (last). Errors are
        reported like errors of the sample."""
        key = self.sample_entry.key if self.sample_entry is not None else None
        target = self.sample_class
        # the sample's own module last: it imports from the edited files
        own = sys.modules.get(target.__module__)
        last = [own] if own is not None else []
        paths = {os.path.abspath(p) for p in paths}
        # their old bytecode must not win: a .pyc is only checked against the source's
        # mtime (1 s resolution) and size, an edit within the same second could keep it
        for path in paths:
            try:
                os.remove(importlib.util.cache_from_source(path))
            except OSError:
                pass
        modules = [
            m
            for m in list(sys.modules.values())
            if m not in last
            and getattr(m, "__file__", None)
            and os.path.abspath(m.__file__) in paths
        ] + last
        try:
            importlib.invalidate_caches()
            for module in modules:
                importlib.reload(module)
        except Exception:
            self._report_error(traceback.format_exc())
            return
        replaced = self.registry.replace_classes(modules)
        if getattr(self, "_sample_classes", None):
            # the sample list's classes (same order as built in _build_panel)
            self._sample_classes = [entry.cls for entry in self.registry]
        self._set_paused_ui(False)
        # by key: modules that register their samples themselves (the box2d
        # ports) already put the new classes into the registry while re-imported
        self.set_sample(self.registry.get(key).cls if key else replaced.get(target, target))

    def _count_fps(self):
        """update the fps overlay about twice a second: frames per second and the
        time per frame spent in physics (sample + world.step) and in drawing"""
        self._fps_frames += 1
        now = time.perf_counter()
        if now - self._fps_t0 >= 0.5:
            frames = self._fps_frames
            fps = frames / (now - self._fps_t0)
            physics_ms = 1000.0 * self._physics_s / frames
            draw_ms = 1000.0 * self._draw_s / frames
            self._fps_frames = 0
            self._physics_s = self._draw_s = 0.0
            self._fps_t0 = now
            w, h = self._pixel_size  # the drawing buffer: what the GPU fills each frame
            self._fps_overlay.textContent = (
                f"{fps:.0f} fps · physics {physics_ms:.1f} ms · draw {draw_ms:.1f} ms · {w}×{h} px"
            )

    def _create_fps_overlay(self):
        """the fps counter: a small label in the bottom right corner of the canvas
        (samples write their own text at the top left)"""
        overlay = self._dom.el("div", self.canvas.parentElement, "", cls="pyb2d3-fps")
        style = overlay.style
        style.position = "absolute"
        style.bottom = "6px"
        style.right = "8px"
        style.padding = "2px 6px"
        style.borderRadius = "4px"
        style.background = "rgba(0, 0, 0, 0.45)"
        style.color = "#d9dce1"
        style.font = "12px monospace"
        style.pointerEvents = "none"
        return overlay

    def _create_zoom_buttons(self):
        """+ / - / fit buttons on the canvas (touch screens have no wheel); placed by
        the page's CSS (class pyb2d3-zoom)"""
        dom = self._dom
        group = dom.el("div", self.canvas.parentElement, cls="pyb2d3-zoom")
        center = lambda: (0.5 * self.camera.width, 0.5 * self.camera.height)  # noqa: E731
        for text, title, action in (
            ("+", "zoom in", lambda e: self.zoom_at(*center(), 1.25)),
            ("−", "zoom out", lambda e: self.zoom_at(*center(), 1.0 / 1.25)),
            ("fit", "show the whole sample", lambda e: self.center_sample(10)),
        ):
            button = dom.el("button", group, text, title=title, type="button")
            dom.on(button, "click", action)
        return group

    def _connect_canvas_events(self):
        """forward the DOM events of the canvas to `_on_canvas_event`"""
        install = pyjs.js.Function("canvas", "cb", _CANVAS_EVENTS_JS)
        install(self.canvas, self._dom.callable(self._on_canvas_event))

    def _world(self, x, y):
        """CSS px of the canvas -> world position"""
        return self.camera.convert_screen_to_world(Vec2(float(x), float(y)))

    # the host interface of PointerGestures (gestures.py)
    def screen_to_world(self, x, y):
        """canvas CSS px -> world position"""
        return self._world(x, y)

    def on_primary_down(self, x, y):
        """the first pointer's press: the sample's mouse down + multi clicks"""
        world = self._world(x, y)
        self.sample.on_mouse_down(MouseDownEvent(world_position=world))
        if self._multi_click_handler is not None:
            self._multi_click_handler.handle_click(world_position=world)

    def pan_screen(self, dx, dy):
        """move the view with the fingers by a canvas px delta"""
        self.drag_camera(self.camera.screen_delta_to_world_delta((dx, dy)))

    def _on_canvas_event(self, kind, x, y, a, b, key, flags, pid=0):
        """a canvas event (reduced to plain values by _CANVAS_EVENTS_JS)"""
        if kind == "keydown" and str(key) in SAMPLE_KEYS:  # also while paused
            self.next_sample(SAMPLE_KEYS[str(key)])
            return
        if self.sample is None or self._is_paused:
            if kind in ("up", "cancel"):  # keep the pointer bookkeeping straight
                self._gestures.up(int(pid), float(x), float(y), cancelled=True)
            return
        x, y = float(x), float(y)
        if kind == "down":
            self._gestures.down(int(pid), x, y, str(key))
        elif kind == "move":
            self._gestures.move(int(pid), x, y)
        elif kind in ("up", "cancel"):
            self._gestures.up(int(pid), x, y, cancelled=(kind == "cancel"))
        elif kind == "wheel":
            delta = float(a)
            if int(flags) & 1:  # trackpad pinch (ctrl + wheel): zoom smoothly
                self.zoom_at(x, y, math.exp(-0.01 * delta))
            elif delta:
                self.sample.on_mouse_wheel(
                    MouseWheelEvent(
                        world_position=self._world(x, y), delta=math.copysign(1.0, delta)
                    )
                )
        elif kind == "enter":
            self.sample.on_mouse_enter(MouseEnterEvent())
        elif kind == "leave":
            self.sample.on_mouse_leave(MouseLeaveEvent())
        elif kind in ("keydown", "keyup"):
            name = key_name(str(key))
            if name is None:
                return
            if kind == "keydown":
                flags = int(flags)
                self._on_key_down(
                    KeyDownEvent(
                        key=name,
                        ctrl=bool(flags & 1),
                        shift=bool(flags & 2),
                        meta=bool(flags & 4),
                        alt=bool(flags & 8),
                    )
                )
            else:
                self._on_key_up(KeyUpEvent(key=name))

    # zoom range relative to the sample's fitted view (center_sample)
    MAX_ZOOM_IN = 50.0
    MAX_ZOOM_OUT = 20.0

    def center_sample(self, margin_px=10):
        """fit the sample's bounding box into the canvas"""
        aabb = self.sample.aabb()
        center = aabb.center()
        size = aabb.upper_bound - aabb.lower_bound
        aspect = float(self.camera.width) / float(self.camera.height)
        self.camera.center = center
        self.camera.zoom = max(0.5 * size.x / aspect, 0.5 * size.y)
        self._fit_zoom = self.camera.zoom
        self.camera._matrix = None

    def drag_camera(self, delta):
        """move the view by a world delta"""
        self.camera.center -= (delta[0], delta[1])
        self.camera._matrix = None

    def zoom_at(self, x, y, factor):
        """zoom by `factor` (> 1: in) about the canvas point (x, y): the world point
        under it stays in place; limited relative to the sample's fitted view"""
        fit = getattr(self, "_fit_zoom", None) or self.camera.zoom
        before = self._world(x, y)
        zoom = self.camera.zoom / factor
        self.camera.zoom = min(max(zoom, fit / self.MAX_ZOOM_IN), fit * self.MAX_ZOOM_OUT)
        self.camera._matrix = None
        after = self._world(x, y)
        self.camera.center += (before.x - after.x, before.y - after.y)
        self.camera._matrix = None

    def change_zoom(self, delta):
        """zoom out (delta > 0) / in by wheel ticks, about the canvas center"""
        self.zoom_at(0.5 * self.camera.width, 0.5 * self.camera.height, 1.1 ** (-delta))

    def wheel_zoom(self, delta, world_position):
        """zoom by wheel ticks about the mouse position (SampleBase.on_mouse_wheel)"""
        screen = self.camera.convert_world_to_screen(Vec2(world_position[0], world_position[1]))
        self.zoom_at(screen.x, screen.y, 1.1 ** (-delta))

    def _build_panel(self):
        """sample list + play / step / reset, the sample's own widgets, simulation
        settings, debug draw options"""
        dom = self._dom
        panel = self.panel
        panel.textContent = ""

        # the controls, on top (a collapsible section, open at the start): one row of icon
        # buttons: previous sample, play / pause, single step, restart, next sample
        section = dom.el("details", panel, cls="pyb2d3-section", open="")
        dom.el("summary", section, "Controls")
        row = dom.el("div", section, cls="pyb2d3-row pyb2d3-icons")

        def icon_button(icon, title, on_click, **attrs):
            button = dom.el("button", row, icon, title=title, aria_label=title, **attrs)
            dom.on(button, "click", lambda e: on_click())
            return button

        if len(self.registry):
            icon_button(ICONS["previous"], "previous sample (PageUp)", lambda: self.next_sample(-1))
        self._play_button = icon_button(ICONS["pause"], "pause", self._toggle_pause)
        self._step_button = icon_button(
            ICONS["step"], "single step (while paused)", self._request_single_step, disabled=""
        )
        icon_button(ICONS["reset"], "restart the sample", self.stop)
        if len(self.registry):
            icon_button(ICONS["next"], "next sample (PageDown)", lambda: self.next_sample(1))

        # sample choice: a tree like the native frontend's, a collapsible group per
        # category (one list of all ~160 samples is far too long); the section itself is
        # collapsible too, open at the start
        if len(self.registry):
            section = dom.el("details", panel, cls="pyb2d3-section pyb2d3-sample-section", open="")
            dom.el("summary", section, "Sample")
            self._sample_classes = [entry.cls for entry in self.registry]
            self._sample_tree = dom.el("div", section, cls="pyb2d3-sample-tree")
            self._tree_groups, self._tree_items = {}, []  # items: in registry order
            for category in self.registry.categories():
                group = dom.el("details", self._sample_tree)
                dom.el("summary", group, category)
                self._tree_groups[category] = group
                for entry in self.registry.samples(category):
                    item = dom.el("div", group, entry.name, cls="pyb2d3-tree-item")
                    index = len(self._tree_items)
                    dom.on(
                        item, "click", lambda e, k=index: self.set_sample(self._sample_classes[k])
                    )
                    self._tree_items.append(item)
            self._show_in_tree()

        # simulation settings: collapsed (click the heading to open)
        section = dom.el("details", panel, cls="pyb2d3-section")
        dom.el("summary", section, "Simulation")
        self._slider(
            dom,
            section,
            "Hertz",
            1,
            120,
            1,
            self.settings.hertz,
            lambda v: setattr(self.settings, "hertz", v),
            fmt="{:.0f} Hz",
        )
        self._slider(
            dom,
            section,
            "Substeps",
            0,
            30,
            1,
            self.settings.substeps,
            lambda v: setattr(self.settings, "substeps", int(v)),
            fmt="{:.0f}",
        )
        self._slider(
            dom,
            section,
            "Speed",
            -4,
            4,
            0.1,
            0.0,
            lambda v: setattr(self.settings, "speed", speed_from_slider(v)),
            fmt_value=lambda v: f"{speed_from_slider(v):.2f}x",
        )

        # debug draw options: collapsed (click the heading to open)
        section = dom.el("details", panel, cls="pyb2d3-section")
        dom.el("summary", section, "Debug draw")
        for name, label in DEBUG_DRAW_OPTIONS:
            self._checkbox(
                dom,
                section,
                label,
                bool(getattr(self.debug_draw, name)),
                lambda v, name=name: setattr(self.debug_draw, name, v),
            )

        # the sample: collapsible, open at the start, its title the heading; its widgets
        # (filled by add_widget), help text (a box of fixed height: switching samples
        # moves nothing)
        section = dom.el("details", panel, cls="pyb2d3-section", open="")
        self._sample_title = dom.el("summary", section, "")
        self._sample_widgets = dom.el("div", section)
        self._sample_help = dom.el("p", section, "", cls="pyb2d3-help pyb2d3-sample-help")
        dom.el(
            "p",
            section,
            "mouse: drag bodies, drag the background to pan, wheel zooms\n"
            "touch: drag bodies, one finger on empty space pans, two fingers zoom",
            cls="pyb2d3-help",
        )

    def _slider(
        self, dom, parent, label, lo, hi, step, value, callback, fmt="{:.2f}", fmt_value=None
    ):
        """a labeled <input type=range> calling `callback(float)` on input"""
        fmt_value = fmt_value or fmt.format
        row = dom.el("label", parent, cls="pyb2d3-slider")
        dom.el("span", row, label)
        slider = dom.el("input", row, type="range", min=lo, max=hi, step=step, value=value)
        shown = dom.el("span", row, fmt_value(value), cls="pyb2d3-value")

        def on_input(event):
            v = float(slider.value)
            shown.textContent = fmt_value(v)
            callback(v)

        dom.on(slider, "input", on_input)
        return slider

    def _checkbox(self, dom, parent, label, value, callback):
        """a labeled checkbox calling `callback(bool)` on change"""
        row = dom.el("label", parent, cls="pyb2d3-check")
        box = dom.el("input", row, type="checkbox")
        box.checked = value
        dom.el("span", row, label)
        dom.on(box, "change", lambda e: callback(bool(box.checked)))
        return box

    def _show_in_tree(self):
        """highlight the running sample in the tree, open its category (the others stay
        as the user left them) and scroll it into the tree's view"""
        current = (
            self._sample_classes.index(self.sample_class)
            if self.sample_class in self._sample_classes
            else -1
        )
        for k, item in enumerate(self._tree_items):
            item.classList.toggle("active", k == current)
        entry = self.sample_entry
        if current < 0 or entry is None:
            return
        self._tree_groups[entry.category].open = True
        item, tree = self._tree_items[current], self._sample_tree
        top = item.offsetTop  # (the tree is the items' offset parent)
        if top < tree.scrollTop or top > tree.scrollTop + tree.clientHeight - item.offsetHeight:
            tree.scrollTop = top - tree.clientHeight / 3

    def _toggle_pause(self):
        """play / pause"""
        self._set_paused_ui(not self.is_paused())

    def _set_paused_ui(self, paused):
        """pause / run the simulation and update the play / step buttons"""
        if paused:
            self.set_paused()
        else:
            self.set_running()
        title = "play" if paused else "pause"
        self._play_button.textContent = ICONS[title]
        self._play_button.title = title
        self._play_button.setAttribute("aria-label", title)
        self._step_button.disabled = not paused

    def _request_single_step(self):
        """one physics step in the next frame (while paused)"""
        self._single_step = True

    # the sample's widgets (FrontendBase)
    def pre_new_sample(self, sample_class, sample_settings):
        """remove the widgets of the previous sample, forget its pointers"""
        if getattr(self, "_sample_widgets", None) is not None:
            self._sample_widgets.textContent = ""
        self._sample_dom.clear()
        self._gestures.reset()

    def post_new_sample(self, sample_class, sample_settings):
        """show the title and the help text of the new sample, select it in the
        sample list, put it into the URL"""
        self._sample_title.textContent = self.sample_title
        self._sample_help.textContent = sample_class.help_text()
        if getattr(self, "_tree_items", None):
            self._show_in_tree()
        self._update_url()
        self._announce_sample(sample_class)

    def _update_url(self):
        """`?sample=Category/Name` of the current sample in the address bar
        (replaceState: switching samples adds no history entries)"""
        entry = self.sample_entry
        if entry is None:
            return
        url = pyjs.js.URL.new(pyjs.js.location.href)
        url.searchParams.set(SAMPLE_QUERY_PARAMETER, entry.key)
        pyjs.js.history.replaceState(None, "", url.href)

    def add_widget(self, element):
        """an HTML control for a sandbox widget of the sample"""
        dom, parent = self._sample_dom, self._sample_widgets
        if isinstance(element, (widgets.FloatSlider, widgets.IntSlider)):
            is_int = isinstance(element, widgets.IntSlider)

            def on_value(v, element=element, is_int=is_int):
                element.value = int(v) if is_int else v
                element.callback(element.value)

            self._slider(
                dom,
                parent,
                element.label,
                element.min_value,
                element.max_value,
                element.step or (1 if is_int else 0.01),
                element.value,
                on_value,
                fmt="{:.0f}" if is_int else "{:.2f}",
            )
        elif isinstance(element, widgets.Checkbox):

            def on_check(v, element=element):
                element.value = v
                element.callback(v)

            self._checkbox(dom, parent, element.label, bool(element.value), on_check)
        elif isinstance(element, widgets.Separator):
            dom.el("hr", parent)
            if element.label:
                dom.el("b", parent, element.label)
        elif isinstance(element, widgets.TextInput):
            dom.el("span", parent, element.label)
            area = dom.el("textarea", parent, element.value, cls="pyb2d3-wide", rows=3)

            def on_text(e, element=element, area=area):
                element.value = str(area.value)
                element.callback(element.value)

            dom.on(area, "input", on_text)
        elif isinstance(element, widgets.Button):
            button = dom.el("button", parent, element.label, cls="pyb2d3-wide")
            dom.on(button, "click", lambda e, element=element: element.callback())
        elif isinstance(element, (widgets.Dropdown, widgets.RadioButtons)):
            options = list(element.options)
            row = dom.el("label", parent, cls="pyb2d3-slider")
            dom.el("span", row, element.label)
            select = dom.el("select", row)
            for i, option in enumerate(options):
                opt = dom.el("option", select, str(option), value=i)
                if option == element.value:
                    opt.selected = True

            def on_change(e, element=element, select=select, options=options):
                element.value = options[int(select.value)]
                element.callback(element.value)

            dom.on(select, "change", on_change)
