"""100 rays cast from a ball in all directions, each drawn up to its closest hit."""

import math
import random

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

ROOM = 10  # half size of the room (m)
N_BOXES = 10
N_RAYS = 100
BALL_RADIUS = 1
RAY_LENGTH = 2 * math.sqrt(2) * ROOM  # the diagonal of the room: long enough to hit a wall
RAY_COLOR = (255, 255, 125)


@register_sample("Queries", "Raycast")
class Raycast(SampleBase):
    """100 rays cast from a ball in all directions with world.cast_ray_closest,
    each drawn up to the closest hit.

    Mouse: drag the ball (or a box) and watch the rays follow.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.create_room()
        self.create_ball()
        self.create_boxes()
        # a stiff mouse joint: the dragged bodies follow the mouse closely
        self.mouse_joint_hertz = 10000
        self.mouse_joint_force_multiplier = 10000.0

    def create_room(self):
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=ROOM, hy=ROOM))

    def create_ball(self):
        self.ball = self.world.create_dynamic_body(linear_damping=10, angular_damping=10)
        self.ball.create_shape(
            b2d.shape_def(density=1, material=b2d.surface_material(restitution=0.5)),
            b2d.circle(radius=BALL_RADIUS),
        )

    def create_boxes(self):
        """boxes at random positions and angles that block the rays"""
        for _ in range(N_BOXES):
            box = self.world.create_dynamic_body(
                position=(random.uniform(-ROOM, ROOM), random.uniform(-ROOM, ROOM)),
                rotation=random.uniform(0, 2 * math.pi),
                linear_damping=10,
                angular_damping=10,
            )
            box.create_shape(
                b2d.shape_def(density=1, material=b2d.surface_material(restitution=0.5)),
                b2d.box(hx=0.5, hy=1.0),
            )

    def pre_update(self, dt):
        if self.frontend.settings.headless:
            # no mouse when rendering the docs video: push the ball to get some movement
            self.ball.apply_force_to_center((40, -40), wake=True)

    def post_debug_draw(self):
        # the rays start at the center of the ball: a ray starting inside a shape does
        # not hit it, so the ball does not block its own rays
        center = self.ball.position
        for i in range(N_RAYS):
            angle = self.ball.angle + 2 * math.pi * i / N_RAYS
            direction = b2d.Vec2(math.cos(angle), math.sin(angle))
            hit = self.world.cast_ray_closest(origin=center, translation=direction * RAY_LENGTH)
            if hit.hit:
                # draw from the surface of the ball on
                start = center + direction * BALL_RADIUS
                self.debug_draw.draw_segment(start, hit.point, color=RAY_COLOR)

    def aabb(self):
        return b2d.aabb(lower_bound=(-ROOM, -ROOM), upper_bound=(ROOM, ROOM))
