# +
import pyb2d3 as b2d
import numpy as np
from enum import Enum
from pyb2d3_sandbox import SampleBase


class GolfState(Enum):
    WAITING_FOR_BALL_CLICK = 0  # we are waiting for the user to click on a ball
    SET_DRAG_FORCE = 1  # user is setting the force via mouse drag/move
    WAITING_FOR_REST = 2  # we are waiting for the ball to come to rest
    BALL_IS_IN_HOLE = 3  # the ball is in the hole, we can reset the level


class Minigolf(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))

        # create the minigolf course
        builder = b2d.PathBuilder((0, 0))
        builder.line_to(right=4)
        self.hole_position = builder.arc_to(
            up=2, radius=1.5, clockwise=False, segments=60, major_arc=True
        )
        builder.line_to(left=4)
        builder.line_to(down=2)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True, reverse=True))
        points = np.array(builder.points)
        self.bounds = (points.min(axis=0), points.max(axis=0))

        # create a ball
        self.ball_radius = 0.1
        self.ball = self.world.create_dynamic_body(
            position=(0.5, 1), linear_damping=0.5, fixed_rotation=True
        )
        self.ball.create_shape(
            b2d.shape_def(density=1, material=b2d.surface_material(restitution=1.0, friction=0.5)),
            b2d.circle(radius=self.ball_radius),
        )

        self.hole_radius = 0.2
        self.drag_pos = None
        self.hole_anchor_body = self.world.create_static_body(position=self.hole_position)
        self.game_state = GolfState.WAITING_FOR_BALL_CLICK
        self.drag_start_pos = None

    def on_mouse_down(self, event):
        if self.game_state == GolfState.WAITING_FOR_BALL_CLICK and self.ball.shapes[0].test_point(
            event.world_position
        ):
            self.game_state = GolfState.SET_DRAG_FORCE
            self.drag_start_pos = b2d.Vec2(event.world_position)

    def on_mouse_move(self, event):
        if self.game_state == GolfState.SET_DRAG_FORCE:
            raw_drag_pos = event.world_position

            # limit the length of the drag vector
            drag_vector = np.array(raw_drag_pos) - np.array(self.ball.position)
            drag_vector_length = np.linalg.norm(drag_vector)
            self.drag_vector_length = drag_vector_length
            if drag_vector_length > 1:
                self.drag_vector_length = 1
                drag_vector = drag_vector / drag_vector_length
                self.drag_pos = np.array(self.ball.position) + drag_vector
            else:
                self.drag_pos = raw_drag_pos

    def on_mouse_up(self, event):
        if self.game_state == GolfState.SET_DRAG_FORCE:
            # we are setting the force, so we apply it now
            force_vector = np.array(self.drag_pos) - np.array(self.ball.position)
            force_vector *= -15
            self.ball.apply_force_to_center(force_vector, True)
            self.game_state = GolfState.WAITING_FOR_REST
            self.drag_pos = None

    def post_update(self, dt):
        if self.game_state == GolfState.WAITING_FOR_REST:
            dist_to_hole = np.linalg.norm(
                np.array(self.ball.position) - np.array(self.hole_position)
            )
            if dist_to_hole < (self.hole_radius - self.ball_radius):
                self.game_state = GolfState.BALL_IS_IN_HOLE

                # connect ball to hole with a distance joint.
                # this gives a very nice effect of the ball rotating into the hole
                self.world.create_distance_joint(
                    body_a=self.ball,
                    body_b=self.hole_anchor_body,
                    length=self.hole_radius / 3.0,  # make sure ball is inside hole
                    enable_spring=True,
                    hertz=100,
                    damping_ratio=1.0,
                )
                return

        if (
            self.game_state == GolfState.BALL_IS_IN_HOLE
            or self.game_state == GolfState.WAITING_FOR_REST
        ):
            speed = np.linalg.norm(self.ball.linear_velocity)
            if speed < 0.01:
                if self.game_state == GolfState.BALL_IS_IN_HOLE:
                    self.frontend.set_sample(self.__class__, self.settings)
                else:
                    self.game_state = GolfState.WAITING_FOR_BALL_CLICK

    def aabb(self):
        lower_bound = (self.bounds[0][0] - 3, self.bounds[0][1] - 1)
        upper_bound = (self.bounds[1][0] + 3, self.bounds[1][1] + 1)

        return b2d.aabb(lower_bound=lower_bound, upper_bound=upper_bound)

    def pre_debug_draw(self):
        self.debug_draw.draw_solid_circle(
            transform=b2d.transform(self.hole_position),
            radius=self.hole_radius,
            color=b2d.hex_color(0, 0, 0),
        )

    def post_debug_draw(self):
        if self.game_state == GolfState.SET_DRAG_FORCE and self.drag_pos is not None:
            color_yellow = np.array([255, 255, 0])
            color_red = np.array([255, 0, 0])
            drag_vector = np.array(self.drag_pos) - np.array(self.ball.position)
            drag_vector_length = np.linalg.norm(drag_vector)
            color = color_yellow + (color_red - color_yellow) * drag_vector_length
            color = (round(color[0]), round(color[1]), round(color[2]))
            self.debug_draw.draw_segment(
                self.ball.position,
                self.drag_pos,
                color=b2d.hex_color(*color),
            )
            for pos in [self.ball.position, self.drag_pos]:
                self.debug_draw.draw_solid_circle(
                    transform=b2d.transform(pos),
                    color=b2d.hex_color(*color),
                    radius=self.ball_radius * 0.5,
                )


if __name__ == "__main__":
    Minigolf.run()
