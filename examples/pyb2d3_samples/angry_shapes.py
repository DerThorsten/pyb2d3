"""A slingshot game: a ball shot at a pyramid of blocks explodes on impact."""

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

BALL_RADIUS = 1.0
SLINGSHOT = b2d.Vec2(-30, 2)  # where the ball waits
SLINGSHOT_STRENGTH = 50.0
BALL_COLOR = b2d.hex_color(200, 50, 50)
BOUNCY = b2d.surface_material(restitution=0.5)


@register_sample("Games", "Angry Shapes", video=True)
class AngryShapes(SampleBase):
    """A slingshot game: shoot a ball at a pyramid of blocks, it explodes on impact.

    Mouse: drag the red ball away from its anchor and release to launch it.
    The further you pull, the stronger the shot. A new ball appears after each hit.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.anchor_body.create_shape(b2d.shape_def(material=BOUNCY), b2d.segment((-1, 0), (28, 0)))
        self.create_pyramid(levels=10, thickness=0.5, length=3.0)
        self.ball = None  # the flying ball
        self.ball_position = SLINGSHOT  # the waiting ball (drawn, not simulated yet)
        self.dragging = False

    def create_pyramid(self, levels, thickness, length):
        """Upright blocks, each pair bridged by a lying block, fewer per level."""
        shape_def = b2d.shape_def(density=1, material=BOUNCY)
        upright = b2d.box(hx=thickness / 2, hy=length / 2)
        lying = b2d.box(hx=length / 2, hy=thickness / 2)
        for level in range(levels):
            y = level * (length + thickness)
            for i in range(levels - level):
                x = (i + level / 2) * length
                body = self.world.create_dynamic_body(position=(x, y + length / 2))
                body.create_shape(shape_def, upright)
                if i + 1 < levels - level:
                    body = self.world.create_dynamic_body(
                        position=(x + length / 2, y + length + thickness / 2)
                    )
                    body.create_shape(shape_def, lying)

    def aabb(self):
        return b2d.aabb(lower_bound=(-50, -10), upper_bound=(35, 60))

    def on_mouse_down(self, event):
        if self.ball is None and b2d.distance(event.world_position, SLINGSHOT) <= BALL_RADIUS:
            self.dragging = True

    def on_mouse_move(self, event):
        if self.dragging:
            self.ball_position = b2d.Vec2(event.world_position)

    def on_mouse_up(self, event):
        if not self.dragging:
            return
        self.dragging = False
        self.ball = self.world.create_dynamic_body(position=self.ball_position)
        self.ball.create_shape(
            b2d.shape_def(density=1, material=BOUNCY, enable_contact_events=True),
            b2d.circle(radius=BALL_RADIUS),
        )
        # the further from the slingshot, the stronger the shot
        self.ball.apply_linear_impulse_to_center(
            (SLINGSHOT - event.world_position) * SLINGSHOT_STRENGTH
        )

    def pre_update(self, dt):
        if self.ball is None:
            return
        # only the ball has contact events enabled: any begin event is a hit
        if self.world.get_contact_events().begin_count > 0:
            self.world.explode(position=self.ball.position, radius=5, impulse_per_length=5)
            self.reload()
        elif self.ball.position.y < -50 or self.ball.position.x > 130:
            self.reload()

    def reload(self):
        self.ball.destroy()
        self.ball = None
        self.ball_position = SLINGSHOT

    def post_debug_draw(self):
        if self.dragging:
            self.debug_draw.draw_segment(p1=SLINGSHOT, p2=self.ball_position, color=BALL_COLOR)
        if self.ball is None:
            self.debug_draw.draw_solid_circle(
                transform=b2d.transform(p=self.ball_position), radius=BALL_RADIUS, color=BALL_COLOR
            )
