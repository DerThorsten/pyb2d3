# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


def grid_iterate(shape):
    rows, cols = shape
    for row in range(rows):
        for col in range(cols):
            yield row, col


class Joints(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)

        half_width = 10
        self.half_width = half_width
        self.anchor_body.create_shape(
            b2d.shape_def(), b2d.segment((-half_width, 0), (half_width, 0))
        )

        h = 4

        # revolute joint
        # create a static anchor body for each joint
        x = -6
        a = self.world.create_static_body(position=(x, h))

        # create a dynamic body
        b = self.world.create_dynamic_body(position=(x, h - 2))
        b.create_shape(b2d.shape_def(), b2d.box(hx=0.5, hy=1.0))

        # create a revolute joint
        self.world.create_revolute_joint(body_a=a, body_b=b, local_anchor_b=(0, 1))

        # to start with some movement
        b.apply_linear_impulse_to_center((10, 0))

        x = -2
        # prismatic joint
        a = self.world.create_static_body(position=(x, h))
        b = self.world.create_dynamic_body(position=(x, h - 2))
        b.create_shape(b2d.shape_def(), b2d.box(hx=0.5, hy=0.5))
        self.world.create_prismatic_joint(
            body_a=a,
            body_b=b,
            local_anchor_b=(0, 0),
            local_axis_a=(1, 1),
        )
        # to start with some movement
        b.apply_linear_impulse_to_center((0, 10))

        x = 0
        # weld joint
        a = self.world.create_static_body(position=(x, h))
        b = self.world.create_dynamic_body(position=(x, h))
        b.create_shape(b2d.shape_def(), b2d.box(hx=2.0, hy=0.5))
        self.world.create_weld_joint(
            body_a=a,
            body_b=b,
            local_anchor_b=(-2, 0),
            linear_hertz=20,
            angular_hertz=5,
        )

        # to start with some movement
        b.apply_linear_impulse_to_center((10, 0))

        x = 5
        # distance joint
        a = self.world.create_static_body(position=(x, h))
        b = self.world.create_dynamic_body(position=(x, h - 2))
        b.create_shape(b2d.shape_def(), b2d.box(hx=0.5, hy=1.0))
        self.world.create_distance_joint(
            body_a=a,
            body_b=b,
            local_anchor_b=(0, 1),
            length=1.0,
            enable_spring=True,
            hertz=5,
            damping_ratio=0.0,
        )

        # to start with some movement
        b.apply_linear_impulse_to_center((10, 0))

    def aabb(self):
        eps = 0.01
        r = self.half_width + eps
        return b2d.aabb(
            lower_bound=(-r, -r),
            upper_bound=(r, r),
        )


if __name__ == "__main__":
    Joints.run()
