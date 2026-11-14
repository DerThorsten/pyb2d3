"""The same vortex force field, computed with a python loop or with the batch API.

Switch the mode and watch the measured time of the force computation (read positions /
velocities, compute, apply) next to box2d's own step time. The vortex follows the mouse.
"""

import math
import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import Ema, create_circles, destroy_bodies, hsv_colors

BATCH, LOOP = "batch API", "python loop"


class BatchVsLoop(SampleBase):
    """A vortex on many bodies: python loop vs. one batch call, timed live."""

    half = 25.0
    radius = 0.25
    pull = 30.0
    spin = 60.0
    drag = 1.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 1000
        self.mode = BATCH
        self.rng = np.random.default_rng(5)
        self.timings = {BATCH: Ema(), LOOP: Ema()}
        self.step_time = Ema()
        self.center = np.zeros(2)
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=self.half, hy=self.half))
        self.bodies = b2d.Bodies()
        self.body_list = []
        self.create_bodies()

        for widget in (
            widgets.RadioButtons("mode", [BATCH, LOOP], self.mode, self.set_mode),
            widgets.IntSlider("bodies", 200, 5000, 100, self.count, self.set_count),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-self.half, -self.half), upper_bound=(self.half, self.half))

    def create_bodies(self):
        destroy_bodies(self, self.bodies)
        n = self.count
        positions = self.rng.uniform(-self.half + 1.0, self.half - 1.0, (n, 2))
        colors = hsv_colors(np.linalg.norm(positions, axis=1) / (1.5 * self.half))
        self.bodies = create_circles(self.world, positions, self.radius, colors=colors, friction=0.1)
        self.body_list = list(self.bodies)
        for ema in self.timings.values():
            ema.value = None

    def set_count(self, value):
        self.count = int(value)
        self.create_bodies()

    def set_mode(self, value):
        self.mode = value

    # ---- the same field, twice ------------------------------------------------------------
    # force = m * (pull towards the center + spin around it - drag * velocity), softened by 1 / (r + 1)

    def field_batch(self):
        bodies = self.bodies
        delta = self.center - bodies.position
        distance = np.linalg.norm(delta, axis=1)
        falloff = 1.0 / (distance + 1.0)
        tangent = np.stack([-delta[:, 1], delta[:, 0]], axis=1)
        accel = (self.pull * delta + self.spin * tangent) * falloff[:, None] ** 2 - self.drag * bodies.linear_velocity
        bodies.apply_force_to_center(bodies.mass[:, None] * accel)

    def field_loop(self):
        cx, cy = self.center
        for body in self.body_list:
            p = body.position
            v = body.linear_velocity
            dx, dy = cx - p.x, cy - p.y
            falloff = 1.0 / (math.hypot(dx, dy) + 1.0)
            f2 = falloff * falloff
            m = body.mass
            ax = (self.pull * dx - self.spin * dy) * f2 - self.drag * v.x
            ay = (self.pull * dy + self.spin * dx) * f2 - self.drag * v.y
            body.apply_force_to_center((m * ax, m * ay))

    def pre_update(self, dt):
        if self.mouse_pos is not None:
            self.center = np.array(self.mouse_pos, dtype=np.float64)
        t0 = time.perf_counter()
        if self.mode == BATCH:
            self.field_batch()
        else:
            self.field_loop()
        self.timings[self.mode](1000.0 * (time.perf_counter() - t0))

    def update(self, dt):
        t0 = time.perf_counter()
        super().update(dt)
        self.step_time(1000.0 * (time.perf_counter() - t0))

    # ---- drawing --------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        dd.draw_point(tuple(self.center), 10.0, b2d.HexColor.Gold)
        lines = [f"{len(self.bodies)} bodies, box2d step: {self.step_time.value or 0.0:.2f} ms"]
        for mode, ema in self.timings.items():
            value = "-" if ema.value is None else f"{ema.value:.3f} ms"
            marker = ">" if mode == self.mode else " "
            lines.append(f"{marker} {mode}: {value}")
        batch, loop = self.timings[BATCH].value, self.timings[LOOP].value
        if batch and loop:
            lines.append(f"batch is {loop / batch:.0f}x faster")
        for i, line in enumerate(lines):
            dd.draw_string((0.0, self.half - 1.5 - 1.5 * i), line, b2d.HexColor.White)


if __name__ == "__main__":
    BatchVsLoop.run()
