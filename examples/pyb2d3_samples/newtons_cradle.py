# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


class NewtonsCradle(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)

        # physical world
        self.n_balls = 10
        self.radius = 1
        self.actual_radius = self.radius * 0.85
        self.rope_length = 10

        diameter = self.radius * 2
        for i in range(self.n_balls):
            x = diameter * i
            y_ball = 0
            y_rope = self.rope_length

            # create dynamic body for the ball
            ball_body = self.world.create_dynamic_body(
                position=(x, y_ball), linear_damping=0.1, angular_damping=0.0
            )
            ball_body.awake = True
            # create circle shape for the ball
            material = b2d.surface_material(
                restitution=1.0,
                friction=0.0,
                custom_color=b2d.hex_color(100, 0, 200),
            )
            ball_body.create_shape(
                b2d.shape_def(density=1, material=material),
                b2d.circle(radius=self.actual_radius),
            )

            # create a rope anchor for the balls
            anchor_pos = (x, y_rope)
            anchor_body_id = self.world.create_static_body(position=anchor_pos)

            self.world.create_distance_joint(
                body_a=ball_body,
                body_b=anchor_body_id,
                length=self.rope_length,
                enable_spring=False,
            )

        impulse = (-10, 0)
        ball_body.apply_linear_impulse_to_center(impulse, wake=True)

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-(self.rope_length + 2 * self.radius), 0),
            upper_bound=(
                self.n_balls * self.radius * 2 + self.rope_length,
                self.rope_length + 2 * self.radius,
            ),
        )

    def on_key_down(self, event):
        if event.key == "a":
            # create dynamic body for the ball
            ball_body = self.world.create_dynamic_body(
                position=(0, 0), linear_damping=0.1, angular_damping=0.0
            )
            ball_body.awake = True
            # create circle shape for the ball
            material = b2d.surface_material(
                restitution=1.0,
                friction=0.0,
                custom_color=b2d.hex_color(100, 0, 200),
            )
            ball_body.create_shape(
                b2d.shape_def(density=1, material=material),
                b2d.circle(radius=self.actual_radius),
            )


if __name__ == "__main__":
    NewtonsCradle.run()
