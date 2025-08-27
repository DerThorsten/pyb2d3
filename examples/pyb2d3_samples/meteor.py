# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


class Meteor(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))

        self.floor_size = 1000

        self.anchor_body.create_shape(
            b2d.shape_def(material=b2d.surface_material(restitution=0.5)),
            b2d.segment(
                (-self.floor_size, 0),
                (self.floor_size, 0),
            ),
        )

        # build a towers  meteor can hit
        num_blocks_base = 40
        box_shape = [0.5, 3.0]
        distance_x = box_shape[1]
        start_x = 0
        y_start = 0

        for outer in range(num_blocks_base):
            y_start_inner = y_start + outer * (box_shape[1] + box_shape[0])
            for i in range(num_blocks_base - outer):
                x = start_x + (i + outer / 2) * distance_x
                y = y_start_inner + box_shape[1] / 2
                body = self.world.create_dynamic_body(position=(x, y))
                body.create_shape(
                    b2d.shape_def(density=1, material=b2d.surface_material(restitution=0.5)),
                    b2d.box(hx=box_shape[0] / 2, hy=box_shape[1] / 2),
                )

                if i + 1 < num_blocks_base - outer:
                    # create a second block on top
                    body = self.world.create_dynamic_body(
                        position=(
                            x + box_shape[1] / 2,
                            y_start_inner + box_shape[1] + box_shape[0] / 2,
                        )
                    )
                    body.create_shape(
                        b2d.shape_def(density=1, material=b2d.surface_material(restitution=0.5)),
                        b2d.box(hx=box_shape[1] / 2, hy=box_shape[0] / 2),
                    )

        if self.frontend.settings.headless:
            meteor_body = self.world.create_dynamic_body(
                position=(-35, 300),
                linear_velocity=(10, 0),
                user_data=3,
                gravity_scale=4.0,  # to make it fall faster
            )
            meteor_body.create_shape(
                b2d.shape_def(
                    density=10,
                    material=b2d.surface_material(restitution=0.5),
                    enable_contact_events=True,
                ),
                b2d.circle(radius=5),
            )

    def on_key_down(self, event):
        if event.key == "m":
            # create a meteor
            meteor_body = self.world.create_dynamic_body(
                position=(0, 0),
                user_data=3,
                gravity_scale=4.0,  # to make it fall faster
            )
            meteor_body.create_shape(
                b2d.shape_def(
                    density=10,
                    material=b2d.surface_material(restitution=0.5),
                    enable_contact_events=True,
                ),
                b2d.circle(radius=5),
            )

    def on_double_click(self, event):
        # create a meteor
        meteor_body = self.world.create_dynamic_body(
            position=event.world_position,
            user_data=3,
            gravity_scale=4.0,  # to make it fall faster
        )
        meteor_body.create_shape(
            b2d.shape_def(
                density=10,
                material=b2d.surface_material(restitution=0.5),
                enable_contact_events=True,
            ),
            b2d.circle(radius=5),
        )

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-50, -10),
            upper_bound=(200, 300),
        )


if __name__ == "__main__":
    Meteor.run()
