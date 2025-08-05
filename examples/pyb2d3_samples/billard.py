# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase

import numpy as np
import math

# from dataclass  import dataclass
from dataclasses import dataclass
import random

import enum


@dataclass
class Ball:
    color: tuple[int, int, int]
    is_half: bool = False
    is_white: bool = False
    is_black: bool = False
    body: b2d.Body = None


# enum for state of game
class GameState(enum.Enum):
    WAITING_FOR_BALL_SELECTION = enum.auto()
    WAITING_FOR_SHOT = enum.auto()
    WAITING_FOR_BALLS_TO_REST = enum.auto()


class Billard(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))

        # billiard table
        w = 8
        h = w / 2
        self.width_lower_bound = w
        self.height_lower_bound = h

        # top_left_corner
        top_left_corner = (-w / 2, h / 2)

        # pocket radius
        r = 0.5
        self.pocket_radius = r

        md = r * math.sqrt(2) * 1.3
        cd = r * 1.3

        self.pocket_centers = []

        # start with left pocket arc
        start = (top_left_corner[0], top_left_corner[1])
        builder = b2d.PathBuilder(start)
        pocket_center = builder.arc_to(
            delta=(-cd, -cd), radius=r, clockwise=False, segments=20, major_arc=True
        )
        self.pocket_centers.append(pocket_center)

        # move down by height
        builder.line_to(down=h)

        # add bottom left corner pocket
        pocket_center = builder.arc_to(
            delta=(cd, -cd), radius=r, clockwise=False, segments=20, major_arc=True
        )
        self.pocket_centers.append(pocket_center)

        # move right by width /2
        builder.line_to(right=w / 2)
        # add bottom middle pocket
        pocket_center = builder.arc_to(
            delta=(md, 0), radius=r, clockwise=False, segments=20, major_arc=True
        )
        self.pocket_centers.append(pocket_center)

        # move right by width /2
        builder.line_to(right=w / 2)
        # add bottom right corner pocket
        pocket_center = builder.arc_to(
            delta=(cd, cd), radius=r, clockwise=False, segments=20, major_arc=True
        )
        self.pocket_centers.append(pocket_center)

        # move up by height
        builder.line_to(up=h)
        # add top right corner pocket
        pocket_center = builder.arc_to(
            delta=(-cd, cd), radius=r, clockwise=False, segments=20, major_arc=True
        )
        self.pocket_centers.append(pocket_center)

        # move left by width/2
        builder.line_to(left=w / 2)
        # add top middle pocket
        pocket_center = builder.arc_to(
            delta=(-md, 0), radius=r, clockwise=False, segments=20, major_arc=True
        )
        self.pocket_centers.append(pocket_center)
        # move left by width/2
        builder.line_to(left=w / 2)

        assert len(self.pocket_centers) == 6, "There should be 6 pocket centers"

        table_center = (np.array(self.pocket_centers[2]) + np.array(self.pocket_centers[5])) / 2
        table_center = (float(table_center[0]), float(table_center[1]))
        self.table_center = table_center

        # add 15 balls
        self.balls = []
        self.ball_radius = 0.2

        def create_ball(position, color):
            material = b2d.surface_material(
                custom_color=b2d.hex_color(color[0], color[1], color[2]),
                restitution=1.0,
            )
            ball = self.world.create_dynamic_body(
                position=position, linear_damping=0.8, fixed_rotation=True
            )
            ball.create_shape(b2d.shape_def(material=material), b2d.circle(radius=self.ball_radius))
            return ball

        billiard_base_colors = [
            (255, 255, 0),  # 1 - Yellow
            (0, 0, 255),  # 2 - Blue
            (255, 0, 0),  # 3 - Red
            (128, 0, 128),  # 4 - Purple
            (255, 165, 0),  # 5 - Orange
            (0, 128, 0),  # 6 - Green
            (128, 0, 0),  # 7 - Maroon (Burgundy)
        ]
        # create a list of all balls (except white and black)
        for i, color in enumerate(billiard_base_colors):
            self.balls.append(Ball(color=color, is_half=False))
            self.balls.append(Ball(color=color, is_half=True))

        # shuffle the balls
        random.shuffle(self.balls[1:])  # keep the first ball (yellow) in place

        self.balls.insert(4, Ball(color=(0, 0, 1), is_black=True))

        # add a white ball as last ball
        self.balls.append(Ball(color=(255, 255, 255), is_white=True))

        ball_index = 0
        for x in range(5):
            n_balls = x + 1
            # pos_x = x * self.ball_radius *
            pos_x = x * self.ball_radius * math.sqrt(3)
            offset_y = -x * self.ball_radius

            for y in range(n_balls):
                ball_item = self.balls[ball_index]
                pos_y = offset_y + y * self.ball_radius * 2
                ball_body = create_ball(
                    position=(table_center[0] + pos_x, table_center[1] + pos_y),
                    color=ball_item.color,
                )
                self.balls[ball_index].body = ball_body
                ball_index += 1

        # white ball
        white_ball = create_ball(
            position=(table_center[0] - w / 4, table_center[1]),
            color=self.balls[-1].color,
        )
        self.balls[-1].body = white_ball

        self.outline = np.array(builder.points)

        material = b2d.surface_material(
            restitution=1.0,
            custom_color=b2d.hex_color(10, 150, 10),
        )
        self.anchor_body.create_chain(
            builder.chain_def(is_loop=True, reverse=True, material=material)
        )

        # state of the game
        self.game_state = GameState.WAITING_FOR_BALL_SELECTION
        self.marked_point_on_white_ball = None
        self.aim_point = None

        # in case of a headless frontend we do one shot
        if self.frontend.settings.headless:
            # we create a mouse joint for the white ball
            self.balls[-1].body.apply_linear_impulse_to_center((3.5, 0.1), wake=True)
            self.game_state = GameState.WAITING_FOR_BALLS_TO_REST

    def on_mouse_down(self, event):
        if self.game_state == GameState.WAITING_FOR_BALL_SELECTION:
            # check if mouse is over **the white ball**
            ball_shape = self.balls[-1].body.shapes[0]
            world_pos = event.world_position
            if ball_shape.test_point(point=world_pos):
                self.marked_point_on_white_ball = world_pos
                self.aim_point = world_pos
                self.game_state = GameState.WAITING_FOR_SHOT

    def on_mouse_move(self, event):
        if self.game_state == GameState.WAITING_FOR_SHOT:
            self.aim_point = event.world_position

    def on_mouse_up(self, event):
        if self.game_state == GameState.WAITING_FOR_SHOT:
            # shoot the white ball
            # get the impulse vector from the marked point on the white ball to the force selection point
            ball_pos = self.balls[-1].body.position
            impulse_vec = -(np.array(self.aim_point) - np.array(ball_pos))
            impulse_vec = (
                float(impulse_vec[0]),
                float(impulse_vec[1]),
            )  # convert to tuple
            # apply the force as impulse
            self.balls[-1].body.apply_linear_impulse(impulse_vec, self.marked_point_on_white_ball)
            self.game_state = GameState.WAITING_FOR_BALLS_TO_REST
            self.marked_point_on_white_ball = None
            self.aim_point = None

    def pre_update(self, dt):
        if self.game_state == GameState.WAITING_FOR_BALLS_TO_REST:
            all_rest = True
            for ball in self.balls:
                body = ball.body
                mag = body.linear_velocity_magnitude()
                if mag > 0.0001:  # threshold for resting
                    all_rest = False
                    break
            if all_rest:
                self.game_state = GameState.WAITING_FOR_BALL_SELECTION
                self.marked_point_on_white_ball = None
                self.aim_point = None

        # check if any ball is in a pocket
        to_be_removed = []
        dr = self.pocket_radius - self.ball_radius
        for ball in self.balls:
            body = ball.body
            for pocket_center in self.pocket_centers:
                if np.linalg.norm(np.array(body.position) - np.array(pocket_center)) < dr:
                    to_be_removed.append(ball)
                    break

        for ball in to_be_removed:
            if ball.is_white or ball.is_black:
                self.frontend.set_sample(type(self), self.settings)
            if self.mouse_joint_body is not None:
                if ball.body == self.mouse_joint_body:
                    self.destroy_mouse_joint()
            self.balls.remove(ball)
            ball.body.destroy()

    def pre_debug_draw(self):
        for pocket_center in self.pocket_centers:
            t = b2d.transform(pocket_center)
            self.debug_draw.draw_solid_circle(
                transform=t,
                radius=0.5,
                color=(0, 0, 0),
            )

        # self.debug_draw.draw_polygon(points=self.outline, color=(10, 150, 10))

    def post_debug_draw(self):
        for ball in self.balls:
            self.debug_draw.draw_solid_circle(
                transform=ball.body.transform,
                radius=self.ball_radius,
                color=ball.color,
            )
            if ball.is_half:
                self.debug_draw.draw_solid_circle(
                    transform=ball.body.transform,
                    radius=self.ball_radius / 2,
                    color=(255, 255, 255),
                )
        if self.marked_point_on_white_ball is not None:
            self.debug_draw.draw_solid_circle(
                transform=b2d.transform(self.marked_point_on_white_ball),
                radius=0.1,
                color=(255, 0, 0),
            )

            if self.aim_point is not None:
                self.debug_draw.draw_segment(
                    self.marked_point_on_white_ball, self.aim_point, color=(255, 0, 0)
                )

    def aabb(self):
        hx = self.width_lower_bound / 2
        hy = self.height_lower_bound / 2
        margin = hx * 1.5
        center = self.table_center
        return b2d.aabb(
            lower_bound=(center[0] - (hx + margin), center[1] - (hy + margin)),
            upper_bound=(center[0] + (hx + margin), center[1] + (hy + margin)),
        )


if __name__ == "__main__":
    Billard.run()
