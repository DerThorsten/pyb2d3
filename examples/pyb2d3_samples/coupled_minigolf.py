# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


import numpy as np
import time
from enum import Enum

from dataclasses import dataclass

# some constants to not overcomplicate the example
BALL_RADIUS = 0.1
HOLE_RADIUS = 0.2
MAX_FORCE_VECTOR_LENGTH = 2
BALL_COLORS = [b2d.hex_color(100, 100, 220), b2d.hex_color(100, 100, 220)]


@dataclass
class CourseLevelData:
    # where are the 2 balls placed?
    start_positions: list[tuple]

    # where is the hole?
    hole_position: tuple

    # the polygons of the course
    course_polygons: list[list[tuple]]


eps = 0.25
Levels = [
    CourseLevelData(
        start_positions=[(1, 1), (1, 1.8)],
        hole_position=(5, 1),
        course_polygons=[[(0, 0), (0, 2), (6, 2), (6, 0)]],
    ),
    CourseLevelData(
        start_positions=[(1, 1), (1, 1.8)],
        hole_position=(5, -1),
        course_polygons=[
            [
                (0, 0),
                (0, 2),
                (6, 2),
                (6, -2),
                (4, -2),
                (4, 0),
            ]
        ],
    ),
    CourseLevelData(
        start_positions=[(1, 1.75), (1, 2.8)],
        hole_position=(1, 5),
        course_polygons=[
            [(0, 0), (0, 2), (2.5, 2), (2.5, 4), (0, 4), (0, 6), (4, 6), (4, 0)],
            [
                (0 + eps, 2 + eps),
                (0 + eps, 4 - eps),
                (2 - eps, 4 - eps),
                (2 - eps, 2 + eps),
            ],
        ],
    ),
]


class GolfState(Enum):
    WAITING_FOR_BALL_CLICK = 0  # we are waiting for the user to click on a ball
    SET_DRAG_FORCE = 1  # user is setting the force via mouse drag/move
    WAITING_FOR_REST = 2  # we are waiting for the ball to come to rest
    BALL_IS_IN_HOLE = 3  # the ball is in the hole, we can proceed to the next level


class CoupledMinigolf(SampleBase):
    @dataclass
    class Settings(SampleBase.Settings):
        current_level: int = 0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.outer_box_radius = 100

        # data for the current level
        self.level = Levels[settings.current_level]

        # create the chain shape for the course
        chain_material = b2d.surface_material(restitution=0.75)
        for polygon in self.level.course_polygons:
            self.anchor_body.create_chain(
                b2d.chain_def(polygon, is_loop=True, material=chain_material)
            )

        # create the balls
        self.balls = []

        for i, position in enumerate(self.level.start_positions):
            body = self.world.create_dynamic_body(
                position=position,
                linear_damping=0.75,
                fixed_rotation=True,
            )
            material = b2d.surface_material(restitution=0.75, custom_color=BALL_COLORS[i])
            ball_shape_def = b2d.shape_def(density=1, material=material)
            body.create_shape(ball_shape_def, b2d.circle(radius=BALL_RADIUS))
            self.balls.append(body)
        self.balls_shape = [ball.shapes[0] for ball in self.balls]

        # create a distance joint between the two balls
        self.world.create_distance_joint(
            body_a=self.balls[0],
            body_b=self.balls[1],
            length=np.linalg.norm(
                np.array(self.balls[0].position) - np.array(self.balls[1].position)
            ),
            collide_connected=True,
            hertz=0.35,
            enable_spring=True,
            damping_ratio=0.25,
        )

        # state of the game
        self.state = GolfState.WAITING_FOR_BALL_CLICK
        self.dragged_ball_index = None
        self.drag_pos = None
        self.force_vector_length = 0
        self.ball_in_hole_time = None

        if self.frontend.settings.headless:
            self.balls[0].apply_linear_impulse_to_center((0.2, 0.01), wake=True)
            self.state = GolfState.WAITING_FOR_REST

    def on_mouse_down(self, event):
        if self.state == GolfState.WAITING_FOR_BALL_CLICK:
            # check if the user clicked on one of the balls
            for i, ball in enumerate(self.balls):
                if self.balls_shape[i].test_point(event.world_position):
                    self.state = GolfState.SET_DRAG_FORCE
                    self.dragged_ball_index = i
                    self.drag_pos = event.world_position
                    return

    def on_mouse_up(self, event):
        if self.state == GolfState.SET_DRAG_FORCE:
            # we are setting the force, so we apply it now
            dragged_ball = self.balls[self.dragged_ball_index]
            force_vector = np.array(self.drag_pos) - np.array(dragged_ball.position)
            force_vector *= -15
            dragged_ball.apply_force_to_center(force_vector, True)
            self.state = GolfState.WAITING_FOR_REST

    def on_mouse_move(self, event):
        if self.state == GolfState.SET_DRAG_FORCE:
            raw_drag_pos = event.world_position

            # limit the length of the force vector
            force_vector = np.array(raw_drag_pos) - np.array(
                self.balls[self.dragged_ball_index].position
            )
            force_vector_length = np.linalg.norm(force_vector)
            self.force_vector_length = force_vector_length
            if force_vector_length > MAX_FORCE_VECTOR_LENGTH:
                self.force_vector_length = MAX_FORCE_VECTOR_LENGTH
                force_vector = force_vector / force_vector_length * MAX_FORCE_VECTOR_LENGTH
                self.drag_pos = (
                    np.array(self.balls[self.dragged_ball_index].position) + force_vector
                )
            else:
                self.drag_pos = raw_drag_pos

    def balls_rest(self):
        mag = self.balls[0].linear_velocity_magnitude() + self.balls[1].linear_velocity_magnitude()
        return mag < 0.0001

    def post_update(self, dt):
        # if the ball is already in the hole, check if all balls are at rest and
        #
        if self.state == GolfState.BALL_IS_IN_HOLE:
            if self.balls_rest():
                # proceed to the next level (jump to first level if we are at the last one)
                self.settings.current_level += 1
                if self.settings.current_level >= len(Levels):
                    self.settings.current_level = 0

                self.frontend.set_sample(CoupledMinigolf, self.settings)

            return

        # check if the center of the hole is inside the balls
        for i, ball in enumerate(self.balls):
            if self.balls_shape[i].test_point(self.level.hole_position):
                self.state = GolfState.BALL_IS_IN_HOLE
                self.ball_in_hole_time = time.time()

                hole_body = self.world.create_static_body(position=self.level.hole_position)

                # create a distance joint to capture the ball in the hole
                self.world.create_distance_joint(
                    body_a=ball,
                    body_b=hole_body,
                    length=0.01,  # very small length to keep the ball in place
                    enable_spring=True,
                    hertz=100,
                    damping_ratio=1.0,
                )
                return

        if self.state == GolfState.WAITING_FOR_REST:
            # check if balls are at rest
            if self.balls_rest():
                self.state = GolfState.WAITING_FOR_BALL_CLICK

    # to ensure the hole is **under** the balls
    # we use the pre_debug_draw method
    def pre_debug_draw(self):
        self.debug_draw.draw_solid_circle(
            transform=b2d.transform(self.level.hole_position),
            radius=HOLE_RADIUS,
            color=b2d.hex_color(0, 0, 0),
        )

    # draw above the debgug draw
    def post_debug_draw(self):
        if self.state == GolfState.SET_DRAG_FORCE:
            # liner interolate force vector color from yellow to red
            color_yellow = np.array([255, 255, 0])
            color_red = np.array([255, 0, 0])
            color = color_yellow + (color_red - color_yellow) * (
                self.force_vector_length / MAX_FORCE_VECTOR_LENGTH
            )
            # round colors to integers
            color = (round(color[0]), round(color[1]), round(color[2]))

            # draw a line from the ball to the mouse position
            dragged_ball = self.balls[self.dragged_ball_index]
            self.debug_draw.draw_segment(
                dragged_ball.position,
                self.drag_pos,
                color=b2d.hex_color(*color),
            )
            for pos in [dragged_ball.position, self.drag_pos]:
                self.debug_draw.draw_solid_circle(
                    transform=b2d.transform(pos),
                    color=b2d.hex_color(*color),
                    radius=BALL_RADIUS * 0.5,
                )

    def aabb(self):
        # bouding box from self.levels.course_polygons
        min_x = min(p[0] for polygon in self.level.course_polygons for p in polygon)
        min_y = min(p[1] for polygon in self.level.course_polygons for p in polygon)
        max_x = max(p[0] for polygon in self.level.course_polygons for p in polygon)
        max_y = max(p[1] for polygon in self.level.course_polygons for p in polygon)
        margin = 1
        return b2d.aabb(
            lower_bound=(min_x - margin, min_y - margin),
            upper_bound=(max_x + margin, max_y + margin),
        )


if __name__ == "__main__":
    CoupledMinigolf.run()
