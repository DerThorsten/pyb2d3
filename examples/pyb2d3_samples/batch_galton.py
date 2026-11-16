"""A Galton board: balls bounce through rows of pegs and pile up as a binomial distribution."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import ParticlePool, draw_histogram


@register_sample("Granular", "Galton Board")
class BatchGalton(SampleBase):
    """A Galton board: balls fall through pegs into bins, which fill like the
    binomial distribution (white curve).
    Sliders: rate, number of balls; "reset" empties the bins.
    """

    rows = 12
    spacing = 0.6  # between pegs: about 3 ball diameters, the balls hit every row
    ball_radius = 0.1
    peg_radius = 0.08  # gaps of ~2 ball diameters: no arching
    # like a tilted board: the balls roll slowly (terminal speed g / damping) and
    # lose their sideways speed within about one row
    damping = 4.0
    bin_height = 10.0  # the middle bin gets ~23 % of the balls: deep enough for 500

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.rate = 25.0
        self.total = 400
        self.rng = np.random.default_rng(4)
        self.top = self.rows * self.spacing * math.sqrt(3) / 2 + 2.0
        self.create_board()
        self.pool = None
        self.reset()
        for widget in (
            widgets.FloatSlider("rate (1/s)", 2.0, 80.0, 1.0, self.rate, self.set_rate),
            widgets.IntSlider("balls", 100, 500, 50, self.total, self.set_total),
            widgets.Button("reset", self.reset),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        w = (self.rows + 2) * self.spacing / 2 + 1.0
        return b2d.aabb(lower_bound=(-w, -self.bin_height - 1.0), upper_bound=(w, self.top + 1.5))

    def create_board(self):
        board = self.world.create_static_body()
        peg_def = b2d.shape_def(
            material=b2d.surface_material(restitution=0.0, custom_color=b2d.HexColor.Silver)
        )
        dy = self.spacing * math.sqrt(3) / 2
        half_width = (self.rows + 1) / 2 * self.spacing
        for row in range(self.rows):
            y = self.top - 1.5 - row * dy
            # the triangle continued to the side walls: a ball bouncing out of the
            # triangle keeps hitting pegs instead of falling into an outer bin
            for k in range(-self.rows, 2 * self.rows):
                x = (k - row / 2) * self.spacing
                # no peg closer to a wall than a ball diameter (or a ball wedges in)
                if abs(x) + self.peg_radius + 2.2 * self.ball_radius <= half_width:
                    board.create_shape(peg_def, b2d.circle(center=(x, y), radius=self.peg_radius))
        # funnel above the first peg
        wall_def = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.DimGray))
        board.create_shape(wall_def, b2d.segment((-2.0, self.top + 1.0), (-0.5, self.top - 0.6)))
        board.create_shape(wall_def, b2d.segment((2.0, self.top + 1.0), (0.5, self.top - 0.6)))
        # bins: one between every two pegs of the last row (+ the outer ones)
        self.bin_edges = (np.arange(self.rows + 2) - (self.rows + 1) / 2) * self.spacing
        self.bins_top = self.top - 1.5 - self.rows * dy
        for x in self.bin_edges[1:-1]:
            board.create_shape(wall_def, b2d.segment((x, self.bins_top), (x, -self.bin_height)))
        # side walls up to the funnel: balls bouncing off the outer pegs stay on the board
        for x in (self.bin_edges[0], self.bin_edges[-1]):
            board.create_shape(wall_def, b2d.segment((x, self.top + 1.0), (x, -self.bin_height)))
        board.create_shape(
            wall_def,
            b2d.segment(
                (self.bin_edges[0], -self.bin_height), (self.bin_edges[-1], -self.bin_height)
            ),
        )

    def reset(self):
        if self.pool is not None:
            self.pool.destroy()
        self.pool = ParticlePool(
            self.world,
            self.total,
            self.ball_radius,
            int(b2d.HexColor.Gold.value),
            restitution=0.0,
            friction=0.1,
            linear_damping=self.damping,
            enable_sleep=False,
        )  # slow balls on a peg top must not fall asleep
        self.emitted = 0
        self.budget = 0.0

    def set_rate(self, value):
        self.rate = value

    def set_total(self, value):
        self.total = int(value)
        self.reset()

    def pre_update(self, dt):
        if self.emitted >= self.total:
            return
        self.budget += self.rate * dt
        k = min(int(self.budget), self.total - self.emitted)
        if k > 0:
            self.budget -= k
            start = np.stack([self.rng.uniform(-0.4, 0.4, k), np.full(k, self.top + 0.3)], axis=1)
            velocity = np.stack([self.rng.normal(0.0, 0.05, k), np.full(k, -1.0)], axis=1)
            self.pool.emit(start, velocity)
            self.emitted += k

    def histogram(self):
        """balls per bin (only those that arrived in the bins)"""
        positions = self.pool.bodies.position
        arrived = self.pool.active & (positions[:, 1] < self.bins_top)
        counts, _ = np.histogram(positions[arrived, 0], bins=self.bin_edges)
        return counts

    def post_debug_draw(self):
        counts = self.histogram()
        n = counts.sum()
        # binomial(rows + 1 bins): probability of k rights out of `rows` bounces
        k = np.arange(self.rows + 1)
        binomial = np.array([math.comb(self.rows, int(i)) for i in k]) / 2.0**self.rows
        width = self.bin_edges[-1] - self.bin_edges[0]
        draw_histogram(
            self.debug_draw,
            (self.bin_edges[0], -self.bin_height - 0.05),
            (width, self.bin_height * 0.9),
            counts,
            b2d.HexColor.Orange,
            reference=binomial * max(n, 1),
            reference_color=b2d.HexColor.White,
        )
        self.debug_draw.draw_string(
            (self.bin_edges[0], self.top + 1.2),
            f"{n} / {self.total} balls in the bins",
            b2d.HexColor.White,
        )
