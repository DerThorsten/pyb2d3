"""world.cast_ray with a Python callback: a laser ray passes green boxes, blue boxes shorten it."""

import math
import random

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

ROOM = 10  # half size of the room (m)
N_BOXES = 20
RAY_LENGTH = 2 * math.sqrt(2) * ROOM  # the diagonal of the room: long enough to hit a wall

# collision categories (one bit each); the ray only looks for green and blue boxes
LASER = 0x0002
GREEN = 0x0004
BLUE = 0x0008
GREEN_COLOR = (40, 240, 40)
BLUE_COLOR = (40, 40, 240)


@register_sample("Queries", "Cast Ray Callback")
class CastRayCallback(SampleBase):
    """world.cast_ray with a Python callback and a query filter: the yellow laser's ray
    passes through green boxes and is clipped to 20% at blue boxes (callback return values).

    Mouse: drag and turn the laser (or the boxes) to see which hits are reported.
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
        """a yellow box, the ray leaves it at its top end"""
        self.laser = self.world.create_dynamic_body(
            linear_damping=10, angular_damping=10, rotation=math.pi / 2.1
        )
        material = b2d.surface_material(
            restitution=0.5, custom_color=b2d.rgb_to_hex_color(255, 240, 40)
        )
        self.laser.create_shape(
            b2d.shape_def(
                density=1, material=material, filter=b2d.make_filter(category_bits=LASER)
            ),
            b2d.box(hx=0.4, hy=1.0),
        )

    def create_boxes(self):
        """green and blue boxes at random positions and angles"""
        for i in range(N_BOXES):
            category, color = (GREEN, GREEN_COLOR) if i % 2 == 0 else (BLUE, BLUE_COLOR)
            box = self.world.create_dynamic_body(
                position=(random.uniform(-ROOM, ROOM), random.uniform(-ROOM, ROOM)),
                rotation=random.uniform(0, 2 * math.pi),
                linear_damping=10,
                angular_damping=10,
            )
            material = b2d.surface_material(
                restitution=0.5, custom_color=b2d.rgb_to_hex_color(*color)
            )
            box.create_shape(
                b2d.shape_def(
                    density=1, material=material, filter=b2d.make_filter(category_bits=category)
                ),
                b2d.box(hx=0.5, hy=1.0),
            )

    def pre_update(self, dt):
        if self.frontend.settings.headless:
            # no mouse when rendering the docs video: turn the laser to get some movement
            self.laser.apply_torque(2, wake=True)

    def post_debug_draw(self):
        start = self.laser.world_point((0, 1 - 1e-5))  # just inside the top end of the laser
        angle = self.laser.angle + math.pi / 2  # along the laser's y axis
        translation = b2d.Vec2(math.cos(angle), math.sin(angle)) * RAY_LENGTH

        def callback(shape, point, normal, fraction):
            """called for every hit (in no particular order); the return value controls
            the rest of the cast: -1 ignore this hit, 0 stop, 1 continue, a fraction:
            continue, but only up to that fraction of the ray"""
            if shape.filter.category_bits == GREEN:
                self.debug_draw.draw_segment(start, point, color=GREEN_COLOR)
                return 1
            # blue: often one returns `fraction` here (closest hit), but we keep going
            # with a ray "weakened" to 20% of its length
            self.debug_draw.draw_segment(start, point, color=BLUE_COLOR)
            return 0.2

        # the mask skips the walls and the laser itself
        query_filter = b2d.query_filter(mask_bits=GREEN | BLUE)
        self.world.cast_ray(start, translation, query_filter=query_filter, callback=callback)

    def aabb(self):
        return b2d.aabb(lower_bound=(-ROOM, -ROOM), upper_bound=(ROOM, ROOM))
