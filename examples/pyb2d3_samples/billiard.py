"""Billiard: a pool table seen from above, 15 balls racked in a triangle and a white ball."""

import math
import random
from dataclasses import dataclass

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

WIDTH, HEIGHT = 8.0, 4.0
POCKET_RADIUS = 0.5
BALL_RADIUS = 0.2
TABLE_COLOR = (10, 150, 10)
BALL_COLORS = [
    (255, 255, 0),  # yellow
    (0, 0, 255),  # blue
    (255, 0, 0),  # red
    (128, 0, 128),  # purple
    (255, 165, 0),  # orange
    (0, 128, 0),  # green
    (128, 0, 0),  # maroon
]


@dataclass
class Ball:
    color: tuple
    striped: bool = False
    body: b2d.Body = None


@register_sample("Games", "Billiard")
class Billiard(SampleBase):
    """A pool table without gravity: a chain with arcs for the six pockets.
    Mouse: press on the white ball, drag back and release; a longer line shoots harder.
    Pocketing the white or the black ball restarts the game.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.create_table()
        self.create_balls()
        self.rolling = False  # no shots until all balls rest
        self.aim_start = self.aim_end = None  # the aiming line while the mouse is down

        if self.frontend.settings.headless:  # nobody plays: one break shot
            self.white.body.apply_linear_impulse_to_center((3.5, 0.1), wake=True)
            self.rolling = True

    def create_table(self):
        """the cushions: one chain around the table, an arc around each pocket"""
        corner = POCKET_RADIUS * 1.3
        middle = POCKET_RADIUS * math.sqrt(2) * 1.3
        path = b2d.PathBuilder((-WIDTH / 2, HEIGHT / 2))
        self.pockets = []

        def pocket(dx, dy):
            center = path.arc_to(
                delta=(dx, dy), radius=POCKET_RADIUS, clockwise=False, segments=20, major_arc=True
            )
            self.pockets.append(center)

        pocket(-corner, -corner)  # top left
        path.line_to(down=HEIGHT)
        pocket(corner, -corner)  # bottom left
        path.line_to(right=WIDTH / 2)
        pocket(middle, 0)  # bottom middle
        path.line_to(right=WIDTH / 2)
        pocket(corner, corner)  # bottom right
        path.line_to(up=HEIGHT)
        pocket(-corner, corner)  # top right
        path.line_to(left=WIDTH / 2)
        pocket(-middle, 0)  # top middle
        path.line_to(left=WIDTH / 2)

        material = b2d.surface_material(restitution=1.0, custom_color=b2d.hex_color(*TABLE_COLOR))
        self.anchor_body.create_chain(path.chain_def(is_loop=True, reverse=True, material=material))
        # half way between the two middle pockets
        (bx, by), (tx, ty) = self.pockets[2], self.pockets[5]
        self.center = ((bx + tx) / 2, (by + ty) / 2)

    def create_balls(self):
        """a triangle of 15 balls (yellow at the tip, black in the middle) and the white"""
        colored = [Ball(color, striped) for color in BALL_COLORS for striped in (False, True)]
        rest = colored[1:]
        random.shuffle(rest)
        self.black = Ball((0, 0, 0))
        rack = [colored[0], *rest]
        rack.insert(4, self.black)  # the middle of the third row

        cx, cy = self.center
        k = 0
        for row in range(5):
            for i in range(row + 1):
                x = cx + row * BALL_RADIUS * math.sqrt(3)
                y = cy - row * BALL_RADIUS + i * 2 * BALL_RADIUS
                self.create_ball(rack[k], (x, y))
                k += 1

        self.white = Ball((255, 255, 255))
        self.create_ball(self.white, (cx - WIDTH / 4, cy))
        self.balls = rack + [self.white]

    def create_ball(self, ball, position):
        ball.body = self.world.create_dynamic_body(
            position=position, linear_damping=0.8, fixed_rotation=True
        )
        material = b2d.surface_material(custom_color=b2d.hex_color(*ball.color), restitution=1.0)
        ball.body.create_shape(b2d.shape_def(material=material), b2d.circle(radius=BALL_RADIUS))

    def aabb(self):
        cx, cy = self.center
        hx, hy = WIDTH / 2 + 6.0, HEIGHT / 2 + 6.0
        return b2d.aabb(lower_bound=(cx - hx, cy - hy), upper_bound=(cx + hx, cy + hy))

    def on_mouse_down(self, event):
        pos = event.world_position
        if not self.rolling and self.white.body.shapes[0].test_point(point=pos):
            self.aim_start = self.aim_end = pos

    def on_mouse_move(self, event):
        if self.aim_start is not None:
            self.aim_end = event.world_position

    def on_mouse_up(self, event):
        if self.aim_start is not None:
            # the white ball is shot away from the mouse, at the point where it was hit
            p = self.white.body.position
            impulse = (p[0] - self.aim_end[0], p[1] - self.aim_end[1])
            self.white.body.apply_linear_impulse(impulse, self.aim_start)
            self.rolling = True
            self.aim_start = self.aim_end = None

    def pre_update(self, dt):
        if self.rolling and all(ball.body.speed <= 0.0001 for ball in self.balls):
            self.rolling = False

        for ball in list(self.balls):
            p = ball.body.position
            in_pocket = (
                math.hypot(p[0] - c[0], p[1] - c[1]) < POCKET_RADIUS - BALL_RADIUS
                for c in self.pockets
            )
            if any(in_pocket):
                if ball is self.white or ball is self.black:
                    self.frontend.set_sample(type(self), self.settings)  # restart
                    return
                self.balls.remove(ball)
                ball.body.destroy()

    def pre_debug_draw(self):
        for pocket in self.pockets:
            self.debug_draw.draw_solid_circle(
                transform=b2d.transform(pocket), radius=POCKET_RADIUS, color=(0, 0, 0)
            )

    def post_debug_draw(self):
        dd = self.debug_draw
        for ball in self.balls:
            t = ball.body.transform
            dd.draw_solid_circle(transform=t, radius=BALL_RADIUS, color=ball.color)
            if ball.striped:
                dd.draw_solid_circle(transform=t, radius=BALL_RADIUS / 2, color=(255, 255, 255))
        if self.aim_start is not None:
            dd.draw_solid_circle(
                transform=b2d.transform(self.aim_start), radius=0.1, color=(255, 0, 0)
            )
            dd.draw_segment(self.aim_start, self.aim_end, color=(255, 0, 0))
