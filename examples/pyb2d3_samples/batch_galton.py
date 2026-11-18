"""A Galton board: balls bounce through rows of pegs and pile up as a binomial distribution."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

ROWS = 12
SPACING = 0.6  # between pegs: about 3 ball diameters, the balls hit every row
ROW_HEIGHT = SPACING * math.sqrt(3) / 2
BALL_RADIUS = 0.1
PEG_RADIUS = 0.08  # gaps of ~2 ball diameters: no arching
# like a tilted board: the balls roll slowly (terminal speed g / damping) and
# lose their sideways speed within about one row
DAMPING = 4.0
BIN_HEIGHT = 10.0  # the middle bin gets ~23 % of the balls: deep enough for 500
TOP = ROWS * ROW_HEIGHT + 2.0  # top of the board, the bins start at y = 0.5
BINS_TOP = TOP - 1.5 - ROWS * ROW_HEIGHT
# bins: one between every two pegs of the last row (+ the outer ones)
BIN_EDGES = (np.arange(ROWS + 2) - (ROWS + 1) / 2) * SPACING


@register_sample("Granular", "Galton Board", video=True)
class BatchGalton(SampleBase):
    """A Galton board: balls fall through pegs into bins, which fill like the
    binomial distribution (white curve).
    Sliders: rate, number of balls; "reset" empties the bins.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.rate = 25.0
        self.total = 400
        self.create_pegs()
        self.create_walls()
        self.create_emitter()
        for widget in (
            widgets.FloatSlider("rate (1/s)", 2.0, 80.0, 1.0, self.rate, self.set_rate),
            widgets.IntSlider("balls", 100, 500, 50, self.total, self.set_total),
            widgets.Button("reset", self.reset),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        w = (ROWS + 2) * SPACING / 2 + 1.0
        return b2d.aabb(lower_bound=(-w, -BIN_HEIGHT - 1.0), upper_bound=(w, TOP + 1.5))

    def create_pegs(self):
        pegs = self.world.create_static_body()
        peg_def = b2d.shape_def(
            material=b2d.surface_material(restitution=0.0, custom_color=b2d.HexColor.Silver)
        )
        half_width = BIN_EDGES[-1]
        for row in range(ROWS):
            y = TOP - 1.5 - row * ROW_HEIGHT
            # the triangle continued to the side walls: a ball bouncing out of the
            # triangle keeps hitting pegs instead of falling into an outer bin
            for k in range(-ROWS, 2 * ROWS):
                x = (k - row / 2) * SPACING
                # no peg closer to a wall than a ball diameter (or a ball wedges in)
                if abs(x) + PEG_RADIUS + 2.2 * BALL_RADIUS <= half_width:
                    pegs.create_shape(peg_def, b2d.circle(center=(x, y), radius=PEG_RADIUS))

    def create_walls(self):
        """the funnel, the bins and the side walls"""
        walls = self.world.create_static_body()
        wall_def = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.DimGray))

        left, right, bottom = BIN_EDGES[0], BIN_EDGES[-1], -BIN_HEIGHT
        segments = [
            ((-2.0, TOP + 1.0), (-0.5, TOP - 0.6)),  # the funnel above the first peg
            ((2.0, TOP + 1.0), (0.5, TOP - 0.6)),
            # side walls up to the funnel: balls bouncing off the outer pegs stay on the board
            ((left, TOP + 1.0), (left, bottom)),
            ((right, TOP + 1.0), (right, bottom)),
            ((left, bottom), (right, bottom)),
        ]
        segments += [((x, BINS_TOP), (x, bottom)) for x in BIN_EDGES[1:-1]]  # the bins
        for p, q in segments:
            walls.create_shape(wall_def, b2d.segment(p, q))

    def create_emitter(self):
        """balls emitted along a line over the funnel, `total` at most; they never expire"""
        y = TOP + 0.3
        self.balls = ext.LinearEmitter(
            self.world,
            b2d.shape_def(
                density=1.0,
                material=b2d.surface_material(
                    friction=0.1, restitution=0.0, custom_color=b2d.HexColor.Gold
                ),
            ),
            b2d.circle(radius=BALL_RADIUS),
            # slow balls on a peg top must not fall asleep
            body_def=b2d.body_def(linear_damping=DAMPING, enable_sleep=False),
            seed=4,
            # from right to left: the left normal of the line (the emit direction) points down
            p1=(0.4, y),
            p2=(-0.4, y),
            rate=self.rate,
            capacity=self.total,
            on_capacity_reached=ext.OnCapacityReached.STOP,
            speed=1.0,
            lifetime=math.inf,
        )

    def reset(self):
        self.balls.clear()

    def set_rate(self, value):
        self.rate = self.balls.rate = value

    def set_total(self, value):
        self.total = self.balls.capacity = int(value)
        self.reset()

    def pre_update(self, dt):
        self.balls.step(dt)

    def post_debug_draw(self):
        # balls per bin (only those that arrived in the bins)
        positions = self.balls.particles.position
        arrived = positions[:, 1] < BINS_TOP
        counts, _ = np.histogram(positions[arrived, 0], bins=BIN_EDGES)
        # binomial: probability to bounce right k times out of ROWS, scaled to the ball count
        n = counts.sum()
        expected = [math.comb(ROWS, k) / 2.0**ROWS * max(n, 1) for k in range(ROWS + 1)]
        self.draw_histogram(counts, expected)
        text = f"{n} / {self.total} balls in the bins"
        self.debug_draw.draw_string((BIN_EDGES[0], TOP + 1.2), text, b2d.HexColor.White)

    def draw_histogram(self, counts, expected):
        """orange bars of the counts in the bins, the expected counts as a white curve"""
        dd = self.debug_draw
        bottom = -BIN_HEIGHT - 0.05
        scale = 0.9 * BIN_HEIGHT / max(counts.max(), max(expected), 1.0)
        for k, count in enumerate(counts):
            x0, x1 = BIN_EDGES[k], BIN_EDGES[k + 1]
            y = bottom + scale * count
            dd.draw_segment((x0, bottom), (x0, y), b2d.HexColor.Orange)
            dd.draw_segment((x0, y), (x1, y), b2d.HexColor.Orange)
            dd.draw_segment((x1, y), (x1, bottom), b2d.HexColor.Orange)
        centers = 0.5 * (BIN_EDGES[:-1] + BIN_EDGES[1:])
        curve = [(x, bottom + scale * e) for x, e in zip(centers, expected)]
        for p, q in zip(curve[:-1], curve[1:]):
            dd.draw_segment(p, q, b2d.HexColor.White)
