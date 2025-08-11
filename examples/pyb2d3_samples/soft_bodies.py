# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets
import math


def grid_iterate(shape):
    rows, cols = shape
    for row in range(rows):
        for col in range(cols):
            yield row, col


class SoftBodies(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)

        self.outer_box_radius = 10

        # attach the chain shape to a static body
        self.box_body = self.world.create_static_body(position=(0, 0))
        self.box_body.create_chain(
            b2d.chain_box(center=(0, 0), hx=self.outer_box_radius, hy=self.outer_box_radius)
        )

        grid_shape = (4, 4)
        bodies = []
        for x, y in grid_iterate(grid_shape):
            body = self.world.create_dynamic_body(
                position=(x * 2, y * 2),
                linear_damping=0.1,
                angular_damping=0.1,
                fixed_rotation=True,
            )
            body.create_shape(
                b2d.shape_def(
                    density=1,
                    material=b2d.surface_material(
                        restitution=0.5, custom_color=b2d.random_hex_color()
                    ),
                ),
                b2d.circle(radius=0.5),
            )
            bodies.append(body)

        self.distance_joins = []

        def connect(body_a, body_b):
            d = math.sqrt(
                (body_b.position[0] - body_a.position[0]) ** 2
                + (body_b.position[1] - body_a.position[1]) ** 2
            )
            joint = self.world.create_distance_joint(
                body_a=body_a,
                body_b=body_b,
                length=d,
                enable_spring=True,
                hertz=5,
                damping_ratio=0.0,
            )
            self.distance_joins.append(joint)

        # lambda to get flat index from coordinates
        def flat_index(x, y):
            return x * grid_shape[1] + y

        for x, y in grid_iterate(grid_shape):
            if x + 1 < grid_shape[0]:
                connect(bodies[flat_index(x, y)], bodies[flat_index(x + 1, y)])
            if y + 1 < grid_shape[1]:
                connect(bodies[flat_index(x, y)], bodies[flat_index(x, y + 1)])
            if x + 1 < grid_shape[0] and y + 1 < grid_shape[1]:
                connect(bodies[flat_index(x, y)], bodies[flat_index(x + 1, y + 1)])
            if x > 0 and y + 1 < grid_shape[1]:
                connect(bodies[flat_index(x, y)], bodies[flat_index(x - 1, y + 1)])

        # create ui-elements / widgets to controll the stiffness of the distance joints
        def update_hz(value):
            for joint in self.distance_joins:
                joint.spring_hertz = value
                for body in (joint.body_a, joint.body_b):
                    body.awake = True

        def update_damping(value):
            for joint in self.distance_joins:
                joint.spring_damping_ratio = value
                for body in (joint.body_a, joint.body_b):
                    body.awake = True

        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Hertz",
                min_value=0.1,
                max_value=10.0,
                step=0.1,
                value=5.0,
                callback=update_hz,
            )
        )
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Damping",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                value=0.0,
                callback=update_damping,
            )
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
    SoftBodies.run()
