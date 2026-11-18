"""Newton's cradle: ten elastic balls on ropes pass the momentum along."""

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

N_BALLS = 10
SPACING = 2  # distance between the ropes (m)
RADIUS = 0.85  # a bit smaller than SPACING / 2: a small gap between the resting balls
ROPE_LENGTH = 10


@register_sample("Demos", "Newton's Cradle", video=True)
class NewtonsCradle(SampleBase):
    """Newton's cradle: ten elastic balls on rigid distance joints pass the momentum along.

    Keys: a adds a loose ball at the position of the first ball.
    Mouse: drag a ball sideways and let it go.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        for i in range(N_BALLS):
            ball = self.create_ball(x=SPACING * i)
            anchor = self.world.create_static_body(position=(SPACING * i, ROPE_LENGTH))
            # a distance joint without spring: a rigid rope
            self.world.create_distance_joint(
                body_a=ball, body_b=anchor, length=ROPE_LENGTH, enable_spring=False
            )
        # push the last ball to start the cradle
        ball.apply_linear_impulse_to_center((-10, 0), wake=True)

    def create_ball(self, x):
        """an elastic (restitution 1) frictionless ball at (x, 0)"""
        ball = self.world.create_dynamic_body(position=(x, 0), linear_damping=0.1)
        material = b2d.surface_material(
            restitution=1.0, friction=0.0, custom_color=b2d.hex_color(100, 0, 200)
        )
        ball.create_shape(b2d.shape_def(density=1, material=material), b2d.circle(radius=RADIUS))
        return ball

    def on_key_down(self, event):
        if event.key == "a":
            self.create_ball(x=0)

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-(ROPE_LENGTH + SPACING), 0),
            upper_bound=(N_BALLS * SPACING + ROPE_LENGTH, ROPE_LENGTH + SPACING),
        )
