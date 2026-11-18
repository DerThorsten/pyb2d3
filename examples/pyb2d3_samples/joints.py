"""Four basic joints side by side: revolute, prismatic, weld and spring distance joint."""

import math

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

HALF_WIDTH = 10  # half size of the shown region and the ground (m)
Y = 4  # height of the static anchors (m)


@register_sample("Demos", "Joints")
class Joints(SampleBase):
    """Four basic joints side by side: revolute, prismatic (45 degree axis), weld and spring distance joint.

    Mouse: drag the boxes to see how each joint constrains the motion.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.anchor_body.create_shape(
            b2d.shape_def(), b2d.segment((-HALF_WIDTH, 0), (HALF_WIDTH, 0))
        )
        self.create_revolute(x=-6)
        self.create_prismatic(x=-2)
        self.create_weld(x=0)
        self.create_distance(x=5)

    def create_revolute(self, x):
        """a pendulum: the box turns around the anchor, pinned at its top end"""
        anchor = self.world.create_static_body(position=(x, Y))
        box = self.world.create_dynamic_body(position=(x, Y - 2))
        box.create_shape(b2d.shape_def(), b2d.box(hx=0.5, hy=1.0))
        self.world.create_revolute_joint(body_a=anchor, body_b=box, local_anchor_b=(0, 1))
        box.apply_linear_impulse_to_center((10, 0))  # start with some movement

    def create_prismatic(self, x):
        """the box slides along a 45 degree axis through the anchor"""
        anchor = self.world.create_static_body(position=(x, Y))
        box = self.world.create_dynamic_body(position=(x, Y - 2))
        box.create_shape(b2d.shape_def(), b2d.box(hx=0.5, hy=0.5))
        self.world.create_prismatic_joint(
            body_a=anchor,
            body_b=box,
            # box2d >= 3.2: the slide axis is the x-axis of local frame A
            local_frame_a=b2d.transform(q=0.25 * math.pi),
            local_anchor_b=(0, 0),
        )
        box.apply_linear_impulse_to_center((0, 10))

    def create_weld(self, x):
        """a soft weld: the plank is glued to the anchor at its left end, but springy"""
        anchor = self.world.create_static_body(position=(x, Y))
        plank = self.world.create_dynamic_body(position=(x, Y))
        plank.create_shape(b2d.shape_def(), b2d.box(hx=2.0, hy=0.5))
        self.world.create_weld_joint(
            body_a=anchor, body_b=plank, local_anchor_b=(-2, 0), linear_hertz=20, angular_hertz=5
        )
        plank.apply_linear_impulse_to_center((10, 0))

    def create_distance(self, x):
        """a spring of rest length 1 between the anchor and the top of the box"""
        anchor = self.world.create_static_body(position=(x, Y))
        box = self.world.create_dynamic_body(position=(x, Y - 2))
        box.create_shape(b2d.shape_def(), b2d.box(hx=0.5, hy=1.0))
        self.world.create_distance_joint(
            body_a=anchor,
            body_b=box,
            local_anchor_b=(0, 1),
            length=1.0,
            enable_spring=True,
            hertz=5,
            damping_ratio=0.0,
        )
        box.apply_linear_impulse_to_center((10, 0))

    def aabb(self):
        r = HALF_WIDTH + 0.01
        return b2d.aabb(lower_bound=(-r, -r), upper_bound=(r, r))
