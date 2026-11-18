"""A Rube Goldberg machine: a chain reaction of ramps, dominoes, a Newton's
cradle, a see-saw, a bucket full of balls and a water wheel that rings a bell."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.joints import pinned

WOOD = b2d.HexColor.Peru
AUTO_START = 1.0  # seconds
BELL_CENTER = b2d.Vec2(37.2, 4.25)
HAMMER_HEAD = (2.75, 0.22)  # on the lever


GROUND = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.DarkGray))
GOLD = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.Gold))


@register_sample("Demos", "Rube Goldberg", video=True)
class RubeGoldberg(SampleBase):
    """A Rube Goldberg machine: ball, dominoes, Newton's cradle, see-saw, water
    wheel, bell. It starts by itself after a second.
    Keys: space starts it, r rebuilds it.
    Mouse: nudge parts to break (or fix) the chain.
    """

    substeps = 8

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.started = False
        # all static shapes go on the ground body; the joints attach the moving parts to the
        # (shapeless) anchor body: a joint disables the collisions between its two bodies
        self.ground = self.world.create_static_body()
        self.create_start()
        self.create_dominoes()
        self.create_cradle()
        self.create_seesaw()
        self.create_bucket()
        self.create_water_wheel()
        self.create_lever_and_bell()
        self.create_stages()
        self.frontend.add_widget(widgets.Button("start (space)", self.start))
        self.frontend.add_widget(widgets.Button("rebuild (r)", self.rebuild))

    def aabb(self):
        return b2d.aabb(lower_bound=(-21.0, 1.0), upper_bound=(34.0, 21.0))

    # the machine, in the order of the chain reaction
    def create_start(self):
        # the start ball on a slightly sloped ledge, held by a peg, then a ramp down to the dominoes
        for a, b in [((-20.0, 18.3), (-17.0, 18.0)), ((-17.0, 18.0), (-9.0, 14.0))]:
            self.ground.create_shape(GROUND, b2d.segment(a, b))
        self.start_ball = self.world.create_dynamic_body(position=(-17.6, 18.47))
        self.start_ball.create_shape(
            b2d.shape_def(
                density=3.0,
                material=b2d.surface_material(friction=0.4, custom_color=b2d.HexColor.Crimson),
            ),
            b2d.circle(radius=0.4),
        )
        # the peg is its own body: start() destroys it
        self.peg = self.world.create_static_body()
        self.peg.create_shape(GOLD, b2d.segment((-17.05, 18.0), (-17.05, 18.35)))

    def create_dominoes(self):
        self.ground.create_shape(GROUND, b2d.segment((-9.0, 14.0), (1.0, 14.0)))
        domino_def = b2d.shape_def(density=1.0, material=b2d.surface_material(custom_color=WOOD))
        self.dominoes = []
        for i in range(12):
            domino = self.world.create_dynamic_body(position=(-7.5 + 0.7 * i, 14.55))
            domino.create_shape(domino_def, b2d.box(0.08, 0.55))
            self.dominoes.append(domino)

    def create_cradle(self):
        # five balls hanging from a beam, the first one next to the last domino
        beam_y, rope = 18.5, 4.2
        self.ground.create_shape(
            b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.DimGray)),
            b2d.segment((1.2, beam_y), (4.4, beam_y)),
        )
        # no friction, fully elastic: the impulse travels through the balls
        ball_def = b2d.shape_def(
            density=4.0,
            material=b2d.surface_material(
                friction=0.0, restitution=1.0, custom_color=b2d.HexColor.LightSteelBlue
            ),
        )
        for i in range(5):
            x = 1.6 + 0.6 * i
            ball = self.world.create_dynamic_body(position=(x, beam_y - rope))
            ball.create_shape(ball_def, b2d.circle(radius=0.3))
            # a rigid rod: the pivot is the beam point for both bodies
            self.world.create_revolute_joint(**pinned(self.anchor_body, ball, (x, beam_y)))

        # the heavy ball waits on a short ledge after the cradle: one push rolls it onto the ramp
        for a, b in [((4.3, 14.0), (4.85, 14.0)), ((4.85, 14.0), (14.0, 9.5))]:
            self.ground.create_shape(GROUND, b2d.segment(a, b))
        self.heavy_ball = self.world.create_dynamic_body(position=(4.62, 14.31))
        self.heavy_ball.create_shape(
            b2d.shape_def(
                density=4.0,
                material=b2d.surface_material(friction=0.4, custom_color=b2d.HexColor.Black),
            ),
            b2d.circle(radius=0.3),
        )

    def create_seesaw(self):
        # it rests with its right end down (a counterweight there, the lower angle limit); the
        # heavy ball landing in the cup on the raised left end swings the right end up into the bucket
        pivot = b2d.Vec2(18.0, 7.6)
        self.seesaw_rest = -0.4
        self.ground.create_shape(GROUND, b2d.polygon([(17.6, 6.0), (18.4, 6.0), (18.0, 7.4)]))
        self.seesaw = self.world.create_dynamic_body(
            position=pivot, rotation=b2d.make_rot(self.seesaw_rest)
        )
        # the plank reaches further left (-3.8) than right (3.0): the cup sits where the ball lands
        self.seesaw.create_shape(
            b2d.shape_def(
                density=2.0, material=b2d.surface_material(friction=0.4, custom_color=WOOD)
            ),
            b2d.box(3.4, 0.1, center=(-0.4, 0.0)),
        )
        # the counterweight
        self.seesaw.create_shape(
            b2d.shape_def(
                density=4.0, material=b2d.surface_material(custom_color=b2d.HexColor.DimGray)
            ),
            b2d.box(0.25, 0.18, center=(2.6, 0.28)),
        )
        cup_def = b2d.shape_def(density=0.5, material=b2d.surface_material(custom_color=WOOD))
        self.seesaw.create_shape(cup_def, b2d.box(0.06, 0.4, center=(-3.74, 0.45)))
        self.seesaw.create_shape(cup_def, b2d.box(0.06, 0.45, center=(-2.4, 0.5)))
        self.world.create_revolute_joint(
            # q_b = -rest: the joint angle is 0 in the rest pose, the limits are relative to it
            **pinned(self.anchor_body, self.seesaw, pivot, q_b=-self.seesaw_rest),
            enable_limit=True,
            lower_angle=0.0,
            upper_angle=0.95,
        )

    def create_bucket(self):
        # a bucket full of balls on a pivot, leaning a little to the left against a stop
        # (easy to tip over)
        pivot = b2d.Vec2(22.0, 9.0)
        self.bucket = self.world.create_dynamic_body(position=pivot, rotation=b2d.make_rot(0.06))
        self.bucket_angle0 = self.bucket.angle
        bucket_def = b2d.shape_def(
            density=3.0,
            material=b2d.surface_material(friction=0.3, custom_color=b2d.HexColor.SteelBlue),
        )
        self.bucket.create_shape(bucket_def, b2d.box(1.3, 0.08))
        self.bucket.create_shape(bucket_def, b2d.box(0.08, 1.2, center=(-1.3, 1.2)))
        self.bucket.create_shape(bucket_def, b2d.box(0.08, 1.2, center=(1.3, 1.2)))
        self.world.create_revolute_joint(**pinned(self.anchor_body, self.bucket, pivot))
        self.ground.create_shape(GOLD, b2d.segment((20.53, 9.6), (20.53, 10.6)))

        # 10 rows of 10 balls, slightly jittered so that they do not stack perfectly
        rng = np.random.default_rng(2)
        for row in range(10):
            for column in range(10):
                x = -1.0 + 0.222 * column + rng.uniform(-0.005, 0.005)
                ball = self.world.create_dynamic_body(position=pivot + (x, 0.2 + 0.23 * row))
                color = b2d.HexColor.DodgerBlue if column % 2 else b2d.HexColor.DeepSkyBlue
                ball.create_shape(
                    b2d.shape_def(
                        density=1.0, material=b2d.surface_material(friction=0.1, custom_color=color)
                    ),
                    b2d.circle(radius=0.11),
                )

    def create_water_wheel(self):
        # a ramp under the bucket (right of the see-saw's swing) leads the balls onto a wheel
        self.ground.create_shape(GROUND, b2d.segment((21.2, 7.9), (27.5, 6.1)))
        hub = b2d.Vec2(29.5, 6.2)
        self.wheel = self.world.create_dynamic_body(position=hub)
        paddle_def = b2d.shape_def(
            density=0.5, material=b2d.surface_material(friction=0.4, custom_color=WOOD)
        )
        for i in range(8):
            angle = i * math.pi / 4.0
            center = (math.cos(angle), math.sin(angle))
            self.wheel.create_shape(paddle_def, b2d.box(0.75, 0.06, center=center, rotation=angle))
        self.world.create_revolute_joint(**pinned(self.anchor_body, self.wheel, hub))

    def create_lever_and_bell(self):
        # a funnel under the wheel into the cup of a lever; with enough balls in the cup
        # the lever's other end (the hammer) swings up into the bell
        for a, b in [
            ((10.0, 1.0), (41.0, 1.0)),  # the floor
            ((41.0, 1.0), (41.0, 6.0)),
            ((27.2, 4.35), (31.6, 4.0)),  # the funnel: below the paddles, above the cup walls
            ((34.6, 4.8), (33.4, 4.0)),
            ((37.0, 1.0), (37.0, 1.45)),  # the hammer rest
            ((37.7, 1.0), (37.7, 1.45)),
        ]:
            self.ground.create_shape(GROUND, b2d.segment(a, b))
        self.ground.create_shape(GROUND, b2d.polygon([(34.2, 1.0), (34.8, 1.0), (34.5, 2.2)]))

        pivot = b2d.Vec2(34.5, 2.3)
        self.lever_rest = -0.25
        self.lever = self.world.create_dynamic_body(
            position=pivot, rotation=b2d.make_rot(self.lever_rest)
        )
        self.lever.create_shape(
            b2d.shape_def(
                density=0.3, material=b2d.surface_material(friction=0.4, custom_color=WOOD)
            ),
            b2d.box(3.0, 0.07),
        )
        cup_def = b2d.shape_def(
            density=0.5, material=b2d.surface_material(friction=0.3, custom_color=WOOD)
        )
        self.lever.create_shape(cup_def, b2d.box(0.05, 0.35, center=(-2.85, 0.42)))
        self.lever.create_shape(cup_def, b2d.box(0.05, 0.35, center=(-1.35, 0.42)))
        self.lever.create_shape(
            b2d.shape_def(
                density=2.0, material=b2d.surface_material(custom_color=b2d.HexColor.Silver)
            ),
            b2d.box(0.25, 0.15, center=HAMMER_HEAD),
        )
        self.world.create_revolute_joint(
            **pinned(self.anchor_body, self.lever, pivot, q_b=-self.lever_rest),
            enable_limit=True,
            lower_angle=0.0,
            upper_angle=0.65,  # relative to the rest pose
        )
        self.ground.create_shape(GOLD, b2d.circle(center=tuple(BELL_CENTER), radius=0.45))

    def create_stages(self):
        """The steps of the chain reaction, each with a test whether it happened."""
        self.stages = [
            ("start", lambda: self.start_ball.position.x > -16.5),
            ("dominoes", lambda: abs(self.dominoes[0].angle) > 0.3),
            ("last domino", lambda: abs(self.dominoes[-1].angle) > 0.6),
            ("Newton's cradle", lambda: self.heavy_ball.position.x > 5.4),
            ("see-saw", lambda: self.seesaw.angle - self.seesaw_rest > 0.5),
            ("bucket", lambda: self.bucket.angle - self.bucket_angle0 < -0.6),
            ("water wheel", lambda: abs(self.wheel.angle) > 0.5),
            ("lever", lambda: self.lever.angle - self.lever_rest > 0.3),
            ("bell", self.hammer_hits_bell),
        ]
        self.stage_times = {}  # name -> world time when it happened

    def hammer_hits_bell(self):
        head = self.lever.world_point(HAMMER_HEAD)
        return (head - BELL_CENTER).length() < 0.45 + 0.35

    def start(self):
        if not self.started:
            self.peg.destroy()
            self.start_ball.awake = True
            self.started = True

    def rebuild(self):
        self.frontend.set_sample(type(self), self.settings)

    def on_key_down(self, event):
        if event.key == "space":
            self.start()
        elif event.key == "r":
            self.rebuild()

    def post_update(self, dt):
        if not self.started and self.world_time > AUTO_START:
            self.start()
        for name, happened in self.stages:
            if name not in self.stage_times and happened():
                self.stage_times[name] = self.world_time

    def post_debug_draw(self):
        n = len(self.stage_times)
        upcoming = [name for name, _ in self.stages if name not in self.stage_times]
        status = f"next: {upcoming[0]}" if upcoming else "done!"
        self.debug_draw.draw_string(
            (-20.0, 20.5), f"stage {n}/{len(self.stages)}: {status}", b2d.HexColor.White
        )
        if not upcoming:
            self.debug_draw.draw_string(
                tuple(BELL_CENTER + (-0.6, 1.2)), "DING!", b2d.HexColor.Gold
            )
