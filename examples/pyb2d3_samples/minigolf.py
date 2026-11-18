"""A minigolf lane seen from above; once the ball drops in, a stiff distance joint pulls it
spinning into the hole."""

from enum import Enum

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

BALL_RADIUS = 0.1
HOLE_RADIUS = 0.2
MAX_DRAG = 1.0  # the longest drag (the strongest putt)
PUTT_STRENGTH = 15.0


class State(Enum):
    AIMING = 0  # waiting for a click on the ball
    DRAGGING = 1  # the mouse drag sets the strength of the putt
    ROLLING = 2  # waiting for the ball to come to rest
    IN_HOLE = 3  # the level restarts once the ball rests in the hole


@register_sample("Games", "Minigolf")
class Minigolf(SampleBase):
    """A minigolf lane seen from above; a distance joint pulls the ball into the hole.
    Mouse: press on the ball, drag back and release to putt (yellow to red: the
    strength). The level restarts once the ball is in.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.create_course()
        self.create_ball()
        self.state = State.AIMING
        self.drag_position = None

    def create_course(self):
        builder = b2d.PathBuilder((0, 0))
        builder.line_to(right=4)
        self.hole_position = builder.arc_to(
            up=2, radius=1.5, clockwise=False, segments=60, major_arc=True
        )
        builder.line_to(left=4)
        builder.line_to(down=2)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True, reverse=True))
        xs = [p[0] for p in builder.points]
        ys = [p[1] for p in builder.points]
        self.view = b2d.aabb(
            lower_bound=(min(xs) - 3, min(ys) - 1), upper_bound=(max(xs) + 3, max(ys) + 1)
        )

    def create_ball(self):
        self.ball = self.world.create_dynamic_body(
            position=(0.5, 1), linear_damping=0.5, fixed_rotation=True
        )
        self.ball.create_shape(
            b2d.shape_def(density=1, material=b2d.surface_material(restitution=1.0, friction=0.5)),
            b2d.circle(radius=BALL_RADIUS),
        )

    def aabb(self):
        return self.view

    def on_mouse_down(self, event):
        if self.state == State.AIMING and self.ball.shapes[0].test_point(event.world_position):
            self.state = State.DRAGGING
            self.drag_position = self.ball.position

    def on_mouse_move(self, event):
        if self.state == State.DRAGGING:
            drag = (b2d.Vec2(event.world_position) - self.ball.position).clamped(MAX_DRAG)
            self.drag_position = self.ball.position + drag

    def on_mouse_up(self, event):
        if self.state == State.DRAGGING:
            # the ball moves opposite to the drag
            force = (self.drag_position - self.ball.position) * -PUTT_STRENGTH
            self.ball.apply_force_to_center(force, True)
            self.state = State.ROLLING
            self.drag_position = None

    def post_update(self, dt):
        if self.state == State.ROLLING:
            distance_to_hole = (self.ball.position - self.hole_position).length()
            if distance_to_hole < HOLE_RADIUS - BALL_RADIUS:
                self.state = State.IN_HOLE
                # a stiff spring towards the hole center: the ball spins into the hole
                self.world.create_distance_joint(
                    body_a=self.ball,
                    body_b=self.world.create_static_body(position=self.hole_position),
                    length=HOLE_RADIUS / 3.0,
                    enable_spring=True,
                    hertz=100,
                    damping_ratio=1.0,
                )
                return

        if self.ball.speed < 0.01:
            if self.state == State.IN_HOLE:
                self.frontend.set_sample(self.__class__, self.settings)
            elif self.state == State.ROLLING:
                self.state = State.AIMING

    def pre_debug_draw(self):
        # drawn before the bodies: the hole is under the ball
        self.debug_draw.draw_solid_circle(
            transform=b2d.transform(self.hole_position),
            radius=HOLE_RADIUS,
            color=b2d.hex_color(0, 0, 0),
        )
        if self.state == State.DRAGGING:
            # from yellow (weak) to red (strong)
            strength = (self.drag_position - self.ball.position).length() / MAX_DRAG
            color = b2d.hex_color(255, int(255 * (1 - strength)), 0)
            self.debug_draw.draw_segment(self.ball.position, self.drag_position, color=color)
