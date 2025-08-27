# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


import random
import numpy as np


def grid_iterate(shape):
    rows, cols = shape
    for row in range(rows):
        for col in range(cols):
            yield row, col


class Jump(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -50)))
        self.outer_box_radius = 100

        # attach the chain shape to a static body
        self.box_body = self.world.create_static_body(position=(0, 0))

        def parabula(p0, p1, n_points=100):
            p0 = np.array(p0)
            p1 = np.array(p1)
            tangent = np.array([1, -1])
            tangent = tangent / np.linalg.norm(tangent)  # normalize

            # Find the length of the segment
            chord = p1 - p0
            chord_length = np.linalg.norm(chord)

            # Heuristic: control point is at distance proportional to chord length
            # Adjust this factor to make the curve more or less "bendy"
            factor = 0.5 * chord_length
            c = p0 + tangent * factor

            t = np.linspace(0, 1, n_points)[:, None]
            curve = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t**2 * p1

            return curve

        chain_points = np.array(
            [
                (0, -35),
                (-100, 0),
                (-100, 100),
                (0, 100),
                (100, 100),
                (200, 100),
                (200, -100),
                (100, -100),
            ]
        )

        p0 = (50, -50)
        p1 = (60, -45)
        curve = parabula(p0, p1, n_points=100)
        curve = np.flip(curve, axis=0)  # flip to match the direction
        chain_points = np.concatenate((chain_points, curve), axis=0)

        self.box_body.create_chain(b2d.chain_def(points=chain_points, is_loop=True))

        # a helper to get a random point in the flat zone
        def random_point_in_box():
            return (random.uniform(-100, 0), random.uniform(1, 10))

        # last time we created a ball
        self.last_ball_time = None
        self.balls_added = 0

    def pre_update(self, dt):
        if self.balls_added > 3000:
            return
        # create a ball every 0.5 seconds
        t = self.world_time
        if self.last_ball_time is None:
            self.last_ball_time = t

        delta = t - self.last_ball_time

        # print(f"balls_added: {self.balls_added}")
        if delta > 0.05:
            self.last_ball_time = t

            ball_body = self.world.create_dynamic_body(
                position=(-95, 5),
                angular_damping=0.01,
                linear_damping=0.01,
                fixed_rotation=False,
            )
            ball_body.create_shape(
                b2d.shape_def(
                    density=1,
                    material=b2d.surface_material(
                        restitution=0, friction=0.0, custom_color=b2d.random_hex_color()
                    ),
                ),
                b2d.circle(radius=2),
            )

            # apply impulse to the ball
            impulse = (500, -500)
            ball_body.apply_linear_impulse_to_center(impulse)
            self.balls_added += 1

    def on_key_down(self, event):
        if event.key == "g":
            self.world.gravity = (0, 0)

    def on_key_up(self, event):
        if event.key == "g":
            self.world.gravity = (0, -50)

    # create explosion on double click
    def on_double_click(self, event):
        self.world.explode(position=event.world_position, radius=70, impulse_per_length=200)

    def aabb(self):
        eps = 0.01
        r = self.outer_box_radius + eps
        return b2d.aabb(
            lower_bound=(-r, -r),
            upper_bound=(r, r),
        )


if __name__ == "__main__":
    Jump.run()
