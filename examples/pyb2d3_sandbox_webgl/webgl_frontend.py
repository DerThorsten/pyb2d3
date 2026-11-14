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
import time
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
  if (e.key.startsWith("Arrow") || e.key === " ") e.preventDefault();
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
        self.update_frontend_logic()
        if self.sample is not None:
            if self._single_step:
                self._single_step = False
                self.update_physics_single_step()
            elif not self._is_paused:
                self.update_physics()

            gl.glViewport(0, 0, *self._pixel_size)
            self.draw_physics()
            self._labels.flush()
        self._count_fps()
        return True

    def _count_fps(self):
        """update the fps display about twice a second"""
        self._fps_frames += 1
        now = time.perf_counter()
        if now - self._fps_t0 >= 0.5:
            fps = self._fps_frames / (now - self._fps_t0)
            self._fps_frames = 0
            self._fps_t0 = now
            self._stats.textContent = f"{fps:.0f} fps"

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
        self._stats = dom.el("span", row, "", cls="pyb2d3-stats")

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

        # the sample's widgets (filled by add_widget)
        section = dom.el("section", panel, cls="pyb2d3-section")
        self._sample_title = dom.el("h3", section, "")
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
        if self.is_paused():
            self.set_running()
        else:
            self.set_paused()
        paused = self.is_paused()
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
        """show the title of the new sample"""
        self._sample_title.textContent = self.sample_title

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
