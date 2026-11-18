"""Minigolf with two balls tied together by a soft spring, on three levels seen from above."""

from dataclasses import dataclass
from enum import Enum

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

BALL_RADIUS = 0.1
BALL_COLOR = b2d.hex_color(100, 100, 220)
HOLE_RADIUS = 0.2
MAX_DRAG = 2.0  # the longest drag (the strongest shot)
SHOT_STRENGTH = 15.0
WALL = 0.25  # distance of the inner island from the outer walls in level 3


@dataclass
class Level:
    start_positions: list  # of the two balls
    hole_position: tuple
    walls: list  # closed polygons


LEVELS = [
    Level(
        start_positions=[(1, 1), (1, 1.8)],
        hole_position=(5, 1),
        walls=[[(0, 0), (0, 2), (6, 2), (6, 0)]],
    ),
    Level(
        start_positions=[(1, 1), (1, 1.8)],
        hole_position=(5, -1),
        walls=[[(0, 0), (0, 2), (6, 2), (6, -2), (4, -2), (4, 0)]],
    ),
    Level(
        start_positions=[(1, 1.75), (1, 2.8)],
        hole_position=(1, 5),
        walls=[
            [(0, 0), (0, 2), (2.5, 2), (2.5, 4), (0, 4), (0, 6), (4, 6), (4, 0)],
            [(WALL, 2 + WALL), (WALL, 4 - WALL), (2 - WALL, 4 - WALL), (2 - WALL, 2 + WALL)],
        ],
    ),
]


class State(Enum):
    AIMING = 0  # waiting for a click on a ball
    DRAGGING = 1  # the mouse drag sets the strength of the shot
    ROLLING = 2  # waiting for the balls to come to rest
    IN_HOLE = 3  # the next level starts once the balls rest


@register_sample("Games", "Coupled Minigolf")
class CoupledMinigolf(SampleBase):
    """Minigolf with two balls tied by a spring (a soft distance joint), three levels.
    Mouse: press on a ball, drag back and release.
    Hint: the other ball follows with a delay: swing it around corners.
    """

    @dataclass
    class Settings(SampleBase.Settings):
        current_level: int = 0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.level = LEVELS[settings.current_level]
        self.create_walls()
        self.balls = self.create_balls()
        self.state = State.AIMING
        self.dragged_ball = None
        self.drag_position = None

        if self.frontend.settings.headless:
            # take a shot, there is no mouse
            self.balls[0].apply_linear_impulse_to_center((0.2, 0.01), wake=True)
            self.state = State.ROLLING

    def create_walls(self):
        material = b2d.surface_material(restitution=0.75)
        for polygon in self.level.walls:
            self.anchor_body.create_chain(b2d.chain_def(polygon, is_loop=True, material=material))

    def create_balls(self):
        material = b2d.surface_material(restitution=0.75, custom_color=BALL_COLOR)
        balls = []
        for position in self.level.start_positions:
            ball = self.world.create_dynamic_body(
                position=position, linear_damping=0.75, fixed_rotation=True
            )
            ball.create_shape(
                b2d.shape_def(density=1, material=material), b2d.circle(radius=BALL_RADIUS)
            )
            balls.append(ball)

        # the spring: a soft distance joint with the start distance as rest length
        a, b = balls
        self.world.create_distance_joint(
            body_a=a,
            body_b=b,
            length=(a.position - b.position).length(),
            collide_connected=True,
            enable_spring=True,
            hertz=0.35,
            damping_ratio=0.25,
        )
        return balls

    def aabb(self):
        xs = [p[0] for polygon in self.level.walls for p in polygon]
        ys = [p[1] for polygon in self.level.walls for p in polygon]
        return b2d.aabb(
            lower_bound=(min(xs) - 1, min(ys) - 1), upper_bound=(max(xs) + 1, max(ys) + 1)
        )

    def on_mouse_down(self, event):
        if self.state != State.AIMING:
            return
        for ball in self.balls:
            if ball.shapes[0].test_point(event.world_position):
                self.state = State.DRAGGING
                self.dragged_ball = ball
                self.drag_position = b2d.Vec2(event.world_position)

    def on_mouse_move(self, event):
        if self.state == State.DRAGGING:
            drag = (b2d.Vec2(event.world_position) - self.dragged_ball.position).clamped(MAX_DRAG)
            self.drag_position = self.dragged_ball.position + drag

    def on_mouse_up(self, event):
        if self.state == State.DRAGGING:
            # the ball moves opposite to the drag
            ball = self.dragged_ball
            ball.apply_force_to_center((self.drag_position - ball.position) * -SHOT_STRENGTH, True)
            self.state = State.ROLLING

    def balls_rest(self):
        return self.balls[0].speed + self.balls[1].speed < 0.0001

    def post_update(self, dt):
        if self.state == State.IN_HOLE:
            if self.balls_rest():
                # the next level (after the last one: the first one again)
                self.settings.current_level = (self.settings.current_level + 1) % len(LEVELS)
                self.frontend.set_sample(CoupledMinigolf, self.settings)
            return

        for ball in self.balls:
            if ball.shapes[0].test_point(self.level.hole_position):
                self.state = State.IN_HOLE
                # a stiff spring holds the ball in the hole
                self.world.create_distance_joint(
                    body_a=ball,
                    body_b=self.world.create_static_body(position=self.level.hole_position),
                    length=0.01,
                    enable_spring=True,
                    hertz=100,
                    damping_ratio=1.0,
                )
                return

        if self.state == State.ROLLING and self.balls_rest():
            self.state = State.AIMING

    def pre_debug_draw(self):
        # drawn before the bodies: the hole is under the balls
        self.debug_draw.draw_solid_circle(
            transform=b2d.transform(self.level.hole_position),
            radius=HOLE_RADIUS,
            color=b2d.hex_color(0, 0, 0),
        )

    def post_debug_draw(self):
        if self.state != State.DRAGGING:
            return
        # from yellow (weak) to red (strong)
        ball = self.dragged_ball
        strength = (self.drag_position - ball.position).length() / MAX_DRAG
        color = b2d.hex_color(255, round(255 * (1 - strength)), 0)
        self.debug_draw.draw_segment(ball.position, self.drag_position, color=color)
        for position in (ball.position, self.drag_position):
            self.debug_draw.draw_solid_circle(
                transform=b2d.transform(position), radius=0.5 * BALL_RADIUS, color=color
            )
