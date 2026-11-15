"""Coulomb crystals: charged particles in a trap order themselves into lattices."""

import math
import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import Ema, create_circles, destroy_bodies

POSITIVE = 0xFF6B5A
NEGATIVE = 0x4FA3FF


class BatchCoulomb(SampleBase):
    """Charged particles in a harmonic trap: all n^2 Coulomb forces with numpy,
    damping cools them until they freeze into a crystal.

    Keys: space flips the sign of the probe charge, m switches all-positive / mixed charges.
    Mouse: hold to put the probe charge there (it pushes / pulls the particles).
    Sliders: charge strength, damping, trap.
    Hint: equal charges form a Wigner crystal (rings, hexagons); mixed charges
    clump into ionic grains. "spacing spread" drops when the lattice orders.
    """

    radius = 0.25
    softening = 0.4
    probe_charge = 12.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 300
        # cloud radius ~ (k n / (trap m))^(1/3): these keep 300 charges at ~11 m
        self.strength = 1.0  # Coulomb constant k
        self.damping = 0.6
        self.trap = 2.0
        self.mixed = False
        self.probe = None  # world position while the mouse is held
        self.probe_sign = 1.0
        self.rng = np.random.default_rng(5)
        self.force_time = Ema()
        self.spread = Ema(0.05)
        self.bodies = b2d.Bodies()
        self.create_particles()
        for widget in (
            widgets.IntSlider("particles", 50, 600, 50, self.count, self.set_count),
            widgets.FloatSlider("charge strength", 0.1, 4.0, 0.1, self.strength, self.set_strength),
            widgets.FloatSlider("damping", 0.0, 3.0, 0.05, self.damping, self.set_damping),
            widgets.FloatSlider("trap", 0.5, 8.0, 0.25, self.trap, self.set_trap),
            widgets.Checkbox("mixed charges (m)", self.mixed, self.set_mixed),
            widgets.Button("reset", self.create_particles),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-16.0, -16.0), upper_bound=(16.0, 17.0))

    # ---- setup ------------------------------------------------------------------------------

    def create_particles(self):
        """a hot gas of charges in a disc"""
        destroy_bodies(self, self.bodies)
        n = self.count
        r = 12.0 * np.sqrt(self.rng.uniform(0.0, 1.0, n))
        phi = self.rng.uniform(0.0, 2.0 * math.pi, n)
        positions = np.stack([r * np.cos(phi), r * np.sin(phi)], axis=1)
        self.charges = np.where(np.arange(n) % 2 == 0, 1.0, -1.0) if self.mixed else np.ones(n)
        colors = np.where(self.charges > 0, POSITIVE, NEGATIVE)
        self.bodies = create_circles(self.world, positions, self.radius, colors=colors, density=1.0,
                                     friction=0.3, restitution=0.0, enable_sleep=False)
        self.bodies.linear_velocity = self.rng.normal(0.0, 3.0, (n, 2))
        self.bodies.linear_damping = self.damping
        self.spread = Ema(0.05)

    def set_count(self, value):
        self.count = int(value)
        self.create_particles()

    def set_strength(self, value):
        self.strength = value

    def set_damping(self, value):
        self.damping = value
        self.bodies.linear_damping = value

    def set_trap(self, value):
        self.trap = value

    def set_mixed(self, value):
        self.mixed = bool(value)
        self.create_particles()

    # ---- input ------------------------------------------------------------------------------

    def on_key_down(self, event):
        """space: probe sign, m: charge mode"""
        if event.key == "space":
            self.probe_sign = -self.probe_sign
        elif event.key == "m":
            self.set_mixed(not self.mixed)

    def on_mouse_down(self, event):
        """the probe charge appears at the mouse (no dragging of bodies / the camera)"""
        self.probe = event.world_position

    def on_mouse_move(self, event):
        """the probe follows the mouse while held"""
        if self.probe is not None:
            self.probe = event.world_position

    def on_mouse_up(self, event):
        self.probe = None

    def on_mouse_leave(self, event):
        self.probe = None

    # ---- n^2 Coulomb forces -----------------------------------------------------------------

    def pre_update(self, dt):
        """Coulomb (all pairs) + probe + trap: one batch call"""
        t0 = time.perf_counter()
        bodies = self.bodies
        p = bodies.position.astype(np.float64)
        m = bodies.mass.astype(np.float64)
        q = self.charges
        delta = p[:, None, :] - p[None, :, :]  # (n, n, 2): from j to i
        d2 = np.einsum("ijk,ijk->ij", delta, delta)
        np.fill_diagonal(d2, np.inf)
        self.nearest = np.sqrt(d2.min(axis=1))
        inv_d3 = (d2 + self.softening**2) ** -1.5
        # F_i = k q_i sum_j q_j (p_i - p_j) / |p_i - p_j|^3: like charges repel
        forces = self.strength * q[:, None] * np.einsum("ij,ijk->ik", inv_d3 * q[None, :], delta)
        if self.probe is not None:
            to_probe = p - np.array([self.probe[0], self.probe[1]])
            d2p = np.einsum("ij,ij->i", to_probe, to_probe) + self.softening**2
            forces += (self.strength * self.probe_charge * self.probe_sign * q * d2p**-1.5)[:, None] * to_probe
        forces -= self.trap * m[:, None] * p  # harmonic trap towards the center
        bodies.apply_force_to_center(forces)
        self.force_time(1000.0 * (time.perf_counter() - t0))

    def post_update(self, dt):
        """order parameter: relative spread of the nearest-neighbor distances"""
        nn = getattr(self, "nearest", None)
        if nn is not None and len(nn) > 1:
            self.spread(float(nn.std() / nn.mean()))

    # ---- drawing ----------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        if self.probe is not None:
            color = b2d.HexColor.Red if self.probe_sign > 0 else b2d.HexColor.DodgerBlue
            dd.draw_circle((self.probe[0], self.probe[1]), 0.6, color)
        speed = float(np.sqrt(np.mean(np.einsum("ij,ij->i", *(2 * [self.bodies.linear_velocity])))))
        mode = "mixed" if self.mixed else "positive"
        text = (f"{len(self.bodies)} charges ({mode}), rms speed {speed:.2f}, "
                f"spacing spread {self.spread.value or 0.0:.2f}, forces {self.force_time.value or 0.0:.1f} ms")
        dd.draw_string((-15.0, 16.0), text, b2d.HexColor.White)


if __name__ == "__main__":
    BatchCoulomb.run()
