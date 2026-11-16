"""Creating many bodies: a python loop or the batch API, timed."""

import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import hsv_colors

BATCH, LOOP = "batch API", "python loop"


@register_sample("Batch API", "Batch Creation")
class BatchCreation(SampleBase):
    """Many circles (own radius and color each) created with a python loop or with the
    batch API, timed.
    Buttons: create them one way or the other. Slider: number of bodies.
    """

    half = 30.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.count = 5000
        self.rng = np.random.default_rng(3)
        self.times = {}
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=self.half, hy=self.half))
        self.bodies = b2d.Bodies()
        self.create(LOOP)
        self.create(BATCH)
        for widget in (
            widgets.Button("create (python loop)", lambda: self.create(LOOP)),
            widgets.Button("create (batch API)", lambda: self.create(BATCH)),
            widgets.IntSlider("bodies", 500, 10000, 500, self.count, self.set_count),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-self.half, -self.half), upper_bound=(self.half, self.half))

    def set_count(self, value):
        self.count = int(value)

    def create(self, way):
        """new bodies (the old ones destroyed): random positions, radii and colors"""
        self.bodies.destroy()
        n = self.count
        positions = self.rng.uniform(-self.half + 1.0, self.half - 1.0, (n, 2))
        radii = self.rng.uniform(0.1, 0.3, n)
        colors = hsv_colors(self.rng.uniform(0.0, 1.0, n))
        start = time.perf_counter()
        if way == BATCH:
            self.bodies = self.world.create_dynamic_bodies(n)
            self.bodies.position = positions
            circles = [b2d.circle(radius=float(r)) for r in radii]
            self.bodies.create_shape(b2d.shape_def(), circles).custom_color = colors
        else:
            bodies = []
            for (x, y), r, color in zip(positions, radii, colors):
                body = self.world.create_dynamic_body(position=(float(x), float(y)))
                material = b2d.surface_material(custom_color=int(color))
                body.create_shape(b2d.shape_def(material=material), b2d.circle(radius=float(r)))
                bodies.append(body)
            self.bodies = b2d.Bodies(bodies)
        self.times[way] = (n, 1000.0 * (time.perf_counter() - start))

    def post_debug_draw(self):
        lines = [f"{way}: {n} bodies in {ms:.1f} ms" for way, (n, ms) in self.times.items()]
        (n_loop, loop), (n_batch, batch) = (
            self.times.get(LOOP, (0, 0)),
            self.times.get(BATCH, (0, 0)),
        )
        if loop and batch and n_loop == n_batch:
            lines.append(f"batch is {loop / batch:.1f}x faster")
        for i, line in enumerate(lines):
            self.debug_draw.draw_string(
                (-self.half + 1.0, self.half - 1.5 - 1.5 * i), line, b2d.HexColor.White
            )
