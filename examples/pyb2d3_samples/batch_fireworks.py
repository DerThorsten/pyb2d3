"""Fireworks: rockets burst into hundreds of sparks, all from one recycled pool."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .batch_common import ParticlePool, hsv_colors
from .batch_common import create_points  # non-colliding circles

# brightness of the sparks by age (fraction of their lifetime)
FADE_STEPS = np.array([0.45, 0.75])
FADE_VALUES = np.array([1.0, 0.6, 0.3])


class SparkPool(ParticlePool):
    """ParticlePool of non-colliding points (sparks born in one spot must not collide)"""

    def __init__(self, world, size, radius, parking=(0.0, -500.0)):
        positions = np.tile(np.asarray(parking, dtype=np.float64), (size, 1))
        self.bodies = create_points(world, positions, radius, np.full(size, 0xFFFFFF), 1.0)
        self.bodies.enabled = False
        self.active = np.zeros(size, dtype=bool)
        self.age = np.zeros(size)
        self._shapes = None


@register_sample("Fields & Space", "Fireworks")
class BatchFireworks(SampleBase):
    """Rockets burst into sparks from one recycled pool of bodies; air drag is one
    batch call.
    Mouse: click to launch a rocket that bursts there.
    Sliders: launch rate (0: clicks only), sparks, drag.
    """

    gravity = 6.0
    spark_radius = 0.07
    rocket_radius = 0.12
    lifetime = (1.6, 2.6)  # s, per spark
    pool_size = 2500
    width = 18.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -self.gravity)))
        self.rate = 1.2  # rockets per second
        self.sparks_per_burst = 150
        self.drag = 1.2
        self.rng = np.random.default_rng(8)
        self.pool = SparkPool(self.world, self.pool_size, self.spark_radius)
        n = self.pool_size
        self.is_rocket = np.zeros(n, dtype=bool)
        self.fuse = np.zeros(n)  # rockets: seconds until the burst
        self.life = np.ones(n)  # sparks: their lifetime
        self.hue = np.zeros(n)
        self.fade = np.zeros(n, dtype=int)  # current brightness step
        self.budget = 0.0
        self.bursts = 0
        for widget in (
            widgets.FloatSlider("launch rate (1/s)", 0.0, 5.0, 0.1, self.rate, self.set_rate),
            widgets.IntSlider(
                "sparks per burst", 30, 400, 10, self.sparks_per_burst, self.set_sparks
            ),
            widgets.FloatSlider("air drag", 0.0, 4.0, 0.1, self.drag, self.set_drag),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-self.width - 2, -1.0), upper_bound=(self.width + 2, 30.0))

    def set_rate(self, value):
        self.rate = value

    def set_sparks(self, value):
        self.sparks_per_burst = int(value)

    def set_drag(self, value):
        self.drag = value

    # ---- rockets ----------------------------------------------------------------------------

    def recolor(self, indices, colors):
        """new colors for some particles (one material change per particle)"""
        shapes = self.pool.shapes
        for i, color in zip(indices.tolist(), colors.tolist()):
            material = shapes[i].surface_material
            material.custom_color = int(color)
            shapes[i].surface_material = material

    def make_room(self, k):
        """free k pool slots by parking the oldest sparks (a full pool would
        otherwise recycle the oldest particles: rockets in flight)"""
        need = k - int((~self.pool.active).sum())
        if need > 0:
            sparks = np.flatnonzero(self.pool.active & ~self.is_rocket)
            oldest = sparks[np.argsort(-self.pool.age[sparks])[:need]]
            mask = np.zeros(self.pool_size, dtype=bool)
            mask[oldest] = True
            self.pool.park(mask)

    def launch(self, x, height):
        """a rocket from the ground at x that bursts at about `height`"""
        self.make_room(1)
        vy = math.sqrt(2.0 * self.gravity * max(height, 2.0))
        vx = self.rng.normal(0.0, 0.6)
        index = self.pool.emit(np.array([[x, 0.0]]), np.array([[vx, vy]]))
        self.is_rocket[index] = True
        self.fuse[index] = vy / self.gravity  # the apex
        self.recolor(index, np.array([0xFFF4D6]))

    def burst(self, rockets):
        """park the rockets, emit a ball of sparks at each"""
        positions = self.pool.bodies[rockets].position
        velocities = self.pool.bodies[rockets].linear_velocity
        self.pool.park(np.isin(np.arange(self.pool_size), rockets))
        self.is_rocket[rockets] = False
        for position, velocity in zip(positions, velocities):
            k = self.sparks_per_burst
            angle = self.rng.uniform(0.0, 2.0 * math.pi, k)
            speed = self.rng.uniform(0.25, 1.0, k) ** 0.5 * self.rng.uniform(7.0, 10.0)
            v = speed[:, None] * np.stack([np.cos(angle), np.sin(angle)], axis=1) + 0.3 * velocity
            self.make_room(k)
            sparks = self.pool.emit(np.repeat(position[None, :], k, axis=0), v)
            self.is_rocket[sparks] = False
            hue = self.rng.random()
            self.hue[sparks] = hue + self.rng.normal(0.0, 0.03, len(sparks))
            self.life[sparks] = self.rng.uniform(*self.lifetime, len(sparks))
            self.fade[sparks] = 0
            self.recolor(sparks, hsv_colors(self.hue[sparks], 0.7, FADE_VALUES[0]))
            self.bursts += 1

    def on_mouse_down(self, event):
        """click: a rocket that bursts at the click (no dragging / camera)"""
        x, y = event.world_position[0], event.world_position[1]
        self.launch(float(np.clip(x, -self.width, self.width)), float(y))

    def on_mouse_move(self, event):
        pass

    def on_mouse_up(self, event):
        pass

    # ---- the simulation: masks + one batch call -----------------------------------------------

    def pre_update(self, dt):
        """launches, bursts, expired sparks; then the air drag of everything in flight"""
        pool = self.pool
        pool.step(dt)
        self.budget += self.rate * dt
        while self.budget >= 1.0:
            self.budget -= 1.0
            self.launch(self.rng.uniform(-0.8, 0.8) * self.width, self.rng.uniform(14.0, 24.0))

        rockets = np.flatnonzero(pool.active & self.is_rocket & (pool.age >= self.fuse))
        if len(rockets):
            self.burst(rockets)

        sparks = pool.active & ~self.is_rocket
        y = pool.bodies.position[:, 1]
        pool.park(sparks & ((pool.age > self.life) | (y < -1.0)))

        # dim the sparks in steps (only those whose step changed get a new color)
        sparks = pool.active & ~self.is_rocket
        fade = np.searchsorted(FADE_STEPS, pool.age / self.life)
        changed = np.flatnonzero(sparks & (fade != self.fade))
        if len(changed):
            self.fade[changed] = fade[changed]
            self.recolor(changed, hsv_colors(self.hue[changed], 0.7, FADE_VALUES[fade[changed]]))

        if self.drag > 0.0 and sparks.any():
            flying = pool.bodies[sparks]
            flying.apply_force_to_center(-self.drag * flying.mass[:, None] * flying.linear_velocity)

    def post_debug_draw(self):
        dd = self.debug_draw
        dd.draw_segment((-self.width - 2, 0.0), (self.width + 2, 0.0), b2d.HexColor.DimGray)
        sparks = int((self.pool.active & ~self.is_rocket).sum())
        rockets = int((self.pool.active & self.is_rocket).sum())
        text = f"{rockets} rockets, {sparks} / {self.pool_size} sparks, {self.bursts} bursts"
        dd.draw_string((-self.width, 29.0), text, b2d.HexColor.White)
