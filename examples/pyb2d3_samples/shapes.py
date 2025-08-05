# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase

import random
import numpy as np
import math


# helper function to create shapes like
# a circle, triangle, pentagon, hexagon, etc.
def approx_circle(radius, n_segments):
    angle = 2 * math.pi / n_segments
    return np.array(
        [(radius * math.cos(i * angle), radius * math.sin(i * angle)) for i in range(n_segments)]
    )


class Shapes(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.outer_box_radius = 10

        # attach the chain shape to a static body
        self.box_body = self.world.create_static_body(position=(0, 0))
        self.box_body.create_chain(
            b2d.chain_box(center=(0, 0), hx=self.outer_box_radius, hy=self.outer_box_radius)
        )

        # a helper to get a random point in the box (with some margin)
        # st. we can place shapes at random positions in the box
        def random_point_in_box():
            margin = 2
            r = self.outer_box_radius - margin
            return (random.uniform(-r, r), random.uniform(-r, r))

        # lambda to create shape def with random rgb color
        def random_color_shape_def():
            return b2d.shape_def(
                density=1,
                material=b2d.surface_material(
                    restitution=0.5,
                    custom_color=b2d.random_hex_color(),
                ),
            )

        # create a lot of different shapes n-times
        n = 4
        for i in range(n):
            # a ball
            self.ball_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            self.ball_body.create_shape(
                random_color_shape_def(),
                b2d.circle(radius=1),
            )

            # a capsule
            capsule_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            capsule_body.create_shape(
                random_color_shape_def(),
                b2d.capsule(radius=0.5, center1=(-0.5, 0), center2=(0.5, 0)),
            )

            # a rectangle
            rectangle_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            rectangle_body.create_shape(
                random_color_shape_def(),
                b2d.box(hx=0.5, hy=1.0),
            )

            # a rounded rectangle
            rounded_rectangle_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            rounded_rectangle_body.create_shape(
                random_color_shape_def(),
                b2d.box(hx=0.5, hy=1.0, radius=0.5),
            )

            # an arbitary convex polygon with optional radius
            # triangle
            triangle_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            points = [
                (-0.5, -0.5),
                (0.5, -0.5),
                (0, 0.5),
            ]
            triangle_body.create_shape(
                random_color_shape_def(),
                b2d.polygon(points=points, radius=0.1),
            )

            # pentagon
            pentagon_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            points = approx_circle(radius=0.5, n_segments=5)
            pentagon_body.create_shape(
                random_color_shape_def(), b2d.polygon(points=points, radius=0.1)
            )

            # hexagon
            hexagon_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            points = approx_circle(radius=0.5, n_segments=6)
            hexagon_body.create_shape(
                random_color_shape_def(), b2d.polygon(points=points, radius=0.1)
            )

            # 8 sided polygon
            eight_sided = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            points = approx_circle(radius=2.5, n_segments=8)
            points[:, 1] *= 0.5  # make it a bit more flat
            eight_sided.create_shape(
                random_color_shape_def(),
                b2d.polygon(points=points, radius=0.1),
            )

            # compound shapes (ie combining multiple shapes into one body)
            shape_def = random_color_shape_def()
            plus_shape_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            plus_shape_body.create_shape(
                shape_def,
                b2d.box(hx=0.5, hy=1.0),
            )
            plus_shape_body.create_shape(
                shape_def,
                b2d.box(hx=1.0, hy=0.5),
            )

            shape_def = random_color_shape_def()
            lollipop_shape_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            lollipop_shape_body.create_shape(
                shape_def,
                b2d.circle(radius=0.5, center=(0, 0.5)),
            )
            lollipop_shape_body.create_shape(
                shape_def,
                b2d.box(hx=0.1, hy=1.0, center=(0, -0.5), rotation=0),
            )

            shape_def = random_color_shape_def()
            dumbell_shape_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            dumbell_shape_body.create_shape(
                shape_def,
                b2d.box(hx=0.1, hy=1.1, center=(0, 0), rotation=0),
            )
            dumbell_shape_body.create_shape(
                shape_def,
                b2d.circle(radius=0.5, center=(0, 1.5)),
            )
            dumbell_shape_body.create_shape(
                shape_def,
                b2d.circle(radius=0.5, center=(0, -1.5)),
            )

        # a lot of tiny balls
        for _ in range(400):
            self.ball_body = self.world.create_dynamic_body(
                position=random_point_in_box(), linear_damping=0.2, angular_damping=0.2
            )
            self.ball_body.create_shape(
                random_color_shape_def(),
                b2d.circle(radius=0.2),
            )

    # create explosion on double click
    def on_double_click(self, event):
        self.world.explode(position=event.world_position, radius=7, impulse_per_length=20)

    # create "negative" explosion on triple click
    # this will pull bodies towards the click position
    def on_triple_click(self, event):
        self.world.explode(position=event.world_position, radius=7, impulse_per_length=-20)

    def aabb(self):
        eps = 0.01
        r = self.outer_box_radius + eps
        return b2d.aabb(
            lower_bound=(-r, -r),
            upper_bound=(r, r),
        )


if __name__ == "__main__":
    Shapes.run()
