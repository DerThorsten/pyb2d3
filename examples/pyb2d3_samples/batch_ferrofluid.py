"""Ferrofluid: a magnetic liquid that grows spikes along the field of a magnet
(SPH liquid + induced dipole forces between all neighbor pairs, numpy + one
batch call)."""

import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import Ema, destroy_bodies, hsv_colors, pair_sum
from .batch_dam_break import FLUID_GROUP, sph_densities


class BatchFerrofluid(SampleBase):
    """A puddle of ferrofluid over a magnet: the particles become little magnets
    along the field, attract head to tail and repel side by side, so the liquid
    stands up in spikes.

    Mouse: drag the magnet (it follows the pointer while pressed).
    Keys: space switches the magnet on / off.
    Sliders: magnet strength, viscosity of the liquid.
    Hint: below a critical strength (~0.6) the liquid only bulges; above it the
    spikes pop up (field concentration at bumps lifts them further). Move the
    magnet slowly under the floor and the spikes follow it.
    """

    radius = 0.08  # particle radius (drawing + walls)
    smoothing = 0.4  # SPH smoothing length = neighbor radius of all pair forces
    tank = (14.0, 8.0)
    max_accel = 150.0  # m/s^2: cap of the explicit forces (no explosions)
    stiffness = 10.0  # SPH pressure (see the dam break)
    reach = 1.5  # the field is ~uniform within this distance of the magnet
    dipole = 15.0  # dipole-dipole force scale
    pull = 80.0  # magnet pull scale
    lift = 600.0  # field concentration at bumps: lift per meter of bump height
    max_lift = 1.6  # ... at most this multiple of the particle's weight ...
    min_neighbors = 4  # ... and only while it is in the liquid
    spike_height = 0.9  # m above the smoothed surface: no lift higher up (the spikes saturate)
    column = 0.12  # surface columns (m) ...
    smooth_columns = 9  # ... and the width of the surroundings (columns): spike spacing
    magnet_rest = (7.0, -1.0)  # where the magnet starts: under the floor

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.count = 900
        self.strength = 1.0
        self.viscosity = 6.0
        self.magnet_on = True
        self.magnet = np.array(self.magnet_rest)
        self.dragging = False
        self.rng = np.random.default_rng(13)
        self.timing = Ema()
        self.particles = b2d.Bodies()
        self.create_tank()
        self.reset()
        for widget in (
            widgets.FloatSlider("magnet strength", 0.0, 3.0, 0.05, self.strength, self.set_strength),
            widgets.FloatSlider("viscosity", 0.5, 15.0, 0.25, self.viscosity, self.set_viscosity),
            widgets.Checkbox("magnet on (space)", self.magnet_on, self.set_magnet_on),
            widgets.Button("reset", self.reset),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        w, h = self.tank
        return b2d.aabb(lower_bound=(-1.0, -3.5), upper_bound=(w + 1.0, h + 1.0))

    def create_tank(self):
        """floor and side walls"""
        w, h = self.tank
        tank = self.world.create_static_body()
        wall_def = b2d.shape_def(material=b2d.surface_material(friction=0.3, custom_color=b2d.HexColor.SlateGray))
        tank.create_shape(wall_def, b2d.box(w / 2 + 0.3, 0.15, center=(w / 2, -0.15)))
        tank.create_shape(wall_def, b2d.box(0.15, h / 2, center=(-0.15, h / 2)))
        tank.create_shape(wall_def, b2d.box(0.15, h / 2, center=(w + 0.15, h / 2)))

    def reset(self):
        """a fresh puddle in the middle of the tank, magnet back under the floor"""
        destroy_bodies(self, self.particles)
        step = 0.5 * self.smoothing
        columns = 45
        rows = int(np.ceil(self.count / columns))
        gx, gy = np.meshgrid(np.arange(columns), np.arange(rows))
        x0 = 0.5 * self.tank[0] - 0.5 * columns * step
        positions = np.stack([x0 + gx.ravel() * step, 0.1 + gy.ravel() * step], axis=1)[: self.count]
        positions += self.rng.uniform(-0.005, 0.005, positions.shape)
        n = len(positions)
        colors = hsv_colors(np.full(n, 0.7), 0.25, self.rng.uniform(0.15, 0.35, n))  # oily black
        bodies = b2d.Bodies()
        shape_filter = b2d.make_filter(group_index=FLUID_GROUP)
        for (x, y), color in zip(positions, colors):
            body = self.world.create_dynamic_body(position=(float(x), float(y)), enable_sleep=False)
            material = b2d.surface_material(friction=0.0, custom_color=int(color))
            body.create_shape(b2d.shape_def(density=1.0, material=material, filter=shape_filter),
                              b2d.circle(radius=self.radius))
            bodies.append(body)
        self.particles = bodies
        self.mass = float(bodies.mass[0])
        _, density, _ = sph_densities(positions, self.smoothing)
        self.rest_density = float(np.median(density))
        self.magnet = np.array(self.magnet_rest)

    def set_strength(self, value):
        self.strength = value

    def set_viscosity(self, value):
        self.viscosity = value

    def set_magnet_on(self, value):
        self.magnet_on = bool(value)

    # ---- mouse / keys: the pointer moves the magnet ---------------------------------------

    def on_mouse_down(self, event):
        """grab the magnet (no body dragging, no camera drag)"""
        self.dragging = True
        self.magnet = np.array(event.world_position, dtype=np.float64)

    def on_mouse_move(self, event):
        """the magnet follows the pointer while pressed"""
        if self.dragging:
            self.magnet = np.array(event.world_position, dtype=np.float64)

    def on_mouse_up(self, event):
        """let go of the magnet"""
        self.dragging = False

    def on_mouse_leave(self, event):
        """let go of the magnet"""
        self.dragging = False

    def on_key_down(self, event):
        """space: magnet on / off"""
        if event.key == "space":
            self.magnet_on = not self.magnet_on

    # ---- forces ---------------------------------------------------------------------------

    def field(self, positions):
        """induced magnetization per particle: direction towards the magnet,
        size ~ 1 / distance^2 (capped: ~uniform within `reach`)"""
        to_magnet = self.magnet - positions
        distance = np.linalg.norm(to_magnet, axis=1)
        direction = to_magnet / np.maximum(distance, 1e-6)[:, None]
        size = self.strength * np.minimum(1.0, (self.reach / np.maximum(distance, 1e-6)) ** 2)
        return direction, size, distance

    def peak_lift(self, positions, size):
        """lift per particle (away from the magnet): for particles at the surface,
        ~ the height of their surface column above the smoothed surface"""
        width = self.column
        column = np.floor(positions[:, 0] / width).astype(int)
        column -= column.min()
        count = column.max() + 1
        top = np.full(count, -np.inf)
        np.maximum.at(top, column, positions[:, 1])
        filled = np.isfinite(top)
        top = np.where(filled, top, np.interp(np.arange(count), np.flatnonzero(filled), top[filled]))
        kernel = np.ones(self.smooth_columns) / self.smooth_columns
        padded = np.pad(top, self.smooth_columns // 2, mode="edge")
        smooth = np.convolve(padded, kernel, mode="valid")[:count]
        excess = np.maximum(top - smooth, 0.0)
        # the whole bump (the part above the smoothed surface, plus the surface
        # layer) is lifted, up to the saturation height of the spikes
        height = positions[:, 1] - smooth[column]
        in_bump = (height > -2.5 * self.radius) & (height < self.spike_height)
        return np.where(in_bump, self.lift * size * np.minimum(excess[column], self.spike_height), 0.0)

    def pre_update(self, dt):
        """SPH pressure + viscosity + magnet pull + dipole-dipole forces, one batch call"""
        t0 = time.perf_counter()
        positions = self.particles.position.astype(np.float64)
        velocities = self.particles.linear_velocity.astype(np.float64)
        n = len(positions)
        (i, j, delta, distance, q), density, near = sph_densities(positions, self.smoothing)
        rhat = delta / np.maximum(distance, 1e-9)[:, None]  # from i to j
        # the liquid (as in the dam break): pressure apart, viscosity together
        pressure = self.stiffness * (density - self.rest_density)
        push = (pressure[i] + pressure[j]) * q + self.stiffness * (near[i] + near[j]) * q**2
        accel = -push[:, None] * rhat + self.viscosity * q[:, None] * (velocities[j] - velocities[i])
        single = np.zeros((n, 2))
        if self.magnet_on and self.strength > 0.0:
            direction, size, to_magnet = self.field(positions)
            # dipoles m = size * direction; force on j from i (identical, parallel
            # dipoles): ~ mi mj (2 c b + (1 - 5 c^2) rhat), c = b . rhat: attract
            # head to tail, repel side by side. The angular part of the point dipole
            # law, but with the smooth SPH falloff q instead of 1 / r^4 (that one
            # is too stiff for explicit 60 Hz forces: the liquid boils)
            b = direction[i] + direction[j]
            b /= np.maximum(np.linalg.norm(b, axis=1), 1e-9)[:, None]
            c = np.einsum("ij,ij->i", b, rhat)
            k = self.dipole * size[i] * size[j] * q
            on_j = k[:, None] * (2.0 * c[:, None] * b + (1.0 - 5.0 * c * c)[:, None] * rhat)
            accel -= on_j  # pair_sum: + on i, - on j
            # the magnet pulls every particle, ~ 1 / distance^2 (a deep potential:
            # the surface, g h + U = const, rises towards the magnet)
            pull = self.pull * self.strength / np.maximum(to_magnet, 0.7) ** 2
            single = pull[:, None] * direction
            # field concentration: the liquid draws the field lines into itself, so
            # the field is strongest at the tips of bumps and lifts them further
            # (the feedback that makes the spikes): surface particles get a lift
            # ~ how far their surface column sticks out of its surroundings
            # capped at a multiple of the particle's weight (gravity + pull), and only
            # for particles still in the liquid (enough neighbors): a particle that
            # breaks off loses its lift and falls back, none is thrown away
            neighbors = np.bincount(i, minlength=n) + np.bincount(j, minlength=n)
            lift = np.minimum(self.peak_lift(positions, size), self.max_lift * (10.0 + pull))
            lift[neighbors < self.min_neighbors] = 0.0
            single -= lift[:, None] * direction
        total = pair_sum(n, i, j, accel) + single
        magnitude = np.linalg.norm(total, axis=1)
        total *= np.minimum(1.0, self.max_accel / np.maximum(magnitude, 1e-9))[:, None]
        self.particles.apply_force_to_center(total * self.mass)
        self.timing(1000.0 * (time.perf_counter() - t0))

    # ---- drawing ----------------------------------------------------------------------------

    def surface(self):
        """the height of the liquid surface in 0.25 m wide columns (empty: nan)"""
        positions = self.particles.position
        edges = np.arange(0.0, self.tank[0] + 0.25, 0.25)
        column = np.clip(np.digitize(positions[:, 0], edges) - 1, 0, len(edges) - 2)
        top = np.full(len(edges) - 1, -np.inf)
        np.maximum.at(top, column, positions[:, 1])
        return np.where(np.isfinite(top), top, np.nan)

    def spikes(self):
        """number of spikes (runs of surface columns > 0.5 m above the surface
        smoothed over 2 m) and the highest point"""
        top = self.surface()
        filled = ~np.isnan(top)
        top = np.interp(np.arange(len(top)), np.flatnonzero(filled), top[filled])
        window = 9
        smooth = np.convolve(np.pad(top, window // 2, mode="edge"), np.ones(window) / window, mode="valid")
        high = (top - smooth) > 0.5
        starts = high & ~np.concatenate([[False], high[:-1]])
        return int(np.count_nonzero(starts)), float(top.max())

    def post_debug_draw(self):
        dd = self.debug_draw
        on = self.magnet_on and self.strength > 0
        m = self.magnet
        color = b2d.HexColor.Red if on else b2d.HexColor.Gray
        dd.draw_segment((m[0] - 0.5, m[1]), (m[0] + 0.5, m[1]), color)  # the magnet
        dd.draw_point(tuple(m), 12.0, color)
        count, highest = self.spikes()
        text = (f"magnet {'on' if self.magnet_on else 'off'} ({self.strength:.2f})   "
                f"{count} spikes, highest {highest:.2f} m   forces {self.timing.value or 0:.1f} ms")
        dd.draw_string((0.0, self.tank[1] + 0.5), text, b2d.HexColor.White)
