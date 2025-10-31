# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase
from examples_common import stacked_blocks


class AngryShapes(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))

        self.floor_size = 27.5

        self.anchor_body.create_shape(
            b2d.shape_def(material=b2d.surface_material(restitution=0.5)),
            b2d.segment(
                (-1, 0),
                (28, 0),
            ),
        )

        stacked_blocks(self.world, num_blocks_base=10, box_shape=[0.5, 3.0], start=(0, 0))

        self.projectile_radius = 1.0
        self.projectile_anchor_pos = b2d.Vec2(-30, 2)
        self.projectile_pos = b2d.Vec2(self.projectile_anchor_pos)
        self.projectile_body = None
        self.projectile_state = "wait_for_movement"

    def on_mouse_down(self, event):
        print("state:", self.projectile_state)
        if self.projectile_state == "wait_for_movement":
            # inside projectile ?
            d = b2d.distance(event.world_position, self.projectile_pos)
            if d <= self.projectile_radius:
                self.projectile_state = "dragging"

    def on_mouse_move(self, event):
        if self.projectile_state == "dragging":
            # move projectile position to mouse position
            self.projectile_pos = b2d.Vec2(event.world_position)

    def on_mouse_up(self, event):
        if self.projectile_state == "dragging":
            # launch projectile by a force proportional to the distance from anchor
            dir_vec = self.projectile_anchor_pos - event.world_position
            force = dir_vec * 50

            # create projectile body
            self.projectile_body = self.world.create_dynamic_body(position=self.projectile_pos)

            shape = self.projectile_body.create_shape(
                b2d.shape_def(density=1, material=b2d.surface_material(restitution=0.5)),
                b2d.circle(radius=self.projectile_radius),
            )
            shape.contact_events_enabled = True
            shape.user_data = 1

            self.projectile_body.apply_linear_impulse_to_center(force)
            self.projectile_state = "launched"

    def post_debug_draw(self):
        if self.projectile_state == "dragging":
            # draw a line from anchor to projectile position
            self.debug_draw.draw_segment(
                p1=self.projectile_anchor_pos,
                p2=self.projectile_pos,
                color=b2d.hex_color(200, 50, 50),
            )
        # draw the projectile (either as a circle at the position or the body if launched)
        if self.projectile_body is None:
            # draw circle at position
            self.debug_draw.draw_solid_circle(
                transform=b2d.transform(p=self.projectile_pos),
                radius=self.projectile_radius,
                color=b2d.hex_color(200, 50, 50),
            )

    def pre_update(self, dt):
        events = self.world.get_contact_events()
        for begin_event in events.begin_events():
            last_projectile_pos = self.projectile_body.position
            self.projectile_body.destroy()
            self.projectile_body = None
            self.projectile_pos = b2d.Vec2(self.projectile_anchor_pos)
            self.projectile_state = "wait_for_movement"
            # create an explosion
            self.world.explode(position=last_projectile_pos, radius=5, impulse_per_length=5)
            break

        if self.projectile_body is not None:
            # check if projectile is out of bounds
            if (
                self.projectile_body.position.y < -50
                or self.projectile_body.position.x > self.floor_size + 100
            ):
                self.projectile_body.destroy()
                self.projectile_body = None
                self.projectile_pos = b2d.Vec2(self.projectile_anchor_pos)
                self.projectile_state = "wait_for_movement"

    def post_update(self, dt):
        pass

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-50, -10),
            upper_bound=(35, 60),
        )


if __name__ == "__main__":
    AngryShapes.run()
