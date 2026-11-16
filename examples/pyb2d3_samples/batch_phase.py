"""Phase transitions: Lennard-Jones particles with a thermostat turn from gas into
droplets into a crystal when cooled (numpy pair forces over all particles)."""

import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .batch_common import Ema, destroy_bodies, draw_plot, hsv_colors, neighbor_pairs, pair_sum


@register_sample("Fluids & Matter", "Phase Transitions")
class BatchPhaseTransitions(SampleBase):
    """Lennard-Jones particles in a box with a thermostat: hot = gas, warm =
    droplets that merge, cold = hexagonal crystals.

    Every step: one neighbor search (cutoff 2.5 sigma), the LJ force of every pair
    and the thermostat force, one batch call; box2d's contacts are the hard core.
    Sliders: temperature (in units of the well depth), thermostat strength, gravity.
    Hint: above ~0.3 it is a gas; set 0.15 and droplets nucleate and merge, at
    0.03 they freeze into hexagonal patches (colors: number of close neighbors).
    The plot: measured temperature (orange) and target (white); condensing
    releases heat, the thermostat takes it away.
    """

    count = 450  # dilute: the gas fills the box, the liquid makes droplets
    sigma = 0.5  # LJ size
    r_min = 2.0 ** (1.0 / 6.0) * sigma  # the LJ minimum = the particle diameter
    epsilon = 0.1  # LJ well depth (the attractive tail is soft enough for 60 Hz)
    box = (26.0, 20.0)

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        # elastic contacts also at thermal speeds (box2d makes slow impacts fully
        # inelastic by default: the particles would stick at any temperature)
        self.world.restitution_threshold = 0.0
        self.target = 1.0
        self.tau = 0.5  # thermostat time constant (s)
        self.gravity = 0.0
        self.rng = np.random.default_rng(9)
        self.timing = Ema()
        self.temperature = 0.0
        self.history = []
        self.particles = b2d.Bodies()
        self.create_box()
        self.reset()
        for widget in (
            widgets.FloatSlider("temperature", 0.01, 2.0, 0.01, self.target, self.set_target),
            widgets.FloatSlider("thermostat (1/s)", 0.1, 5.0, 0.1, 1.0 / self.tau, self.set_rate),
            widgets.FloatSlider("gravity", 0.0, 2.0, 0.05, self.gravity, self.set_gravity),
            widgets.Button("reset", self.reset),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        w, h = self.box
        return b2d.aabb(lower_bound=(-1.0, -1.0), upper_bound=(w + 6.0, h + 1.5))

    def create_box(self):
        """the walls"""
        w, h = self.box
        walls = self.world.create_static_body()
        wall_def = b2d.shape_def(
            material=b2d.surface_material(
                friction=0.0, restitution=1.0, custom_color=b2d.HexColor.SlateGray
            )
        )
        corners = [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)]
        for p, q in zip(corners, corners[1:] + corners[:1]):
            walls.create_shape(wall_def, b2d.segment(p, q))

    def reset(self):
        """particles on a loose grid with random thermal velocities"""
        destroy_bodies(self, self.particles)
        w, h = self.box
        step = 1.6 * self.sigma
        gx, gy = np.meshgrid(np.arange(step, w - step, step), np.arange(step, h - step, step))
        grid = np.stack([gx.ravel(), gy.ravel()], axis=1)
        positions = grid[self.rng.permutation(len(grid))[: self.count]]
        bodies = b2d.Bodies()
        # the particles collide as circles of diameter r_min: box2d's contacts
        # are the hard core (the LJ core is far too stiff for an explicit step)
        shape_def = b2d.shape_def(
            density=1.0, material=b2d.surface_material(friction=0.0, restitution=1.0)
        )
        for x, y in positions:
            body = self.world.create_dynamic_body(position=(float(x), float(y)), enable_sleep=False)
            body.create_shape(shape_def, b2d.circle(radius=0.5 * self.r_min))
            bodies.append(body)
        self.particles = bodies
        self.shapes = [body.shapes[0] for body in bodies]
        self.mass = float(bodies.mass[0])
        speed = np.sqrt(self.target * self.epsilon / self.mass)
        bodies.linear_velocity = self.rng.normal(0.0, speed, (len(bodies), 2))
        self.band = np.full(len(bodies), -1)
        self.history = []

    def set_target(self, value):
        self.target = value

    def set_rate(self, value):
        self.tau = 1.0 / value

    def set_gravity(self, value):
        self.gravity = value

    # ---- forces -----------------------------------------------------------------------------

    def pre_update(self, dt):
        """LJ pair forces + Berendsen thermostat + gravity, one batch call"""
        t0 = time.perf_counter()
        positions = self.particles.position.astype(np.float64)
        velocities = self.particles.linear_velocity.astype(np.float64)
        n = len(positions)
        i, j, delta, distance = neighbor_pairs(positions, 2.5 * self.sigma)
        # F(r) = 24 eps / r (2 (s/r)^12 - (s/r)^6), only its attractive tail from
        # the minimum r_min on (the force is 0 there, so no jump); closer, the
        # circles touch and box2d's contact is the (implicit, stable) repulsion
        r = np.maximum(distance, self.r_min)
        s6 = (self.sigma / r) ** 6
        magnitude = 24.0 * self.epsilon / r * (2.0 * s6 * s6 - s6)  # positive: apart
        force = -(magnitude / np.maximum(distance, 1e-9))[:, None] * delta  # on i
        total = pair_sum(n, i, j, force)
        # thermostat: scale the velocities towards the target temperature
        # (kinetic energy per particle = T in units of epsilon, 2D: m v^2 / 2 = k T)
        kinetic = 0.5 * self.mass * np.einsum("ij,ij->i", velocities, velocities)
        self.temperature = float(kinetic.mean()) / self.epsilon
        scale = np.sqrt(1.0 + dt / self.tau * (self.target / max(self.temperature, 1e-6) - 1.0))
        total += self.mass * (scale - 1.0) / dt * velocities
        total[:, 1] -= self.mass * self.gravity
        self.particles.apply_force_to_center(total)
        self.neighbors = 2.0 * len(i) / n
        self.timing(1000.0 * (time.perf_counter() - t0))

    def post_update(self, dt):
        """color by the number of close neighbors (gas: few, crystal: six)"""
        self.history.append((self.temperature, self.target))
        del self.history[:-600]
        positions = self.particles.position
        i, j, _, _ = neighbor_pairs(positions, 1.35 * self.sigma)
        bonds = np.bincount(i, minlength=len(positions)) + np.bincount(j, minlength=len(positions))
        band = np.minimum(bonds, 6)
        changed = np.flatnonzero(band != self.band)
        for k in changed:
            material = self.shapes[k].surface_material
            material.custom_color = BOND_COLORS[band[k]]
            self.shapes[k].surface_material = material
        self.band = band
        self.bonds = bonds

    def phase(self):
        """a guess of the state: the share of condensed particles (>= 3 close
        neighbors) and of crystal-like ones (6 close neighbors)"""
        bonds = getattr(self, "bonds", np.zeros(1))
        condensed = float(np.mean(bonds >= 3))
        crystal = float(np.mean(bonds >= 6))
        if condensed < 0.3:
            state = "gas"
        elif crystal > 0.4:
            state = "solid"
        else:
            state = "liquid droplets"
        return state, condensed, crystal

    def post_debug_draw(self):
        w, h = self.box
        state, condensed, crystal = self.phase()
        text = (
            f"T {self.temperature:.2f} (target {self.target:.2f})   {state}: condensed {100 * condensed:.0f} %, "
            f"crystal {100 * crystal:.0f} %   forces {self.timing.value or 0:.1f} ms"
        )
        self.debug_draw.draw_string((0.0, h + 0.8), text, b2d.HexColor.White)
        if len(self.history) > 1:
            series = np.array(self.history)
            draw_plot(
                self.debug_draw,
                (w + 0.8, 0.0),
                (4.5, h),
                [series[:, 0], series[:, 1]],
                [b2d.HexColor.Orange, b2d.HexColor.White],
                y_max=2.0,
            )


# close neighbors 0..6 -> colors (gas: blue ... crystal: white-ish yellow)
BOND_COLORS = [
    int(c) for c in hsv_colors(np.linspace(0.62, 0.12, 7), np.linspace(0.8, 0.35, 7), 1.0)
]
