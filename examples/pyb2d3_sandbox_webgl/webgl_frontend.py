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
import inspect
import json
import linecache
import os
import sys
import time
import traceback
from dataclasses import dataclass

import pyjs
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
    MouseMoveEvent,
    MouseUpEvent,
    MouseWheelEvent,
)
from pyb2d3_sandbox_opengl.debug_draw_gl import Camera, GLDebugDraw

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


# ---------------------------------------------------------------------------
# WebGL2 context (emscripten's html5 API via ctypes: the GL functions PyOpenGL
# calls use emscripten's current context)
# ---------------------------------------------------------------------------


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


def create_webgl2_context(canvas):
    """create a WebGL2 context on `canvas` and make it current (for PyOpenGL)"""
    pyjs.set_canvas(canvas)
    lib = ctypes.CDLL(None)
    attrs = _WebGLContextAttributes()
    lib.emscripten_webgl_init_context_attributes(ctypes.byref(attrs))
    attrs.majorVersion = 2
    attrs.minorVersion = 0
    attrs.alpha = False
    attrs.depth = False
    attrs.stencil = False
    attrs.antialias = True

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


# ---------------------------------------------------------------------------
# DOM helpers
# ---------------------------------------------------------------------------

# one listener per element + event; forwards the event to python. Pointer /
# key events are reduced to plain values in JS (fewer JS <-> python calls).
_CANVAS_EVENTS_JS = """
const mods = (e) => (e.ctrlKey ? 1 : 0) | (e.shiftKey ? 2 : 0) | (e.metaKey ? 4 : 0) | (e.altKey ? 8 : 0);
canvas.style.touchAction = "none";
canvas.addEventListener("pointerdown", (e) => {
  if (e.button !== 0) return;
  canvas.setPointerCapture(e.pointerId);
  canvas.focus();
  cb("down", e.offsetX, e.offsetY, 0, 0, "", 0);
});
canvas.addEventListener("pointermove", (e) => {
  cb("move", e.offsetX, e.offsetY, e.movementX, e.movementY, "", e.buttons);
});
canvas.addEventListener("pointerup", (e) => {
  if (e.button !== 0) return;
  cb("up", e.offsetX, e.offsetY, 0, 0, "", 0);
});
canvas.addEventListener("pointerenter", () => cb("enter", 0, 0, 0, 0, "", 0));
canvas.addEventListener("pointerleave", () => cb("leave", 0, 0, 0, 0, "", 0));
canvas.addEventListener("wheel", (e) => {
  e.preventDefault();
  cb("wheel", e.offsetX, e.offsetY, Math.sign(e.deltaY), 0, "", 0);
}, { passive: false });
canvas.addEventListener("keydown", (e) => {
  if (e.repeat) return;
  if (e.key.startsWith("Arrow") || e.key.startsWith("Page") || e.key === " ") e.preventDefault();
  cb("keydown", 0, 0, 0, 0, e.key, mods(e));
});
canvas.addEventListener("keyup", (e) => cb("keyup", 0, 0, 0, 0, e.key, 0));
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
        span.style.cssText = (
            f"display:block;left:{screen_pos.x:.0f}px;top:{screen_pos.y:.0f}px;color:rgb({r},{g},{b})"
        )

    def flush(self):
        """hide the labels not used in this frame"""
        for span in self.spans[self.used:]:
            span.style.display = "none"
        self.used = 0


# ---------------------------------------------------------------------------
# the frontend
# ---------------------------------------------------------------------------


class WebglFrontend(FrontendBase):
    @dataclass
    class Settings(FrontendBase.Settings):
        canvas_id: str = "canvas"
        panel_id: str = "panel"
        labels_id: str = "labels"

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

    # -- setup -------------------------------------------------------------

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

        create_webgl2_context(self.canvas)
        self.debug_draw = GLDebugDraw(self.camera, draw_text=self._labels.add)
        self.debug_draw.draw_shapes = True
        self.debug_draw.draw_joints = True

        self._resize()
        self._build_panel()
        self._fps_overlay = self._create_fps_overlay()
        self._connect_canvas_events()
        self.ui_is_ready()  # creates the sample

        self._loop = pyjs.request_animation_frame_loop(self._frame)

    def stop_loop(self):
        """stop rendering (e.g. before the page starts another frontend)"""
        if self._loop is not None:
            self._loop.cancel()
            self._loop = None

    # -- frames --------------------------------------------------------------

    def _resize(self):
        """match the drawing buffer to the canvas' CSS size (x devicePixelRatio)"""
        css_w = max(1, int(self.canvas.clientWidth))
        css_h = max(1, int(self.canvas.clientHeight))
        dpr = float(pyjs.js.devicePixelRatio or 1.0)
        pixel_size = (max(1, round(css_w * dpr)), max(1, round(css_h * dpr)))
        if pixel_size != self._pixel_size:
            self._pixel_size = pixel_size
            self.canvas.width, self.canvas.height = pixel_size
        # the camera works in CSS px (the coordinates of the pointer events)
        self.camera.set_size(css_w, css_h)

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

    # -- the page: events for the code editor (examples/web) -------------------

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
        self._dispatch("pyb2d3-sample", {"key": entry.key if entry else None, "file": file, "line": line})

    def samples_in_file(self, path):
        """the registered samples defined in the python file `path`, as JSON:
        [{key, first, last}] with the line range of each sample class (the page's
        Run button starts the sample the editor cursor is in)"""
        path = os.path.abspath(path)
        linecache.checkcache(path)  # the file may have been edited + re-imported
        found = []
        for entry in self.registry:
            try:
                if os.path.abspath(inspect.getsourcefile(entry.cls)) != path:
                    continue
                lines, first = inspect.getsourcelines(entry.cls)
            except (OSError, TypeError):
                continue
            found.append({"key": entry.key, "first": first, "last": first + len(lines) - 1})
        return json.dumps(found)

    def reload_code(self, paths, key=None):
        """re-import the modules of the python files `paths` (edited in the
        page and written to the file system) and start the sample `key`
        ("Category/Name", default: the current one) with the new code; the
        modules of both samples are always re-imported (last). Errors are
        reported like errors of the sample."""
        if not key and self.sample_entry is not None:
            key = self.sample_entry.key
        try:
            target = self.registry.get(key).cls if key else self.sample_class
        except KeyError:
            key, target = None, self.sample_class
        # the samples' own modules last: they import from the edited helpers
        last = []
        for cls in (target, self.sample_class):
            module = sys.modules.get(cls.__module__)
            if module is not None and module not in last:
                last.append(module)
        paths = {os.path.abspath(p) for p in paths}
        modules = [
            m for m in list(sys.modules.values())
            if m not in last and getattr(m, "__file__", None)
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
            self._fps_overlay.textContent = (
                f"{fps:.0f} fps · physics {physics_ms:.1f} ms · draw {draw_ms:.1f} ms"
            )

    def _create_fps_overlay(self):
        """the fps counter: a small label in the top left corner of the canvas"""
        overlay = self._dom.el("div", self.canvas.parentElement, "", cls="pyb2d3-fps")
        style = overlay.style
        style.position = "absolute"
        style.top = "6px"
        style.left = "8px"
        style.padding = "2px 6px"
        style.borderRadius = "4px"
        style.background = "rgba(0, 0, 0, 0.45)"
        style.color = "#d9dce1"
        style.font = "12px monospace"
        style.pointerEvents = "none"
        return overlay

    # -- input ---------------------------------------------------------------

    def _connect_canvas_events(self):
        """forward the DOM events of the canvas to `_on_canvas_event`"""
        install = pyjs.js.Function("canvas", "cb", _CANVAS_EVENTS_JS)
        install(self.canvas, self._dom.callable(self._on_canvas_event))

    def _world(self, x, y):
        """CSS px of the canvas -> world position"""
        return self.camera.convert_screen_to_world(Vec2(float(x), float(y)))

    def _on_canvas_event(self, kind, x, y, a, b, key, flags):
        """a canvas event (reduced to plain values by _CANVAS_EVENTS_JS)"""
        if kind == "keydown" and str(key) in SAMPLE_KEYS:  # also while paused
            self.next_sample(SAMPLE_KEYS[str(key)])
            return
        if self.sample is None or self._is_paused:
            return
        if kind == "down":
            world = self._world(x, y)
            self.sample.on_mouse_down(MouseDownEvent(world_position=world))
            self._multi_click_handler.handle_click(world_position=world)
        elif kind == "move":
            if int(flags) & 1:  # dragging with the primary button
                delta = self.camera.screen_delta_to_world_delta((float(a), float(b)))
                self.sample.on_mouse_move(
                    MouseMoveEvent(world_position=self._world(x, y), world_delta=delta)
                )
        elif kind == "up":
            self.sample.on_mouse_up(MouseUpEvent(world_position=self._world(x, y)))
        elif kind == "wheel":
            self.sample.on_mouse_wheel(
                MouseWheelEvent(world_position=self._world(x, y), delta=float(a))
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

    # -- camera (FrontendBase) ------------------------------------------------

    def center_sample(self, margin_px=10):
        """fit the sample's bounding box into the canvas"""
        aabb = self.sample.aabb()
        center = aabb.center()
        size = aabb.upper_bound - aabb.lower_bound
        aspect = float(self.camera.width) / float(self.camera.height)
        self.camera.center = center
        self.camera.zoom = max(0.5 * size.x / aspect, 0.5 * size.y)
        self.camera._matrix = None

    def drag_camera(self, delta):
        """move the view by a world delta"""
        self.camera.center -= (delta[0], delta[1])
        self.camera._matrix = None

    def change_zoom(self, delta):
        """zoom in / out"""
        self.camera.zoom = max(1.0, self.camera.zoom + delta)
        self.camera._matrix = None

    # -- the panel ------------------------------------------------------------

    def _build_panel(self):
        """sample list, controls, debug draw options, the sample's own widgets"""
        dom = self._dom
        panel = self.panel
        panel.textContent = ""

        # sample list
        if len(self.registry):
            section = dom.el("section", panel, cls="pyb2d3-section")
            dom.el("h3", section, "Sample")
            self._sample_select = dom.el("select", section)
            self._sample_classes = []
            for category in self.registry.categories():
                group = dom.el("optgroup", self._sample_select, label=category)
                for entry in self.registry.samples(category):
                    option = dom.el("option", group, entry.name, value=len(self._sample_classes))
                    if entry.cls is self.sample_class:
                        option.selected = True
                    self._sample_classes.append(entry.cls)
            dom.on(self._sample_select, "change", lambda e: self._on_select_sample())
            row = dom.el("div", section, cls="pyb2d3-row")
            previous = dom.el("button", row, "◀ Previous", title="previous sample (PageUp)")
            dom.on(previous, "click", lambda e: self.next_sample(-1))
            following = dom.el("button", row, "Next ▶", title="next sample (PageDown)")
            dom.on(following, "click", lambda e: self.next_sample(1))

        # controls
        section = dom.el("section", panel, cls="pyb2d3-section")
        dom.el("h3", section, "Controls")
        row = dom.el("div", section, cls="pyb2d3-row")
        self._play_button = dom.el("button", row, "Pause")
        dom.on(self._play_button, "click", lambda e: self._toggle_pause())
        self._step_button = dom.el("button", row, "Step", disabled="")
        dom.on(self._step_button, "click", lambda e: self._request_single_step())
        reset = dom.el("button", row, "Reset")
        dom.on(reset, "click", lambda e: self.stop())

        self._slider(
            dom, section, "Hertz", 1, 120, 1, self.settings.hertz,
            lambda v: setattr(self.settings, "hertz", v), fmt="{:.0f} Hz",
        )
        self._slider(
            dom, section, "Substeps", 0, 30, 1, self.settings.substeps,
            lambda v: setattr(self.settings, "substeps", int(v)), fmt="{:.0f}",
        )
        self._slider(
            dom, section, "Speed", -4, 4, 0.1, 0.0,
            lambda v: setattr(self.settings, "speed", speed_from_slider(v)),
            fmt_value=lambda v: f"{speed_from_slider(v):.2f}x",
        )

        # debug draw options
        section = dom.el("section", panel, cls="pyb2d3-section")
        dom.el("h3", section, "Debug draw")
        for name, label in DEBUG_DRAW_OPTIONS:
            self._checkbox(
                dom, section, label, bool(getattr(self.debug_draw, name)),
                lambda v, name=name: setattr(self.debug_draw, name, v),
            )

        # the sample: title, help text, its widgets (filled by add_widget)
        section = dom.el("section", panel, cls="pyb2d3-section")
        self._sample_title = dom.el("h3", section, "")
        self._sample_help = dom.el("p", section, "", cls="pyb2d3-help")
        dom.el("p", section, "mouse: drag bodies, drag the background to pan, wheel zooms", cls="pyb2d3-help")
        self._sample_widgets = dom.el("div", section)

    def _slider(self, dom, parent, label, lo, hi, step, value, callback, fmt="{:.2f}", fmt_value=None):
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

    def _on_select_sample(self):
        """the sample list changed"""
        self.set_sample(self._sample_classes[int(self._sample_select.value)])

    def _toggle_pause(self):
        """play / pause"""
        self._set_paused_ui(not self.is_paused())

    def _set_paused_ui(self, paused):
        """pause / run the simulation and update the play / step buttons"""
        if paused:
            self.set_paused()
        else:
            self.set_running()
        self._play_button.textContent = "Play" if paused else "Pause"
        self._step_button.disabled = not paused

    def _request_single_step(self):
        """one physics step in the next frame (while paused)"""
        self._single_step = True

    # -- the sample's widgets (FrontendBase) ----------------------------------

    def pre_new_sample(self, sample_class, sample_settings):
        """remove the widgets of the previous sample"""
        if getattr(self, "_sample_widgets", None) is not None:
            self._sample_widgets.textContent = ""
        self._sample_dom.clear()

    def post_new_sample(self, sample_class, sample_settings):
        """show the title and the help text of the new sample, select it in the
        sample list, put it into the URL"""
        self._sample_title.textContent = self.sample_title
        self._sample_help.textContent = sample_class.help_text()
        if sample_class in getattr(self, "_sample_classes", ()):
            self._sample_select.value = str(self._sample_classes.index(sample_class))
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
                dom, parent, element.label, element.min_value, element.max_value,
                element.step or (1 if is_int else 0.01), element.value, on_value,
                fmt="{:.0f}" if is_int else "{:.2f}",
            )
        elif isinstance(element, widgets.Checkbox):

            def on_check(v, element=element):
                element.value = v
                element.callback(v)

            self._checkbox(dom, parent, element.label, bool(element.value), on_check)
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
