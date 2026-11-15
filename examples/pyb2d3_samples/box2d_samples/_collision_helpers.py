"""Shared helpers for the ports of box2d's collision and geometry samples."""

import math
import random
from types import SimpleNamespace

import pyb2d3 as b2d
from pyb2d3_sandbox import widgets

from ._common import Box2dSample

# b2d.HexColor values as plain ints: colors.White, colors.Cyan, ...
colors = SimpleNamespace(**{c.name: c.value for c in b2d.HexColor})


def random_float(lo=-1.0, hi=1.0):
    """box2d's RandomFloat() / RandomFloatRange(lo, hi)."""
    return random.uniform(lo, hi)


def octagon_points(w=1.0):
    b = w / (2.0 + math.sqrt(2.0))
    s = math.sqrt(2.0) * b
    return [
        (0.5 * s, 0.0), (0.5 * w, b), (0.5 * w, b + s), (0.5 * s, w),
        (-0.5 * s, w), (-0.5 * w, b + s), (-0.5 * w, b), (-0.5 * s, 0.0),
    ]  # fmt: skip


def with_position(transform, p):
    """`transform` moved to the world point `p` (keeps its rotation)."""
    return b2d.transform(p=p, q=transform.q)


def draw_geometry(debug_draw, shape, transform, color, radius=None):
    """Draw a Circle / Capsule / Segment / Polygon placed at `transform`."""
    tp = lambda p: b2d.transform_point(transform, p)  # noqa: E731
    if isinstance(shape, b2d.Circle):
        debug_draw.draw_solid_circle(with_position(transform, tp(shape.center)), shape.radius, color)
    elif isinstance(shape, b2d.Capsule):
        debug_draw.draw_solid_capsule(tp(shape.center1), tp(shape.center2), shape.radius, color)
    elif isinstance(shape, b2d.Segment):
        debug_draw.draw_segment(tp(shape.point1), tp(shape.point2), color)
    elif isinstance(shape, b2d.Polygon):
        r = shape.radius if radius is None else radius
        debug_draw.draw_solid_polygon(transform, shape.vertices, r, color)
    else:
        raise TypeError(f"cannot draw {shape!r}")


def draw_manifold(
    debug_draw,
    manifold,
    transform_a,
    line_color=colors.Violet,
    point_size=10.0,
    point_color=colors.Blue,
    show_ids=False,
    show_separation=False,
):
    """Contact points and normals of a local manifold (given in the frame of shape A)."""
    normal = b2d.rotate_vector(transform_a.q, manifold.normal)
    for mp in manifold.points:
        p1 = b2d.transform_point(transform_a, mp.point)
        debug_draw.draw_segment(p1, p1 + 0.5 * normal, line_color)
        debug_draw.draw_point(p1, point_size, point_color)
        if show_ids:
            debug_draw.draw_string(p1 + (0.05, -0.02), f"0x{mp.id:04x}", colors.White)
        if show_separation:
            debug_draw.draw_string(p1 + (0.05, 0.03), f"{mp.separation:.3f}", colors.White)


class TransformDragSample(Box2dSample):
    """A sample that moves a transform with the mouse.

    mouse button 1: drag, mouse button 1 + shift: rotate (as in the box2d samples).
    Subclasses map further modifiers to their own modes with `mouse_modes`.
    """

    mouse_modes = {None: "drag", "shift": "rotate"}
    drag_scale = 0.5
    rotate_scale = 1.0

    def __init__(self, frontend, settings, position=(0.0, 0.0), angle=0.0):
        super().__init__(frontend, settings)
        self.position = b2d.Vec2(*position)
        self.angle = angle
        self.mode = None
        self.start_point = b2d.Vec2(0, 0)
        self.base_position = self.position
        self.base_angle = angle

    @property
    def transform(self):
        return b2d.transform(p=self.position, q=b2d.make_rot(self.angle))

    def reset_transform(self):
        self.position = b2d.Vec2(0, 0)
        self.angle = 0.0

    def add_transform_widgets(self, labels=("x offset", "y offset", "angle")):
        x_label, y_label, angle_label = labels
        add = self.frontend.add_widget
        add(widgets.FloatSlider(x_label, -2.0, 2.0, 0.01, self.position.x, self._set_x))
        add(widgets.FloatSlider(y_label, -2.0, 2.0, 0.01, self.position.y, self._set_y))
        add(widgets.FloatSlider(angle_label, -math.pi, math.pi, 0.01, self.angle, self._set_angle))

    def _set_x(self, x):
        self.position = b2d.Vec2(x, self.position.y)

    def _set_y(self, y):
        self.position = b2d.Vec2(self.position.x, y)

    def _set_angle(self, angle):
        self.angle = angle

    def modifier(self):
        keys = self.pressed_keys()
        if "shift" in keys:
            return "shift"
        if "ctrl" in keys or "control" in keys:
            return "ctrl"
        return None

    def on_mouse_down(self, event):
        self.mode = self.mouse_modes.get(self.modifier())
        self.start_point = event.world_position
        self.base_position = self.position
        self.base_angle = self.angle

    def on_mouse_up(self, event):
        self.mode = None

    def on_mouse_move(self, event):
        d = event.world_position - self.start_point
        if self.mode == "drag":
            self.position = self.base_position + self.drag_scale * d
        elif self.mode == "rotate":
            self.angle = min(max(self.base_angle + self.rotate_scale * d.x, -math.pi), math.pi)


class ProxyPairSample(TransformDragSample):
    """Two shape proxies (point / segment / triangle / box) with a radius each.

    Shape A sits at the origin, shape B at the dragged transform.
    """

    shape_types = ("point", "segment", "triangle", "box")

    def __init__(self, frontend, settings, segment, box, type_a, type_b, radius_a, radius_b, **kwargs):
        super().__init__(frontend, settings, **kwargs)
        self.segment = segment
        self.triangle = b2d.polygon(points=[(-0.5, 0.0), (0.5, 0.0), (0.0, 1.0)])
        self.box = box
        self.type_a, self.type_b = type_a, type_b
        self.radius_a, self.radius_b = radius_a, radius_b
        self.show_indices = False

    def proxy_points(self, shape_type):
        if shape_type == "point":
            return [(0.0, 0.0)]
        if shape_type == "segment":
            return [self.segment.point1, self.segment.point2]
        return (self.triangle if shape_type == "triangle" else self.box).vertices

    @property
    def proxy_a(self):
        return b2d.make_proxy(self.proxy_points(self.type_a), self.radius_a)

    @property
    def proxy_b(self):
        return b2d.make_proxy(self.proxy_points(self.type_b), self.radius_b)

    def add_shape_widgets(self):
        add = self.frontend.add_widget
        types = list(self.shape_types)
        add(widgets.Dropdown("shape A", types, self.type_a, lambda v: setattr(self, "type_a", v)))
        add(widgets.FloatSlider("radius A", 0.0, 0.5, 0.01, self.radius_a, lambda v: setattr(self, "radius_a", v)))
        add(widgets.Dropdown("shape B", types, self.type_b, lambda v: setattr(self, "type_b", v)))
        add(widgets.FloatSlider("radius B", 0.0, 0.5, 0.01, self.radius_b, lambda v: setattr(self, "radius_b", v)))
        self.add_transform_widgets()
        add(widgets.Checkbox("show indices", self.show_indices, lambda v: setattr(self, "show_indices", v)))

    def draw_shape(self, shape_type, transform, radius, color):
        dd = self.debug_draw
        if shape_type == "point":
            if radius > 0.0:
                dd.draw_solid_circle(transform, radius, color)
            else:
                dd.draw_point(transform.p, 5.0, color)
        elif shape_type == "segment":
            p1 = b2d.transform_point(transform, self.segment.point1)
            p2 = b2d.transform_point(transform, self.segment.point2)
            if radius > 0.0:
                dd.draw_solid_capsule(p1, p2, radius, color)
            else:
                dd.draw_segment(p1, p2, color)
        else:
            polygon = self.triangle if shape_type == "triangle" else self.box
            dd.draw_solid_polygon(transform, polygon.vertices, radius, color)

    def draw_indices(self):
        if not self.show_indices:
            return
        for proxy, transform in ((self.proxy_a, b2d.Transform()), (self.proxy_b, self.transform)):
            for i, p in enumerate(proxy.points):
                self.debug_draw.draw_string(b2d.transform_point(transform, p), f" {i}", colors.White)


class BodySlotsSample(Box2dSample):
    """Up to `max_count` randomly placed bodies in a ring buffer of slots.

    Subclasses implement `create_shape(body, kind, slot)`; the shape in slot
    `ignore_index` is skipped by the queries.
    """

    max_count = 64
    ignore_index = 7

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.bodies = [None] * self.max_count
        self.body_index = 0

    def body_options(self, slot):
        return {}

    def create(self, kind):
        slot = self.body_index
        self.destroy_slot(slot)
        body = self.world.create_body(
            position=(random_float(-20.0, 20.0), random_float(0.0, 20.0)),
            rotation=random_float(-math.pi, math.pi),
            **self.body_options(slot),
        )
        self.create_shape(body, kind, slot)
        self.bodies[slot] = body
        self.body_index = (slot + 1) % self.max_count

    def create_n(self, kind, count=10):
        for _ in range(count):
            self.create(kind)

    def destroy_slot(self, slot):
        if self.bodies[slot] is not None:
            self.bodies[slot].destroy()
            self.bodies[slot] = None

    def destroy_first(self):
        for slot, body in enumerate(self.bodies):
            if body is not None:
                self.destroy_slot(slot)
                return

    def is_ignored(self, shape):
        ignored = self.bodies[self.ignore_index]
        return ignored is not None and shape.body == ignored

    def add_slot_widgets(self, labels):
        add = self.frontend.add_widget
        for kind, label in enumerate(labels):
            add(widgets.Button(label, lambda kind=kind: self.create(kind)))
            add(widgets.Button(f"10x {label}", lambda kind=kind: self.create_n(kind)))
        add(widgets.Button("Destroy Shape", self.destroy_first))

    def draw_ignore_label(self, text):
        ignored = self.bodies[self.ignore_index]
        if ignored is not None:
            self.debug_draw.draw_string(ignored.position - (0.2, 0.0), text, colors.White)

