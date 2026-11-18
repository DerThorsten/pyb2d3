"""Ferrofluid: a magnetic liquid that grows spikes along the field of a magnet
(SPH liquid + induced dipole forces between all neighbor pairs, numpy + one
batch call)."""

import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .batch_dam_break import FLUID_GROUP, sph_densities
from .examples_common.batch import hsv_colors, pair_sum

RADIUS = 0.08  # particle radius (drawing + walls)
SMOOTHING = 0.4  # SPH smoothing length = neighbor radius of all pair forces
TANK = (14.0, 8.0)
MAX_ACCEL = 150.0  # m/s^2: cap of the explicit forces (no explosions)
STIFFNESS = 10.0  # SPH pressure (see the dam break)
REACH = 1.5  # the field is ~uniform within this distance of the magnet
DIPOLE = 15.0  # dipole-dipole force scale
PULL = 80.0  # magnet pull scale
LIFT = 600.0  # field concentration at bumps: lift per meter of bump height
MAX_LIFT = 1.6  # ... at most this multiple of the particle's weight ...
MIN_NEIGHBORS = 4  # ... and only while it is in the liquid
SPIKE_HEIGHT = 0.9  # m above the smoothed surface: no lift higher up (the spikes saturate)
LIFT_COLUMN = 0.12  # surface columns (m) for the lift ...
LIFT_WINDOW = 9  # ... and the width of their surroundings (columns): the spike spacing
MAGNET_REST = (7.0, -1.0)  # where the magnet starts: under the floor


def column_tops(positions, width):
    """the liquid surface: the highest particle in each `width` wide column of the
    tank (empty columns interpolated), and the column of every particle"""
    count = int(TANK[0] / width) + 1
    column = np.clip(np.floor(positions[:, 0] / width).astype(int), 0, count - 1)
    top = np.full(count, -np.inf)
    np.maximum.at(top, column, positions[:, 1])
    filled = np.isfinite(top)
    top = np.interp(np.arange(count), np.flatnonzero(filled), top[filled])
    return top, column


def smoothed(values, window):
    """moving average over `window` (odd) values"""
    padded = np.pad(values, window // 2, mode="edge")
    return np.convolve(padded, np.ones(window) / window, mode="valid")


@register_sample("Fluids & Matter", "Ferrofluid", video=True)
class BatchFerrofluid(SampleBase):
    """Ferrofluid over a magnet: the particles align with the field and, above a
    critical strength (~0.6), the liquid stands up in spikes.
    Mouse: drag the magnet.
    Keys: space: magnet on / off.
    Sliders: strength, viscosity.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.count = 900
        self.strength = 1.0
        self.viscosity = 6.0
        self.magnet_on = True
        self.rng = np.random.default_rng(13)
        self.force_ms = 0.0  # time of the force computation, smoothed
        self.particles = b2d.Bodies()
        self.create_tank()
        self.reset()
        for widget in (
            widgets.FloatSlider(
                "magnet strength", 0.0, 3.0, 0.05, self.strength, self.set_strength
            ),
            widgets.FloatSlider("viscosity", 0.5, 15.0, 0.25, self.viscosity, self.set_viscosity),
            widgets.Checkbox("magnet on (space)", self.magnet_on, self.set_magnet_on),
            widgets.Button("reset", self.reset),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        w, h = TANK
        return b2d.aabb(lower_bound=(-1.0, -3.5), upper_bound=(w + 1.0, h + 1.0))

    def create_tank(self):
        """floor and side walls"""
        w, h = TANK
        tank = self.world.create_static_body()
        wall_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.3, custom_color=b2d.HexColor.SlateGray)
        )
        tank.create_shape(wall_def, b2d.box(w / 2 + 0.3, 0.15, center=(w / 2, -0.15)))
        tank.create_shape(wall_def, b2d.box(0.15, h / 2, center=(-0.15, h / 2)))
        tank.create_shape(wall_def, b2d.box(0.15, h / 2, center=(w + 0.15, h / 2)))

    def reset(self):
        """a fresh puddle in the middle of the tank, magnet back under the floor"""
        self.particles.destroy()
        step = 0.5 * SMOOTHING
        columns = 45
        rows = int(np.ceil(self.count / columns))
        gx, gy = np.meshgrid(np.arange(columns), np.arange(rows))
        x0 = 0.5 * TANK[0] - 0.5 * columns * step
        positions = np.stack([x0 + gx.ravel() * step, 0.1 + gy.ravel() * step], axis=1)
        positions = positions[: self.count] + self.rng.uniform(-0.005, 0.005, (self.count, 2))
        brightness = self.rng.uniform(0.15, 0.35, self.count)
        colors = hsv_colors(np.full(self.count, 0.7), 0.25, brightness)  # oily black
        fluid_filter = b2d.make_filter(group_index=FLUID_GROUP)
        material = b2d.surface_material(friction=0.0)
        self.particles, shapes = self.world.create_bodies(
            positions,
            b2d.shape_def(material=material, filter=fluid_filter),
            b2d.circle(radius=RADIUS),
            enable_sleep=False,
        )
        shapes.custom_color = colors
        self.mass = self.particles.mass[0]
        _, density, _ = sph_densities(positions, SMOOTHING)
        self.rest_density = np.median(density)
        self.magnet = np.array(MAGNET_REST)

    def set_strength(self, value):
        self.strength = value

    def set_viscosity(self, value):
        self.viscosity = value

    def set_magnet_on(self, value):
        self.magnet_on = bool(value)

    def on_mouse_down(self, event):
        # no super(): the button grabs the magnet instead of dragging bodies / the camera
        self.is_mouse_down = True
        self.mouse_pos = event.world_position

    def on_key_down(self, event):
        if event.key == "space":
            self.magnet_on = not self.magnet_on

    def field(self, positions):
        """induced magnetization per particle: direction towards the magnet,
        size ~ 1 / distance^2 (capped: ~uniform within REACH)"""
        to_magnet = self.magnet - positions
        distance = np.maximum(np.linalg.norm(to_magnet, axis=1), 1e-6)
        direction = to_magnet / distance[:, None]
        size = self.strength * np.minimum(1.0, (REACH / distance) ** 2)
        return direction, size, distance

    def bump_lift(self, positions, size):
        """lift per particle (away from the magnet): the particles of a bump in the
        surface get a lift ~ how far their surface column sticks out of its surroundings"""
        top, column = column_tops(positions, LIFT_COLUMN)
        surroundings = smoothed(top, LIFT_WINDOW)
        excess = np.maximum(top - surroundings, 0.0)
        # the whole bump (the part above the smoothed surface, plus the surface
        # layer) is lifted, up to the saturation height of the spikes
        height = positions[:, 1] - surroundings[column]
        in_bump = (height > -2.5 * RADIUS) & (height < SPIKE_HEIGHT)
        return np.where(in_bump, LIFT * size * np.minimum(excess[column], SPIKE_HEIGHT), 0.0)

    def pre_update(self, dt):
        """SPH pressure + viscosity + magnet pull + dipole-dipole forces, one batch call"""
        if self.is_mouse_down:
            self.magnet = np.array(self.mouse_pos)
        t0 = time.perf_counter()
        # (the batch api returns float32: compute the forces in double precision)
        positions = self.particles.position.astype(np.float64)
        velocities = self.particles.linear_velocity.astype(np.float64)
        n = len(positions)
        (i, j, delta, distance, q), density, near = sph_densities(positions, SMOOTHING)
        rhat = delta / np.maximum(distance, 1e-9)[:, None]  # from i to j
        # the liquid (as in the dam break): pressure apart, viscosity together
        pressure = STIFFNESS * (density - self.rest_density)
        push = (pressure[i] + pressure[j]) * q + STIFFNESS * (near[i] + near[j]) * q**2
        accel = -push[:, None] * rhat + self.viscosity * q[:, None] * (
            velocities[j] - velocities[i]
        )
        single = np.zeros((n, 2))  # forces that act on single particles, not on pairs
        if self.magnet_on and self.strength > 0.0:
            direction, size, to_magnet = self.field(positions)
            # dipoles m = size * direction; force on j from i (identical, parallel
            # dipoles): ~ mi mj (2 c b + (1 - 5 c^2) rhat), c = b . rhat: attract
            # head to tail, repel side by side. The angular part of the point dipole
            # law, but with the smooth SPH falloff q instead of 1 / r^4 (that one
            # is too stiff for explicit 60 Hz forces: the liquid boils)
            b = direction[i] + direction[j]
            b /= np.maximum(np.linalg.norm(b, axis=1), 1e-9)[:, None]
            c = np.sum(b * rhat, axis=1)
            k = DIPOLE * size[i] * size[j] * q
            on_j = k[:, None] * (2.0 * c[:, None] * b + (1.0 - 5.0 * c * c)[:, None] * rhat)
            accel -= on_j  # pair_sum: + on i, - on j
            # the magnet pulls every particle, ~ 1 / distance^2 (a deep potential:
            # the surface, g h + U = const, rises towards the magnet)
            pull = PULL * self.strength / np.maximum(to_magnet, 0.7) ** 2
            single = pull[:, None] * direction
            # field concentration: the liquid draws the field lines into itself, so
            # the field is strongest at the tips of bumps and lifts them further (the
            # feedback that makes the spikes). Capped at a multiple of the particle's
            # weight (gravity + pull), and only for particles still in the liquid: a
            # particle that breaks off loses its lift and falls back
            neighbors = np.bincount(i, minlength=n) + np.bincount(j, minlength=n)
            lift = np.minimum(self.bump_lift(positions, size), MAX_LIFT * (10.0 + pull))
            lift[neighbors < MIN_NEIGHBORS] = 0.0
            single -= lift[:, None] * direction
        total = pair_sum(n, i, j, accel) + single
        magnitude = np.linalg.norm(total, axis=1)
        total *= np.minimum(1.0, MAX_ACCEL / np.maximum(magnitude, 1e-9))[:, None]
        self.particles.apply_force_to_center(total * self.mass)
        self.force_ms = 0.9 * self.force_ms + 0.1 * 1000.0 * (time.perf_counter() - t0)

    def spikes(self):
        """number of spikes (runs of 0.25 m surface columns > 0.5 m above the surface
        smoothed over ~2 m) and the highest point"""
        top, _ = column_tops(self.particles.position, 0.25)
        high = top - smoothed(top, 9) > 0.5
        starts = high & ~np.concatenate([[False], high[:-1]])
        return np.count_nonzero(starts), top.max()

    def post_debug_draw(self):
        dd = self.debug_draw
        on = self.magnet_on and self.strength > 0
        x, y = self.magnet
        color = b2d.HexColor.Red if on else b2d.HexColor.Gray
        dd.draw_segment((x - 0.5, y), (x + 0.5, y), color)  # the magnet
        dd.draw_point((x, y), 12.0, color)
        count, highest = self.spikes()
        text = (
            f"magnet {'on' if self.magnet_on else 'off'} ({self.strength:.2f})   "
            f"{count} spikes, highest {highest:.2f} m   forces {self.force_ms:.1f} ms"
        )
        dd.draw_string((0.0, TANK[1] + 0.5), text, b2d.HexColor.White)
