"""Many bodies of all drawn shape types: a stress test for drawing (and the draw benchmark)."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import destroy_bodies, hsv_colors

# shape type -> how a body of this type is built (half size ~0.4)
SHAPE_TYPES = ["mixed", "circles", "boxes", "rounded boxes", "polygons", "capsules"]
HEXAGON = [(0.4 * math.cos(a), 0.4 * math.sin(a)) for a in np.linspace(0.0, 2.0 * math.pi, 7)[:-1]]
PALETTE = [int(c) for c in hsv_colors(np.linspace(0.0, 1.0, 8, endpoint=False), 0.55, 0.95)]


def make_shape(kind):
    """the box2d shape of one body of `kind` (not "mixed")"""
    if kind == "circles":
        return b2d.circle(radius=0.4)
    if kind == "boxes":
        return b2d.box(0.4, 0.3)
    if kind == "rounded boxes":
        return b2d.box(0.3, 0.2, radius=0.1)
    if kind == "polygons":
        return b2d.polygon(points=HEXAGON)
    return b2d.capsule((-0.3, 0.0), (0.3, 0.0), 0.2)


class BatchManyShapes(SampleBase):
    """Thousands of bodies of every drawn shape type (circles, boxes, rounded boxes,
    polygons, capsules) in a box: a stress test for drawing.

    Sliders: body count. Dropdown: one shape type or all mixed.
    Checkboxes: joints (each body linked to its right neighbor: joints draw lines
    and points too), freeze (no physics steps, the bodies are still drawn: the
    frame time is drawing only).
    Hint: the fps overlay (browser) splits a frame into physics and draw.
    """

    spacing = 1.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.count = 2000
        self.kind = "mixed"
        self.with_joints = False
        self.frozen = False
        self.bodies = b2d.Bodies()
        self.walls = None
        self.build()
        for widget in (
            widgets.IntSlider("bodies", 500, 10000, 500, self.count, self.set_count),
            widgets.Dropdown("shapes", SHAPE_TYPES, self.kind, self.set_kind),
            widgets.Checkbox("joints", self.with_joints, self.set_joints),
            widgets.Checkbox("freeze (draw only)", self.frozen, self.set_frozen),
        ):
            self.frontend.add_widget(widget)

    def side(self):
        """bodies per row of the starting grid (a square-ish block)"""
        return int(math.ceil(math.sqrt(self.count)))

    def half_width(self):
        """half width of the box: the grid plus some room"""
        return 0.5 * self.side() * self.spacing + 2.0

    def aabb(self):
        w = self.half_width()
        return b2d.aabb(lower_bound=(-w - 1.0, -1.0), upper_bound=(w + 1.0, 2.0 * w + 1.0))

    def build(self):
        """the box (static segments: lines) and the bodies on a grid"""
        destroy_bodies(self, self.bodies)
        if self.walls is not None:
            self.walls.destroy()
        w = self.half_width()
        self.walls = self.world.create_static_body()
        wall_def = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.SlateGray))
        corners = [(-w, 2.0 * w), (-w, 0.0), (w, 0.0), (w, 2.0 * w)]
        for p, q in zip(corners[:-1], corners[1:]):
            self.walls.create_shape(wall_def, b2d.segment(p, q))

        side = self.side()
        kinds = SHAPE_TYPES[1:] if self.kind == "mixed" else [self.kind]
        shapes = {kind: make_shape(kind) for kind in kinds}
        bodies = b2d.Bodies()
        for i in range(self.count):
            row, column = divmod(i, side)
            position = ((column - 0.5 * (side - 1)) * self.spacing, 0.6 + row * self.spacing)
            body = self.world.create_dynamic_body(position=position, rotation=b2d.make_rot(0.3 * i))
            kind = kinds[i % len(kinds)]
            material = b2d.surface_material(friction=0.5, custom_color=PALETTE[i % len(PALETTE)])
            body.create_shape(b2d.shape_def(density=1.0, material=material), shapes[kind])
            if self.with_joints and column > 0:
                # a soft distance joint to the left neighbor (drawn as a line + points)
                left = bodies[i - 1]
                self.world.create_distance_joint(
                    body_a=left,
                    body_b=body,
                    length=self.spacing,
                    enable_spring=True,
                    hertz=4.0,
                    damping_ratio=0.5,
                )
            bodies.append(body)
        self.bodies = bodies

    def set_count(self, value):
        """slider: number of bodies"""
        self.count = int(value)
        self.build()

    def set_kind(self, value):
        """dropdown: one shape type or all mixed"""
        self.kind = value
        self.build()

    def set_joints(self, value):
        """checkbox: link the bodies with joints"""
        self.with_joints = bool(value)
        self.build()

    def set_frozen(self, value):
        """checkbox: stop stepping the world (drawing only)"""
        self.frozen = bool(value)

    def update(self, dt):
        """the world step, skipped while frozen"""
        if not self.frozen:
            super().update(dt)

    def post_debug_draw(self):
        """the body count"""
        w = self.half_width()
        state = "frozen" if self.frozen else "running"
        self.debug_draw.draw_string(
            (-w, 2.0 * w + 0.5), f"{len(self.bodies)} {self.kind}, {state}", b2d.HexColor.White
        )
