"""A particle fountain run entirely with masks over a fixed pool of bodies.

Parked particles are disabled. Every step a numpy mask picks the particles to emit (enable,
teleport to the nozzle, set velocities; the oldest ones when the pool runs dry), another one
the expired particles to park again.
Wind drags all flying particles with one `apply_force_to_center` call, and particles are
recolored by speed: only those whose speed band changed get a new material.
"""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import create_circles, destroy_bodies, hsv_colors

# speed bands -> colors (slow: deep blue ... fast: white-ish cyan)
SPEED_BANDS = np.array([3.0, 6.0, 10.0, 15.0])
BAND_COLORS = [int(c) for c in hsv_colors(np.linspace(0.66, 0.5, len(SPEED_BANDS) + 1), np.linspace(0.9, 0.2, 5), 1.0)]


class BatchFountain(SampleBase):
    """A fountain of recycled particles, steered by masks."""

    nozzle = np.array([0.0, 4.0])
    radius = 0.15
    lifetime = 7.0
    rest_speed = 1.5
    wind_drag = 0.6  # 1 / s
    parking = (0.0, -50.0)

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.pool_size = 1000
        self.rate = 250.0  # particles per second
        self.jet_speed = 20.0
        self.spread = 8.0  # degrees
        self.wind = 0.0
        self.rng = np.random.default_rng(3)
        self.bodies = b2d.Bodies()

        self.create_basin()
        self.create_pool()

        for widget in (
            widgets.IntSlider("pool size", 200, 4000, 100, self.pool_size, self.set_pool_size),
            widgets.FloatSlider("rate (1/s)", 20.0, 1000.0, 10.0, self.rate, self.setter("rate")),
            widgets.FloatSlider("jet speed", 5.0, 35.0, 1.0, self.jet_speed, self.setter("jet_speed")),
            widgets.FloatSlider("spread (deg)", 0.0, 30.0, 1.0, self.spread, self.setter("spread")),
            widgets.FloatSlider("wind", -15.0, 15.0, 0.5, self.wind, self.setter("wind")),
        ):
            self.frontend.add_widget(widget)

    def setter(self, name):
        return lambda value: setattr(self, name, value)

    def aabb(self):
        return b2d.aabb(lower_bound=(-22.0, -4.0), upper_bound=(22.0, 32.0))

    def create_basin(self):
        # the nozzle sits on a column; sloped basins on both sides run off into drains
        ground = self.world.create_static_body()
        shape_def = b2d.shape_def(material=b2d.surface_material(friction=0.2))
        ground.create_shape(shape_def, b2d.box(0.5, 0.5 * self.nozzle[1] - 0.2, center=(0.0, 0.5 * self.nozzle[1] - 0.4)))
        for side in (-1.0, 1.0):
            ground.create_shape(shape_def, b2d.segment((side * 0.5, 2.5), (side * 14.0, 0.0)))  # basin
            ground.create_shape(shape_def, b2d.segment((side * 16.0, -1.0), (side * 20.0, 7.0)))  # outer rim
        # drains between basin and rim: particles that fall through are recycled

    def create_pool(self):
        destroy_bodies(self, self.bodies)
        n = self.pool_size
        positions = np.tile(self.parking, (n, 1))
        self.bodies = create_circles(self.world, positions, self.radius, colors=BAND_COLORS[0], restitution=0.2, friction=0.1)
        self.bodies.enabled = False  # everything starts parked
        self.shape_list = [body.shapes[0] for body in self.bodies]  # for the per-shape material changes
        self.active = np.zeros(n, dtype=bool)
        self.age = np.zeros(n)
        self.band = np.zeros(n, dtype=int)
        self.emit_budget = 0.0

    def set_pool_size(self, value):
        self.pool_size = int(value)
        self.create_pool()

    # ---- emit / expire with masks ---------------------------------------------------------

    def pre_update(self, dt):
        self.age[self.active] += dt
        self.expire()
        self.emit(dt)
        if self.wind != 0.0 and self.active.any():
            # linear air drag towards the wind velocity, for the particles in flight only
            flying = self.bodies[self.active]
            relative = np.array([self.wind, 0.0]) - flying.linear_velocity
            flying.apply_force_to_center(self.wind_drag * flying.mass[:, None] * relative)

    def expire(self):
        positions = self.bodies.position
        # too old, out of the basin, or come to rest (the puddle drains away)
        resting = (self.age > 1.0) & (self.bodies.speed < self.rest_speed)
        expired = self.active & (
            (self.age > self.lifetime) | resting | (positions[:, 1] < -5.0) | (np.abs(positions[:, 0]) > 40.0)
        )
        if expired.any():
            parked = self.bodies[expired]
            parked.enabled = False
            self.active &= ~expired

    def emit(self, dt):
        self.emit_budget = min(self.emit_budget + self.rate * dt, float(self.pool_size))
        k = int(self.emit_budget)
        if k == 0:
            return
        self.emit_budget -= k
        free = np.flatnonzero(~self.active)[:k]
        if len(free) < k:
            # pool exhausted: recycle the oldest particles in flight
            flying = np.flatnonzero(self.active)
            oldest = flying[np.argpartition(-self.age[flying], k - len(free) - 1)[: k - len(free)]]
            free = np.concatenate([free, oldest])
        jets = self.bodies[free]
        jets.enabled = True  # enable first: a disabled body ignores velocity changes
        angle = np.radians(self.rng.normal(scale=self.spread, size=k))
        speed = self.jet_speed * self.rng.uniform(0.9, 1.05, k)
        start = self.nozzle + self.rng.uniform(-0.3, 0.3, (k, 2)) * (1.0, 0.2)
        jets.set_transform(start, (1.0, 0.0))
        jets.linear_velocity = speed[:, None] * np.stack([np.sin(angle), np.cos(angle)], axis=1)
        jets.angular_velocity = 0.0
        self.active[free] = True
        self.age[free] = 0.0

    def post_update(self, dt):
        # recolor by speed band; only bodies whose band changed touch their material
        band = np.searchsorted(SPEED_BANDS, self.bodies.speed)
        changed = np.flatnonzero(self.active & (band != self.band))
        for i in changed:
            shape = self.shape_list[i]
            material = shape.surface_material
            material.custom_color = BAND_COLORS[band[i]]
            shape.surface_material = material
        self.band[changed] = band[changed]

    # ---- drawing --------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        dd.draw_point(tuple(self.nozzle), 10.0, b2d.HexColor.LightSkyBlue)
        if self.wind != 0.0:
            arrow = (8.0 + 0.4 * self.wind, 28.0)
            dd.draw_segment((8.0, 28.0), arrow, b2d.HexColor.LightGray)
            dd.draw_point(arrow, 6.0, b2d.HexColor.LightGray)
        text = f"{int(self.active.sum())} / {self.pool_size} particles in flight"
        dd.draw_string((0.0, 30.0), text, b2d.HexColor.White)


if __name__ == "__main__":
    BatchFountain.run()
