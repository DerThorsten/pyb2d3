"""Every shape type in a box: circles, capsules, (rounded) boxes, polygons and compounds."""

import math
import random

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

BOX = 10  # half size of the box (m)
MARGIN = 2  # bodies start this far from the walls
N_ROUNDS = 4  # how often each kind of body is created
N_TINY_BALLS = 400


def regular_polygon(radius, n_corners, y_scale=1.0):
    """the corners of a regular polygon (triangle, pentagon, ...), optionally squashed"""
    angles = [2 * math.pi * i / n_corners for i in range(n_corners)]
    return [(radius * math.cos(a), y_scale * radius * math.sin(a)) for a in angles]


# each kind of body: the shapes it is made of (several shapes: a compound body)
BODY_KINDS = {
    "ball": [b2d.circle(radius=1)],
    "capsule": [b2d.capsule(center1=(-0.5, 0), center2=(0.5, 0), radius=0.5)],
    "rectangle": [b2d.box(hx=0.5, hy=1.0)],
    "rounded rectangle": [b2d.box(hx=0.5, hy=1.0, radius=0.5)],
    "triangle": [b2d.polygon(points=[(-0.5, -0.5), (0.5, -0.5), (0, 0.5)], radius=0.1)],
    "pentagon": [b2d.polygon(points=regular_polygon(0.5, 5), radius=0.1)],
    "hexagon": [b2d.polygon(points=regular_polygon(0.5, 6), radius=0.1)],
    "flat octagon": [b2d.polygon(points=regular_polygon(2.5, 8, y_scale=0.5), radius=0.1)],
    "plus": [b2d.box(hx=0.5, hy=1.0), b2d.box(hx=1.0, hy=0.5)],
    "lollipop": [b2d.circle(radius=0.5, center=(0, 0.5)), b2d.box(0.1, 1.0, center=(0, -0.5))],
    "dumbbell": [
        b2d.box(hx=0.1, hy=1.1),
        b2d.circle(radius=0.5, center=(0, 1.5)),
        b2d.circle(radius=0.5, center=(0, -1.5)),
    ],
}


@register_sample("Demos", "Shapes")
class Shapes(SampleBase):
    """All shape types in a box: circles, capsules, (rounded) boxes, convex polygons and
    compound bodies made of several shapes, plus 400 small balls.

    Mouse: drag a body, double click for an explosion, triple click to pull bodies in.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=BOX, hy=BOX))
        for _ in range(N_ROUNDS):
            for shapes in BODY_KINDS.values():
                self.create_body(shapes)
        for _ in range(N_TINY_BALLS):
            self.create_body([b2d.circle(radius=0.2)])

    def create_body(self, shapes):
        """a body with a random color at a random position, made of `shapes`"""
        r = BOX - MARGIN
        body = self.world.create_dynamic_body(
            position=(random.uniform(-r, r), random.uniform(-r, r)),
            linear_damping=0.2,
            angular_damping=0.2,
        )
        material = b2d.surface_material(restitution=0.5, custom_color=b2d.random_hex_color())
        shape_def = b2d.shape_def(density=1, material=material)
        for shape in shapes:
            body.create_shape(shape_def, shape)

    def on_double_click(self, event):
        self.world.explode(position=event.world_position, radius=7, impulse_per_length=20)

    def on_triple_click(self, event):
        # a negative impulse pulls the bodies towards the click
        self.world.explode(position=event.world_position, radius=7, impulse_per_length=-20)

    def aabb(self):
        r = BOX + 0.01
        return b2d.aabb(lower_bound=(-r, -r), upper_bound=(r, r))
