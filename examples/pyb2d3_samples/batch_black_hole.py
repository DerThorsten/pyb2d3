"""A black hole with an accretion disc: particles spiral in and are swallowed."""

import math
import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import Ema, destroy_bodies, hsv_colors
from .batch_common import create_points  # non-colliding circles


class BatchBlackHole(SampleBase):
    """An accretion disc around a black hole: gravity + viscosity with numpy, one
    batch call; swallowed particles are recycled to the outer edge with masks.

    Mouse: hold to move the black hole (the disc follows, or gets torn apart).
    Sliders: hole mass, viscosity (how fast the disc drains), particles.
    Hint: viscosity lets the gas lose angular momentum and spiral in (inner orbits
    are faster: watch the spiral wind up); at 0 the disc almost just orbits. The
    text shows the accretion rate.
    """

    # the force is computed once per step: held constant over several substeps it pumps
    # energy into the fast inner orbits (they drift outwards and pile up in a ring).
    # The gas has no contacts, so one substep (plain symplectic Euler) is enough
    substeps = 1
    softening = 0.5
    horizon = 1.5  # event horizon radius
    disc = (3.0, 16.0)  # inner / outer radius of the initial disc
    feed = (13.0, 17.0)  # recycled particles re-enter here
    particle_radius = 0.16
    coupling = 5.0  # 1/s: how fast the gas follows the viscous flow

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 700
        self.mass = 600.0  # G M (G = 1)
        # inward drift as a fraction of the orbital speed: ~20 s from the outer edge to the horizon
        self.viscosity = 0.06
        self.hole = np.zeros(2)
        self.dragging = False
        self.rng = np.random.default_rng(11)
        self.force_time = Ema()
        self.rate = Ema(0.02)
        self.swallowed = 0
        self.bodies = b2d.Bodies()
        self.create_disc()
        for widget in (
            widgets.FloatSlider("hole mass", 100.0, 1500.0, 50.0, self.mass, self.set_mass),
            widgets.FloatSlider("viscosity", 0.0, 0.3, 0.01, self.viscosity, self.set_viscosity),
            widgets.IntSlider("particles", 100, 1500, 100, self.count, self.set_count),
            widgets.Button("reset", self.create_disc),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        r = self.feed[1] + 1.0
        return b2d.aabb(lower_bound=(-r, -r), upper_bound=(r, r + 1.0))

    def set_mass(self, value):
        self.mass = value

    def set_viscosity(self, value):
        self.viscosity = value

    def set_count(self, value):
        self.count = int(value)
        self.create_disc()

    # ---- setup ------------------------------------------------------------------------------

    def orbit(self, r, phi):
        """positions + circular orbit velocities around the hole (softened gravity)"""
        radial = np.stack([np.cos(phi), np.sin(phi)], axis=1)
        tangent = np.stack([-np.sin(phi), np.cos(phi)], axis=1)
        speed = np.sqrt(self.mass * r**2 / (r**2 + self.softening**2) ** 1.5)
        return self.hole + r[:, None] * radial, speed[:, None] * tangent

    def create_disc(self):
        """a rotating disc of gas around the hole"""
        destroy_bodies(self, self.bodies)
        self.hole = np.zeros(2)
        n = self.count
        r = np.sqrt(self.rng.uniform(self.disc[0] ** 2, self.disc[1] ** 2, n))
        phi = self.rng.uniform(0.0, 2.0 * math.pi, n)
        positions, velocities = self.orbit(r, phi)
        colors = hsv_colors(0.02 + 0.12 * self.rng.random(n), 0.85, 1.0)
        # gas without collisions: colliding particles at orbital speeds jam into a ring
        # and blow it apart; the viscosity below stands in for the gas friction
        self.bodies = create_points(self.world, positions, self.particle_radius, colors, 1.0)
        self.bodies.linear_velocity = velocities
        self.swallowed = 0
        self.rate = Ema(0.02)

    # ---- input ------------------------------------------------------------------------------

    def on_mouse_down(self, event):
        """grab the hole (no dragging of particles / the camera)"""
        self.dragging = True
        self.hole = np.array([event.world_position[0], event.world_position[1]])

    def on_mouse_move(self, event):
        if self.dragging:
            self.hole = np.array([event.world_position[0], event.world_position[1]])

    def on_mouse_up(self, event):
        self.dragging = False

    def on_mouse_leave(self, event):
        self.dragging = False

    # ---- gravity, viscosity, swallowing -----------------------------------------------------

    def pre_update(self, dt):
        """swallow (recycle) the particles inside the horizon, then gravity + viscosity"""
        t0 = time.perf_counter()
        bodies = self.bodies
        p = bodies.position.astype(np.float64)
        to_hole = self.hole - p
        d2 = np.einsum("ij,ij->i", to_hole, to_hole)

        inside = d2 < self.horizon**2
        k = int(inside.sum())
        if k:
            # recycle: back to the outer disc on circular orbits (one masked batch)
            r = self.rng.uniform(*self.feed, k)
            phi = self.rng.uniform(0.0, 2.0 * math.pi, k)
            positions, velocities = self.orbit(r, phi)
            batch = bodies[inside]
            batch.set_transform(positions, (1.0, 0.0))
            batch.linear_velocity = velocities
            p[inside] = positions
            to_hole[inside] = self.hole - positions
            d2[inside] = r**2
            self.swallowed += k
        self.rate(k / dt)

        m = bodies.mass.astype(np.float64)
        forces = (self.mass * m * (d2 + self.softening**2) ** -1.5)[:, None] * to_hole
        # gas viscosity: relax the velocity towards a near-circular orbit with a small
        # inward drift (viscosity = drift / orbital speed). Keeps the orbits circular:
        # plain drag makes them eccentric, plunging particles skip the horizon between
        # two steps and get flung out by the (softened) pull at the center
        r = np.sqrt(d2)
        inward = to_hole / r[:, None]
        counterclockwise = np.stack([inward[:, 1], -inward[:, 0]], axis=1)
        v_circular = np.sqrt(self.mass * d2 / (d2 + self.softening**2) ** 1.5)
        target = v_circular[:, None] * (counterclockwise + self.viscosity * inward)
        v = bodies.linear_velocity.astype(np.float64)
        forces += self.coupling * m[:, None] * (target - v)
        bodies.apply_force_to_center(forces)
        self.force_time(1000.0 * (time.perf_counter() - t0))

    # ---- drawing ----------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        hole = (float(self.hole[0]), float(self.hole[1]))
        dd.draw_circle(hole, self.horizon, b2d.HexColor.White)
        dd.draw_circle(hole, 0.5 * self.horizon, b2d.HexColor.DimGray)
        text = (f"{len(self.bodies)} particles, swallowed {self.swallowed} "
                f"({self.rate.value or 0.0:.0f}/s), forces {self.force_time.value or 0.0:.2f} ms")
        dd.draw_string((-self.feed[1], self.feed[1] + 1.4), text, b2d.HexColor.White)


if __name__ == "__main__":
    BatchBlackHole.run()
