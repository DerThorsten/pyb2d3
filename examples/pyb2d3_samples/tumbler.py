"""A slowly turning box tumbles 2000 small colorful capsules."""

import random

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

BOX_SIZE = 20  # inner width / height of the tumbler (m)
WALL = 1  # wall thickness (m)
MOTOR_SPEED = 0.1  # rad / s
N_CAPSULES = 2000
CAPSULE_RADIUS = 0.1
CAPSULE_LENGTH = 0.2


@register_sample("Demos", "Tumbler", video=True)
class Tumbler(SampleBase):
    """A box turned slowly by a revolute joint motor, tumbling 2000 small capsules.

    Keys: hold g to switch gravity off.
    Mouse: double click for an explosion, triple click to pull bodies in.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_tumbler()
        self.create_capsules()

    def create_tumbler(self):
        """a box of four walls on a motor driven revolute joint"""
        tumbler = self.world.create_dynamic_body(linear_damping=0.1, angular_damping=0.1)
        wall_def = b2d.shape_def(
            density=5, material=b2d.surface_material(restitution=0.5, friction=0.5)
        )
        h = BOX_SIZE / 2
        tumbler.create_shape(wall_def, b2d.box(WALL / 2, h, center=(-h, 0)))  # left
        tumbler.create_shape(wall_def, b2d.box(WALL / 2, h, center=(h, 0)))  # right
        tumbler.create_shape(wall_def, b2d.box(h, WALL / 2, center=(0, h)))  # top
        tumbler.create_shape(wall_def, b2d.box(h, WALL / 2, center=(0, -h)))  # bottom

        # the motor is strong enough to turn the box however the capsules lie
        self.world.create_revolute_joint(
            body_a=self.anchor_body,
            body_b=tumbler,
            enable_motor=True,
            motor_speed=MOTOR_SPEED,
            max_motor_torque=50000.0,
        )

    def create_capsules(self):
        """capsules with random colors at random positions inside the box"""
        r = BOX_SIZE / 2 - CAPSULE_RADIUS
        capsule = b2d.capsule((0, 0), (CAPSULE_LENGTH, 0), radius=CAPSULE_RADIUS)
        for _ in range(N_CAPSULES):
            body = self.world.create_dynamic_body(
                position=(random.uniform(-r, r), random.uniform(-r, r)), linear_damping=0.9
            )
            material = b2d.surface_material(
                restitution=0.5, friction=0.5, custom_color=b2d.random_hex_color()
            )
            body.create_shape(b2d.shape_def(density=1, material=material), capsule)

    def on_key_down(self, event):
        if event.key == "g":
            self.world.gravity = (0, 0)

    def on_key_up(self, event):
        if event.key == "g":
            self.world.gravity = (0, -10)

    def on_double_click(self, event):
        self.world.explode(position=event.world_position, radius=20, impulse_per_length=10)

    def on_triple_click(self, event):
        self.world.explode(position=event.world_position, radius=20, impulse_per_length=-10)

    def aabb(self):
        return b2d.aabb(lower_bound=(-20, -20), upper_bound=(20, 20))
