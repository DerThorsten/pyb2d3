import pyb2d3 as b2d
from pyb2d3.samples import SampleBase


import random
import numpy as np
import time
import math


class Tumbler(SampleBase):
    def __init__(self):
        super().__init__()

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

        left = b2d.make_offset_box(
            hx=wall_thickness / 2,
            hy=box_diameter / 2,
            center=(-box_diameter / 2, 0),
            rotation=0,
        )
        right = b2d.make_offset_box(
            hx=wall_thickness / 2,
            hy=box_diameter / 2,
            center=(box_diameter / 2, 0),
            rotation=0,
        )
        top = b2d.make_offset_box(
            hx=box_diameter / 2,
            hy=wall_thickness / 2,
            center=(0, box_diameter / 2),
            rotation=0,
        )
        bottom = b2d.make_offset_box(
            hx=box_diameter / 2,
            hy=wall_thickness / 2,
            center=(0, -box_diameter / 2),
            rotation=0,
        )

        material = b2d.surface_material(restitution=0.5, friction=0.5)

        self.tumbler_body.create_shape(
            b2d.shape_def(density=5, material=material), left
        )

        self.tumbler_body.create_shape(
            b2d.shape_def(density=5, material=material), right
        )
        self.tumbler_body.create_shape(b2d.shape_def(density=5, material=material), top)
        self.tumbler_body.create_shape(
            b2d.shape_def(density=5, material=material), bottom
        )

        # add a revolute joint to the tumbler body
        self.world.create_revolute_joint(
            body_a=anchor_body,
            body_b=self.tumbler_body,
            enable_motor=True,
            motor_speed=0.1,
            max_motor_torque=50000.0,
        )

        # add a bunch of balls
        n_balls = 600
        self.ball_radius = 0.1
        for i in range(n_balls):

            # radom position in the tumbler
            x = random.uniform(
                -box_diameter / 2 + self.ball_radius,
                box_diameter / 2 - self.ball_radius,
            )
            y = random.uniform(
                -box_diameter / 2 + self.ball_radius,
                box_diameter / 2 - self.ball_radius,
            )

            ball_body = self.world.create_dynamic_body(
                position=(x, y),
                linear_damping=0.9,
                is_bullet=True,  # make the ball a bullet body
            )
            material = b2d.surface_material(
                restitution=0.5,
                friction=0.5,
                custom_color=b2d.rgb_to_hex_color(100, 0, 200),
            )
            ball_body.create_shape(
                b2d.shape_def(density=1, material=material, enable_contact_events=True),
                b2d.circle(radius=self.ball_radius),
            )

        # add a bunch of capsules
        n_capsules = 600
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
                custom_color=b2d.rgb_to_hex_color(0, 100, 200),
            )
            capsule_body.create_shape(
                b2d.shape_def(density=1, material=material, enable_contact_events=True),
                b2d.capsule(
                    (0, 0), (self.capsule_length, 0), radius=self.capsule_radius
                ),
            )

        # rounded rectangle
        self.rounded_rectangle_radius = 0.1
        self.rounded_rectangle_width = 0.3
        self.rounded_rectangle_height = 0.1
        for i in range(600):
            # radom position in the tumbler
            x = random.uniform(
                -box_diameter / 2 + self.rounded_rectangle_width / 2,
                box_diameter / 2 - self.rounded_rectangle_width / 2,
            )
            y = random.uniform(
                -box_diameter / 2 + self.rounded_rectangle_height / 2,
                box_diameter / 2 - self.rounded_rectangle_height / 2,
            )

            rounded_rectangle_body = self.world.create_dynamic_body(
                position=(x, y),
                linear_damping=0.9,
            )
            material = b2d.surface_material(
                restitution=0.5,
                friction=0.5,
                custom_color=b2d.rgb_to_hex_color(200, 100, 0),
            )
            rounded_rectangle_body.create_shape(
                b2d.shape_def(density=1, material=material, enable_contact_events=True),
                b2d.make_rounded_box(
                    hx=self.rounded_rectangle_width / 2,
                    hy=self.rounded_rectangle_height / 2,
                    radius=self.rounded_rectangle_radius,
                ),
            )

    def on_click(self, pos):
        print(f"Clicked at {pos}")

    def on_double_click(self, pos):
        print(f"Double clicked at {pos}")
        # create explosion at the mouse position
        self.world.explode(position=pos, radius=20, impulse_per_length=10)

    def on_triple_click(self, pos):
        print(f"Triple clicked at {pos}")
        self.world.explode(position=pos, radius=20, impulse_per_length=-10)

    def aabb(self):
        return b2d.aabb(lower_bound=(-20, -20), upper_bound=(20, 20))


class NetwonsCradle(SampleBase):
    def __init__(self):
        super().__init__(gravity=(0, -10))

        # physical world
        self.n_balls = 10
        self.radius = 0.2
        self.actual_radius = self.radius * 0.85
        self.rope_length = 2.5

        diameter = self.radius * 2
        self.ball_bodies = []
        self.world_rope_anchors = []
        for i in range(self.n_balls):
            x = diameter * i
            y_ball = 0
            y_rope = self.rope_length

            # create dynamic body for the ball
            ball_body = self.world.create_dynamic_body(
                position=(x, y_ball), linear_damping=0.1, angular_damping=0.0
            )
            ball_body.awake = True
            self.ball_bodies.append(ball_body)
            # create circle shape for the ball
            material = b2d.surface_material(
                restitution=1.0,
                friction=0.0,
                custom_color=b2d.rgb_to_hex_color(100, 0, 200),
            )
            ball_body.create_shape(
                b2d.shape_def(density=1, material=material),
                b2d.circle(radius=self.actual_radius),
            )

            # create a rope anchor for the ball
            anchor_pos = (x, y_rope)
            self.world_rope_anchors.append(anchor_pos)
            # create a static body for the rope anchor
            anchor_body_id = self.world.create_static_body(position=anchor_pos)

            self.world.create_distance_joint(
                body_a=ball_body,
                body_b=anchor_body_id,
                length=self.rope_length,
                enable_spring=False,
            )

        # apply impusle to the last ball st. it moves to the right
        last_ball = self.ball_bodies[-1]
        impulse = (0.5, 0)
        # last_ball.apply_linear_impulse_to_center(impulse, wake=True)

    def pre_debug_draw(self):
        bb = self.aabb()
        world_lower_bound = bb.lower_bound
        world_upper_bound = bb.upper_bound

        # draw green rectangle around the world bounds

        center = (
            (world_lower_bound[0] + world_upper_bound[0]) / 2,
            (world_lower_bound[1] + world_upper_bound[1]) / 2,
        )
        shape = (
            world_upper_bound[0] - world_lower_bound[0],
            world_upper_bound[1] - world_lower_bound[1],
        )
        self.debug_draw.draw_solid_rect(center=center, shape=shape, color=(0, 255, 0))
        self.debug_draw.draw_rect(
            center=center,
            shape=shape,
            line_width=self.actual_radius,
            color=(0, 255, 255),
            width_in_pixels=False,
        )

    def post_debug_draw(self):
        # a line diagonal over the aabb
        bb = self.aabb()
        world_lower_bound = bb.lower_bound
        world_upper_bound = bb.upper_bound
        p1 = (world_lower_bound[0], world_upper_bound[1])
        p2 = (world_upper_bound[0], world_lower_bound[1])
        self.debug_draw.draw_line(
            p1=p1,
            p2=p2,
            line_width=self.actual_radius,
            color=(255, 255, 0),
            width_in_pixels=False,
        )

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-(self.rope_length + 2 * self.radius), 0),
            upper_bound=(
                self.n_balls * self.radius * 2 + self.rope_length,
                self.rope_length + 2 * self.radius,
            ),
        )


if __name__ == "__main__":
    Tumbler.run()
