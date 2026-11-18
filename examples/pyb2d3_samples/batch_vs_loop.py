"""The same vortex force field, computed with a python loop or with the batch API.

Switch the mode and watch the measured time of the force computation (read positions /
velocities, compute, apply) next to box2d's own step time. The vortex follows the mouse.
"""

import math
import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import hsv_colors

BATCH, LOOP = "batch API", "python loop"
HALF = 25.0  # arena half size
RADIUS = 0.25
# the vortex: acceleration = (PULL towards the center + SPIN around it) / (r + 1)^2
#                            - DRAG * velocity
PULL = 30.0
SPIN = 60.0
DRAG = 1.5


def smooth(old, new_ms):
    """a running average of a time in ms: steady numbers on screen"""
    return 0.9 * old + 0.1 * new_ms


@register_sample("Batch API", "Loop vs Batch")
class BatchVsLoop(SampleBase):
    """A vortex on many bodies: a python loop vs. one batch call, timed live.

    Mouse: the vortex follows the cursor.
    Hint: switch "mode" and compare the measured force times next to box2d's step time.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 1000
        self.mode = BATCH
        self.rng = np.random.default_rng(5)
        self.center = (0.0, 0.0)
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=HALF, hy=HALF))
        self.bodies = b2d.Bodies()
        self.create_bodies()
        for widget in (
            widgets.RadioButtons("mode", [BATCH, LOOP], self.mode, self.set_mode),
            widgets.IntSlider("bodies", 200, 5000, 100, self.count, self.set_count),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-HALF, -HALF), upper_bound=(HALF, HALF))

    def create_bodies(self):
        self.bodies.destroy()
        positions = self.rng.uniform(-HALF + 1.0, HALF - 1.0, (self.count, 2))
        colors = hsv_colors(np.linalg.norm(positions, axis=1) / (1.5 * HALF))
        # the same bodies twice: a batch for the batch api and a list for the python loop
        material = b2d.surface_material(friction=0.1)
        self.bodies, shapes = self.world.create_bodies(
            positions, b2d.shape_def(material=material), b2d.circle(radius=RADIUS)
        )
        shapes.custom_color = colors
        self.body_list = list(self.bodies)
        # smoothed times in ms: the force computation of both modes, box2d's step
        self.force_ms = {BATCH: 0.0, LOOP: 0.0}
        self.step_ms = 0.0

    def set_count(self, value):
        self.count = int(value)
        self.create_bodies()

    def set_mode(self, value):
        self.mode = value

    # the same field, twice
    def field_batch(self):
        bodies = self.bodies
        delta = self.center - bodies.position
        falloff = 1.0 / (np.linalg.norm(delta, axis=1) + 1.0)
        tangent = np.stack([-delta[:, 1], delta[:, 0]], axis=1)
        accel = (PULL * delta + SPIN * tangent) * (falloff**2)[:, None]
        accel -= DRAG * bodies.linear_velocity
        bodies.apply_force_to_center(bodies.mass[:, None] * accel)

    def field_loop(self):
        cx, cy = self.center
        for body in self.body_list:
            p = body.position
            v = body.linear_velocity
            dx, dy = cx - p.x, cy - p.y
            falloff = 1.0 / (math.hypot(dx, dy) + 1.0)
            ax = (PULL * dx - SPIN * dy) * falloff**2 - DRAG * v.x
            ay = (PULL * dy + SPIN * dx) * falloff**2 - DRAG * v.y
            body.apply_force_to_center((body.mass * ax, body.mass * ay))

    def pre_update(self, dt):
        if self.mouse_pos is not None:
            self.center = tuple(self.mouse_pos)
        t0 = time.perf_counter()
        if self.mode == BATCH:
            self.field_batch()
        else:
            self.field_loop()
        ms = 1000.0 * (time.perf_counter() - t0)
        self.force_ms[self.mode] = smooth(self.force_ms[self.mode], ms)

    def update(self, dt):
        t0 = time.perf_counter()
        super().update(dt)
        self.step_ms = smooth(self.step_ms, 1000.0 * (time.perf_counter() - t0))

    def post_debug_draw(self):
        dd = self.debug_draw
        dd.draw_point(self.center, 10.0, b2d.HexColor.Gold)
        lines = [f"{len(self.bodies)} bodies, box2d step: {self.step_ms:.2f} ms"]
        for mode, ms in self.force_ms.items():
            value = f"{ms:.3f} ms" if ms > 0 else "-"
            marker = ">" if mode == self.mode else " "
            lines.append(f"{marker} {mode}: {value}")
        batch, loop = self.force_ms[BATCH], self.force_ms[LOOP]
        if batch > 0 and loop > 0:
            lines.append(f"batch is {loop / batch:.0f}x faster")
        for i, line in enumerate(lines):
            dd.draw_string((0.0, HALF - 1.5 - 1.5 * i), line, b2d.HexColor.White)
