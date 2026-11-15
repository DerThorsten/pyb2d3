"""A Rube Goldberg machine: a chain reaction of ramps, dominoes, a Newton's
cradle, a see-saw, a bucket full of balls and a water wheel that rings a bell."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .examples_common.joints import pinned

STEEL = b2d.HexColor.LightSteelBlue
WOOD = b2d.HexColor.Peru


class Stage:
    """one step of the chain reaction: `done()` becomes true once it happened"""

    def __init__(self, name, done):
        self.name = name
        self.done = done
        self.time = None  # world time it happened


class RubeGoldberg(SampleBase):
    """A Rube Goldberg machine: ball -> dominoes -> Newton's cradle -> ramp ->
    see-saw -> bucket of balls -> water wheel -> bell.

    Keys: space starts the machine, r rebuilds it.
    Hint: it starts by itself after a second; watch the stage counter on top, and
    try nudging parts with the mouse to break (or fix) the chain.
    """

    substeps = 8
    auto_start = 1.0  # seconds
    bucket_balls = 100  # 10 rows of 10: they fit inside the bucket

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.build()
        for widget in (
            widgets.Button("start (space)", self.start),
            widgets.Button("rebuild (r)", self.rebuild),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-21.0, 1.0), upper_bound=(34.0, 21.0))

    # ---- helpers --------------------------------------------------------------------------

    def static_shapes(self, shapes, color=b2d.HexColor.DarkGray, friction=0.6):
        """one static body with the given (segment / polygon) geometries"""
        body = self.world.create_static_body()
        shape_def = b2d.shape_def(material=b2d.surface_material(friction=friction, custom_color=color))
        for geometry in shapes:
            body.create_shape(shape_def, geometry)
        self.parts.append(body)
        return body

    def dynamic(self, position, geometry, density=1.0, color=STEEL, friction=0.4, restitution=0.0, rotation=0.0, **kwargs):
        body = self.world.create_dynamic_body(position=position, rotation=b2d.make_rot(rotation), **kwargs)
        material = b2d.surface_material(friction=friction, restitution=restitution, custom_color=color)
        body.create_shape(b2d.shape_def(density=density, material=material), geometry)
        self.parts.append(body)
        return body

    # ---- the machine ----------------------------------------------------------------------

    def build(self):
        self.parts = []
        self.started = False

        # 1: the start ball on a slightly sloped ledge, held by a peg, then a ramp down to the domino shelf
        self.static_shapes([
            b2d.segment((-20.0, 18.3), (-17.0, 18.0)),
            b2d.segment((-17.0, 18.0), (-9.0, 14.0)),
            b2d.segment((-9.0, 14.0), (1.0, 14.0)),  # domino shelf
        ])
        self.start_ball = self.dynamic((-17.6, 18.47), b2d.circle(radius=0.4), density=3.0, color=b2d.HexColor.Crimson)
        self.peg = self.static_shapes([b2d.segment((-17.05, 18.0), (-17.05, 18.35))], color=b2d.HexColor.Gold)

        # 2: dominoes
        self.dominoes = [
            self.dynamic((-7.5 + 0.7 * i, 14.55), b2d.box(0.08, 0.55), density=1.0, color=WOOD, friction=0.6)
            for i in range(12)
        ]

        # 3: Newton's cradle: five balls hanging from a beam, the first one next to the last domino
        beam_y, rope = 18.5, 4.2
        anchor = self.static_shapes([b2d.segment((1.2, beam_y), (4.4, beam_y))], color=b2d.HexColor.DimGray)
        self.cradle = []
        for i in range(5):
            x = 1.6 + 0.6 * i
            ball = self.dynamic((x, beam_y - rope), b2d.circle(radius=0.3), density=4.0, restitution=1.0, friction=0.0)
            # a rigid rod: the pivot is the beam point for both bodies
            self.world.create_revolute_joint(**pinned(anchor, ball, (x, beam_y)))
            self.cradle.append(ball)
        # the heavy ball waiting on a ledge after the cradle, then the second ramp
        # (a short ledge: one push from the cradle rolls it onto the ramp)
        self.static_shapes([
            b2d.segment((4.3, 14.0), (4.85, 14.0)),
            b2d.segment((4.85, 14.0), (14.0, 9.5)),
        ])
        self.heavy_ball = self.dynamic((4.62, 14.31), b2d.circle(radius=0.3), density=4.0, color=b2d.HexColor.Black)

        # 4: see-saw: its left arm catches the heavy ball, its right arm kicks the bucket
        # it rests with its right end down (a weight there, the lower angle limit); the heavy
        # ball landing on the raised left end swings the right end up into the bucket
        pivot = b2d.Vec2(18.0, 7.6)
        self.static_shapes([b2d.polygon([(17.6, 6.0), (18.4, 6.0), (18.0, 7.4)])])
        rest = -0.4
        # the plank reaches further left (-3.8) than right (3.0): the cup sits where the ball lands
        self.seesaw = self.dynamic(pivot, b2d.box(3.4, 0.1, center=(-0.4, 0.0)), density=2.0, color=WOOD, rotation=rest)
        # the counterweight keeps it at rest (it outweighs the longer left arm, not the ball)
        weight_def = b2d.shape_def(density=4.0, material=b2d.surface_material(custom_color=b2d.HexColor.DimGray))
        self.seesaw.create_shape(weight_def, b2d.box(0.25, 0.18, center=(2.6, 0.28)))
        # a cup on the left arm catches the ball: it stays there (and tips the see-saw)
        # instead of rolling along the plank
        cup_wall_def = b2d.shape_def(density=0.5, material=b2d.surface_material(custom_color=WOOD))
        self.seesaw.create_shape(cup_wall_def, b2d.box(0.06, 0.4, center=(-3.74, 0.45)))
        self.seesaw.create_shape(cup_wall_def, b2d.box(0.06, 0.45, center=(-2.4, 0.5)))
        self.world.create_revolute_joint(
            # q_b = -rest: the joint angle is 0 in the rest pose, the limits are relative to it
            **pinned(self.static_shapes([]), self.seesaw, pivot, q_b=-rest),
            enable_limit=True, lower_angle=0.0, upper_angle=0.95,
        )

        # 5: a bucket full of balls on a pivot, leaning left against a stop
        bucket_pivot = b2d.Vec2(22.0, 9.0)
        self.bucket = self.world.create_dynamic_body(position=bucket_pivot, rotation=b2d.make_rot(0.06))
        bucket_def = b2d.shape_def(density=3.0, material=b2d.surface_material(friction=0.3, custom_color=b2d.HexColor.SteelBlue))
        for geometry in (b2d.box(1.3, 0.08, center=(0.0, 0.0)), b2d.box(0.08, 1.2, center=(-1.3, 1.2)), b2d.box(0.08, 1.2, center=(1.3, 1.2))):
            self.bucket.create_shape(bucket_def, geometry)
        self.parts.append(self.bucket)
        self.world.create_revolute_joint(**pinned(self.static_shapes([]), self.bucket, bucket_pivot))
        # the stop: the bucket leans only a little (easy to tip over)
        self.static_shapes([b2d.segment((20.53, 9.6), (20.53, 10.6))], color=b2d.HexColor.Gold)
        rng = np.random.default_rng(2)
        self.bucket_bodies = []
        for k in range(self.bucket_balls):
            row, column = divmod(k, 10)
            p = bucket_pivot + (-1.0 + 0.222 * column + rng.uniform(-0.005, 0.005), 0.2 + 0.23 * row)
            color = int(b2d.HexColor.DodgerBlue.value if k % 2 else b2d.HexColor.DeepSkyBlue.value)
            self.bucket_bodies.append(self.dynamic(p, b2d.circle(radius=0.11), density=1.0, color=color, friction=0.1))

        # 6: a ramp under the bucket catching the poured balls, leading onto a (balanced)
        # water wheel; it starts right of the see-saw's swing
        self.static_shapes([b2d.segment((21.2, 7.9), (27.5, 6.1))])
        hub = b2d.Vec2(29.5, 6.2)
        self.wheel = self.world.create_dynamic_body(position=hub)
        wheel_def = b2d.shape_def(density=0.5, material=b2d.surface_material(friction=0.4, custom_color=WOOD))
        for i in range(8):
            angle = i * math.pi / 4.0
            c, s = math.cos(angle), math.sin(angle)
            self.wheel.create_shape(wheel_def, b2d.box(0.75, 0.06, center=(1.0 * c, 1.0 * s), rotation=angle))
        self.parts.append(self.wheel)
        self.world.create_revolute_joint(**pinned(self.static_shapes([]), self.wheel, hub))

        # 7: a funnel under the wheel into the cup of a lever; with enough balls in the cup
        # the lever's other end (the hammer) swings up into the bell
        self.static_shapes([
            b2d.segment((10.0, 1.0), (41.0, 1.0)), b2d.segment((41.0, 1.0), (41.0, 6.0)),  # floor
            # funnel into the cup: below the paddles of the wheel (down to y=4.45), above the
            # cup walls (up to y=3.8)
            b2d.segment((27.2, 4.35), (31.6, 4.0)), b2d.segment((34.6, 4.8), (33.4, 4.0)),
            b2d.segment((37.0, 1.0), (37.0, 1.45)), b2d.segment((37.7, 1.0), (37.7, 1.45)),  # hammer rest
        ])
        lever_pivot = b2d.Vec2(34.5, 2.3)
        self.static_shapes([b2d.polygon([(34.2, 1.0), (34.8, 1.0), (34.5, 2.2)])])
        lever_rest = -0.25
        self.lever = self.dynamic(lever_pivot, b2d.box(3.0, 0.07), density=0.3, color=WOOD, rotation=lever_rest)
        cup_def = b2d.shape_def(density=0.5, material=b2d.surface_material(friction=0.3, custom_color=WOOD))
        self.lever.create_shape(cup_def, b2d.box(0.05, 0.35, center=(-2.85, 0.42)))
        self.lever.create_shape(cup_def, b2d.box(0.05, 0.35, center=(-1.35, 0.42)))
        head_def = b2d.shape_def(density=2.0, material=b2d.surface_material(custom_color=b2d.HexColor.Silver))
        self.lever.create_shape(head_def, b2d.box(0.25, 0.15, center=(2.75, 0.22)))
        self.world.create_revolute_joint(
            **pinned(self.static_shapes([]), self.lever, lever_pivot, q_b=-lever_rest),
            enable_limit=True, lower_angle=0.0, upper_angle=0.65,  # relative to the rest pose
        )
        self.lever_rest = lever_rest

        # 8: the bell above the hammer
        self.bell_center = b2d.Vec2(37.2, 4.25)
        self.static_shapes([b2d.circle(center=tuple(self.bell_center), radius=0.45)], color=b2d.HexColor.Gold)

        domino0, domino_last = self.dominoes[0], self.dominoes[-1]
        seesaw_angle0 = self.seesaw.angle
        bucket_angle0 = self.bucket.angle
        self.stages = [
            Stage("start", lambda: self.start_ball.position.x > -16.5),
            Stage("dominoes", lambda: abs(domino0.angle) > 0.3),
            Stage("last domino", lambda: abs(domino_last.angle) > 0.6),
            Stage("Newton's cradle", lambda: self.heavy_ball.position.x > 5.4),
            Stage("see-saw", lambda: self.seesaw.angle - seesaw_angle0 > 0.5),
            Stage("bucket", lambda: self.bucket.angle - bucket_angle0 < -0.6),
            Stage("water wheel", lambda: abs(self.wheel.angle) > 0.5),
            Stage("lever", lambda: self.lever.angle - lever_rest > 0.3),
            Stage("bell", self.hammer_hits_bell),
        ]

    def hammer_hits_bell(self):
        head = self.lever.world_point((2.75, 0.22))
        return (head - self.bell_center).length() < 0.45 + 0.35

    def destroy(self):
        self.destroy_mouse_joint()
        for body in self.parts:
            if body.is_valid:
                body.destroy()
        self.parts = []

    # ---- controls -------------------------------------------------------------------------

    def start(self):
        if not self.started and self.peg.is_valid:
            self.peg.destroy()
            self.start_ball.awake = True
            self.started = True

    def rebuild(self):
        self.destroy()
        self.build()

    def on_key_down(self, event):
        if event.key == "space":
            self.start()
        elif event.key == "r":
            self.rebuild()

    # ---- simulation -----------------------------------------------------------------------

    def post_update(self, dt):
        if not self.started and self.world_time > self.auto_start:
            self.start()
        for stage in self.stages:
            if stage.time is None and stage.done():
                stage.time = self.world_time

    @property
    def stages_done(self):
        return sum(stage.time is not None for stage in self.stages)

    def post_debug_draw(self):
        dd = self.debug_draw
        n = self.stages_done
        current = self.stages[n].name if n < len(self.stages) else "done!"
        dd.draw_string((-20.0, 20.5), f"stage {n}/{len(self.stages)}: next: {current}", b2d.HexColor.White)
        if n == len(self.stages):
            dd.draw_string(tuple(self.bell_center + (-0.6, 1.2)), "DING!", b2d.HexColor.Gold)
