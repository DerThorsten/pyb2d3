# +
import pyb2d3 as b2d
from pyb2d3_sandbox.sample_base import SampleBase
import random


try:
    import examples_common  # noqa: F401, E402
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import examples_common  # noqa: F401, E402


class Tumbler(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)

        # physical world
        box_diameter = 20
        wall_thickness = 1

        self.wall_thickness = wall_thickness
        self.box_diameter = box_diameter

        anchor_body = self.world.create_static_body(position=(0, 0))
        self.tumbler_body = self.world.create_dynamic_body(
            position=(0, 0), linear_damping=0.1, angular_damping=0.1
        )

        wall_thickness / 2

        left = b2d.box(
            hx=wall_thickness / 2,
            hy=box_diameter / 2,
            center=(-box_diameter / 2, 0),
            rotation=0,
        )
        right = b2d.box(
            hx=wall_thickness / 2,
            hy=box_diameter / 2,
            center=(box_diameter / 2, 0),
            rotation=0,
        )
        top = b2d.box(
            hx=box_diameter / 2,
            hy=wall_thickness / 2,
            center=(0, box_diameter / 2),
            rotation=0,
        )
        bottom = b2d.box(
            hx=box_diameter / 2,
            hy=wall_thickness / 2,
            center=(0, -box_diameter / 2),
            rotation=0,
        )

        material = b2d.surface_material(restitution=0.5, friction=0.5)

        self.tumbler_body.create_shape(b2d.shape_def(density=5, material=material), left)

        self.tumbler_body.create_shape(b2d.shape_def(density=5, material=material), right)
        self.tumbler_body.create_shape(b2d.shape_def(density=5, material=material), top)
        self.tumbler_body.create_shape(b2d.shape_def(density=5, material=material), bottom)

        # add a revolute joint to the tumbler body
        self.world.create_revolute_joint(
            body_a=anchor_body,
            body_b=self.tumbler_body,
            enable_motor=True,
            motor_speed=0.1,
            max_motor_torque=50000.0,
        )

        # add a bunch of capsules
        n_capsules = 2000
        self.capsule_radius = 0.1
        self.capsule_length = 0.2
        # self.capsule_bodies = b2d.Bodies()
        for i in range(n_capsules):
            # radom position in the tumbler
            x = random.uniform(
                -box_diameter / 2 + self.capsule_radius,
                box_diameter / 2 - self.capsule_radius,
            )
            y = random.uniform(
                -box_diameter / 2 + self.capsule_radius,
                box_diameter / 2 - self.capsule_radius,
            )

            capsule_body = self.world.create_dynamic_body(
                position=(x, y),
                linear_damping=0.9,
            )
            material = b2d.surface_material(
                restitution=0.5,
                friction=0.5,
                custom_color=b2d.rgb_to_hex_color(
                    random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
                ),
            )
            capsule_body.create_shape(
                b2d.shape_def(density=1, material=material, enable_contact_events=True),
                b2d.capsule((0, 0), (self.capsule_length, 0), radius=self.capsule_radius),
            )

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


if __name__ == "__main__":
    Tumbler.run()
