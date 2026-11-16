"""Rain: a shower of recycled drops over umbrellas walking to and fro (numpy masks
+ batch calls)."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .batch_common import ParticlePool


@register_sample("Fluids & Matter", "Rain")
class BatchRain(SampleBase):
    """A shower of drops falls on umbrellas walking to and fro; the drops splash on
    the ground and are recycled.

    Mouse: grab an umbrella and hold it where you like (it walks on when let go).
    Sliders: rain rate and wind.
    Hint: all drops move with one batch call per step; they come from a fixed pool,
    parked drops are recycled for new ones.
    """

    ground = 0.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.rate = 300.0  # drops / s
        self.wind = 2.0
        self.rng = np.random.default_rng(17)
        self.time = 0.0
        self.splashes = []  # (position, time) of drops hitting the ground
        self.budget = 0.0

        ground = self.world.create_static_body(position=(0.0, self.ground))
        ground.create_shape(
            b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.DimGray)),
            b2d.box(14.0, 0.25, center=(0.0, -0.25)),
        )
        # umbrellas: dynamic (draggable, pushed by the rain), no gravity, upright; a
        # spring force walks them along their path
        self.umbrellas = []
        cloth = [b2d.HexColor.Crimson, b2d.HexColor.Gold, b2d.HexColor.MediumSeaGreen]
        for k, (x, y, period) in enumerate(((-6.0, 3.2, 7.0), (0.5, 4.0, 9.5), (6.0, 3.5, 6.0))):
            umbrella = self.world.create_dynamic_body(
                position=(x, y), gravity_scale=0.0, fixed_rotation=True, enable_sleep=False
            )
            canopy = b2d.shape_def(
                material=b2d.surface_material(friction=0.2, custom_color=cloth[k])
            )
            angles = np.linspace(math.radians(15), math.radians(165), 12)
            arc = np.stack([1.8 * np.cos(angles), 0.8 * np.sin(angles)], axis=1)
            # thick canopy: a drop falls ~0.2 m per step, a thin canopy would let drops
            # tunnel through
            for p, q in zip(arc[:-1], arc[1:]):
                umbrella.create_shape(canopy, b2d.capsule(tuple(p), tuple(q), 0.16))
            handle = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.Black))
            umbrella.create_shape(handle, b2d.capsule((0.0, 0.8), (0.0, -2.0), 0.04))
            self.umbrellas.append((umbrella, np.array([x, y]), period))

        no_drop_contacts = b2d.make_filter(group_index=-1)  # drops pass through each other
        self.pool = ParticlePool(
            self.world,
            1200,
            0.045,
            int(b2d.HexColor.LightSkyBlue.value),
            parking=(0.0, -50.0),
            restitution=0.0,
            friction=0.0,
            enable_sleep=False,
        )
        for shape in self.pool.shapes:
            shape.filter = no_drop_contacts

        for widget in (
            widgets.FloatSlider("rain (drops/s)", 20.0, 800.0, 10.0, self.rate, self.set_rate),
            widgets.FloatSlider("wind", -8.0, 8.0, 0.25, self.wind, self.set_wind),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-12.0, -1.0), upper_bound=(12.0, 13.0))

    def set_rate(self, value):
        self.rate = value

    def set_wind(self, value):
        self.wind = value

    # ---- simulation -----------------------------------------------------------------------

    def walk(self, dt):
        """a critically damped spring pulls every umbrella that is not held along its path"""
        omega = 2.0 * math.pi * 1.0  # 1 Hz
        for umbrella, base, period in self.umbrellas:
            if umbrella == self.mouse_joint_body:
                continue
            target = base + (2.5 * math.sin(2.0 * math.pi * self.time / period), 0.0)
            position = np.array(tuple(umbrella.position))
            velocity = np.array(tuple(umbrella.linear_velocity))
            accel = omega**2 * (target - position) - 2.0 * omega * velocity
            umbrella.apply_force_to_center(tuple(umbrella.mass * accel))

    def pre_update(self, dt):
        """umbrellas walk, new drops at the top, drops on the ground are parked"""
        self.walk(dt)
        pool = self.pool
        pool.step(dt)
        positions = pool.bodies.position
        landed = pool.active & (positions[:, 1] < self.ground + 0.12)
        expired = pool.active & ((pool.age > 6.0) | (np.abs(positions[:, 0]) > 16.0))
        if landed.any():
            self.splashes.extend((tuple(p), self.time) for p in positions[landed])
        pool.park(landed | expired)
        self.splashes = [s for s in self.splashes if self.time - s[1] < 0.25][-400:]
        self.budget += self.rate * dt
        k = int(self.budget)
        if k:
            self.budget -= k
            start = np.stack(
                [self.rng.uniform(-14.0, 14.0, k) - 0.6 * self.wind, np.full(k, 12.5)], axis=1
            )
            velocity = np.stack([np.full(k, self.wind), self.rng.uniform(-12.0, -9.0, k)], axis=1)
            pool.emit(start, velocity)
        flying = pool.bodies[pool.active]
        if len(flying):
            # air drag towards the wind (one batch call for all drops in flight)
            relative = np.array([self.wind, 0.0]) - flying.linear_velocity
            relative[:, 1] = 0.0
            flying.apply_force_to_center(0.8 * flying.mass[:, None] * relative)
        self.time += dt

    # ---- drawing --------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        for (x, y), t in self.splashes:  # little splashes
            s = 0.25 - (self.time - t)
            dd.draw_segment((x, y), (x - s, y + s), b2d.HexColor.LightSkyBlue)
            dd.draw_segment((x, y), (x + s, y + s), b2d.HexColor.LightSkyBlue)
        text = f"{int(self.pool.active.sum())} / {len(self.pool)} drops in the air, wind {self.wind:+.1f}"
        dd.draw_string((-11.5, 12.5), text, b2d.HexColor.White)
