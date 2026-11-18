"""A laser beam bouncing off the walls and boxes of a room."""

import math
import random

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

ROOM = 10  # half size of the room (m)
N_BOXES = 10
N_REFLECTIONS = 3
RAY_LENGTH = 2 * math.sqrt(2) * ROOM  # the diagonal of the room: long enough to hit a wall
LASER_COLOR = (255, 40, 40)


@register_sample("Queries", "Mirror", video=True)
class Mirror(SampleBase):
    """A laser beam reflected up to three times, from repeated cast_ray_closest calls
    and the surface normals of the hits.

    Mouse: drag and turn the yellow laser box (or the other boxes) to aim the beam.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.create_room()
        self.create_laser()
        self.create_boxes()
        # a stiff mouse joint: the dragged bodies follow the mouse closely
        self.mouse_joint_hertz = 10000
        self.mouse_joint_force_multiplier = 10000.0

    def create_room(self):
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=ROOM, hy=ROOM))

    def create_laser(self):
        """a yellow box, the beam leaves it at its top end"""
        self.laser = self.world.create_dynamic_body(
            linear_damping=10, angular_damping=10, rotation=math.pi / 2.1
        )
        material = b2d.surface_material(
            restitution=0.5, custom_color=b2d.rgb_to_hex_color(255, 240, 40)
        )
        self.laser.create_shape(
            b2d.shape_def(density=1, material=material), b2d.box(hx=0.4, hy=1.0)
        )

    def create_boxes(self):
        """the boxes the beam bounces off, at random positions and angles"""
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
            # no mouse when rendering the docs video: turn the laser to get some movement
            self.laser.apply_torque(2, wake=True)

    def post_debug_draw(self):
        # start just inside the top end of the laser (a ray starting inside a shape
        # does not hit it), pointing along the laser's y axis
        start = self.laser.world_point((0, 1 - 1e-5))
        angle = self.laser.angle + math.pi / 2
        direction = b2d.Vec2(math.cos(angle), math.sin(angle))

        for _ in range(1 + N_REFLECTIONS):
            hit = self.world.cast_ray_closest(origin=start, translation=direction * RAY_LENGTH)
            if not hit.hit:
                return
            self.debug_draw.draw_segment(start, hit.point, color=LASER_COLOR)
            direction = b2d.reflect(direction, hit.normal)  # mirrored at the surface
            start = hit.point

    def aabb(self):
        return b2d.aabb(lower_bound=(-ROOM, -ROOM), upper_bound=(ROOM, ROOM))
