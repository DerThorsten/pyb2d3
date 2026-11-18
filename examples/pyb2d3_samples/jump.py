"""Jump: a stream of big balls races down a slope, over a ski jump and into a pit."""

import math

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

GRAVITY = (0, -50)
MAX_BALLS = 3000
SPAWN_INTERVAL = 0.05  # seconds of world time between two balls
SPAWN_POSITION = (-95, 5)
SPAWN_IMPULSE = (500, -500)
BALL_RADIUS = 2

# the walls, from the bottom of the slope up, around and down into the pit; the ski
# jump closes the loop
OUTLINE = [(0, -35), (-100, 0), (-100, 100), (200, 100), (200, -100), (100, -100)]


def ski_jump(n_points=100):
    """a curve from the lip of the jump at (60, -45) down to its bottom at (50, -50)
    (a quadratic bezier, its control point below and right of the bottom)"""
    (x0, y0), (x1, y1) = (50, -50), (60, -45)
    reach = 0.5 * math.hypot(x1 - x0, y1 - y0) / math.sqrt(2)
    cx, cy = x0 + reach, y0 - reach
    points = []
    for i in range(n_points):
        t = 1 - i / (n_points - 1)
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t**2 * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t**2 * y1
        points.append((x, y))
    return points


@register_sample("Games", "Jump")
class Jump(SampleBase):
    """A stream of balls (up to 3000) shot down a slope over a ski jump into a pit.

    Keys: hold g to switch gravity off.
    Mouse: double click for an explosion.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity(GRAVITY))
        self.anchor_body.create_chain(b2d.chain_def(points=OUTLINE + ski_jump(), is_loop=True))
        self.balls_added = 0
        self.next_ball_time = 0.0

    def aabb(self):
        return b2d.aabb(lower_bound=(-100, -100), upper_bound=(100, 100))

    def pre_update(self, dt):
        if self.balls_added < MAX_BALLS and self.world_time >= self.next_ball_time:
            self.next_ball_time = self.world_time + SPAWN_INTERVAL
            self.add_ball()

    def add_ball(self):
        ball = self.world.create_dynamic_body(
            position=SPAWN_POSITION, angular_damping=0.01, linear_damping=0.01
        )
        material = b2d.surface_material(
            restitution=0, friction=0.0, custom_color=b2d.random_hex_color()
        )
        ball.create_shape(
            b2d.shape_def(density=1, material=material), b2d.circle(radius=BALL_RADIUS)
        )
        ball.apply_linear_impulse_to_center(SPAWN_IMPULSE)
        self.balls_added += 1

    def on_key_down(self, event):
        if event.key == "g":
            self.world.gravity = (0, 0)

    def on_key_up(self, event):
        if event.key == "g":
            self.world.gravity = GRAVITY

    def on_double_click(self, event):
        self.world.explode(position=event.world_position, radius=70, impulse_per_length=200)
