"""N-body gravity: every body attracts every other body.

The pairwise forces are one (n, n, 2) numpy computation per step (n^2 pairs: 90 000 for
300 bodies), applied with a single batch call. Bodies collide and clump into planets.
Drag the sun around with the mouse.
"""

import math
import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import Ema, create_circles, destroy_bodies, hsv_colors


class BatchNBody(SampleBase):
    """A protoplanetary disc: n^2 gravitational forces per step with numpy."""

    sun_mass = 4000.0
    sun_radius = 2.0
    softening = 0.5
    disc = (6.0, 40.0)  # inner / outer radius

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 300
        self.gravity = 1.0  # the gravitational constant
        self.rng = np.random.default_rng(7)
        self.force_time = Ema()
        self.bodies = b2d.Bodies()
        self.create_disc()

        for widget in (
            widgets.IntSlider("bodies", 50, 1000, 50, self.count, self.set_count),
            widgets.FloatSlider("G", 0.1, 3.0, 0.1, self.gravity, self.set_gravity),
            widgets.Button("reset", self.create_disc),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        r = self.disc[1] + 2.0
        return b2d.aabb(lower_bound=(-r, -r), upper_bound=(r, r))

    def set_count(self, value):
        self.count = int(value)
        self.create_disc()

    def set_gravity(self, value):
        self.gravity = value

    def create_disc(self):
        destroy_bodies(self, self.bodies)
        n = self.count - 1  # plus the sun
        # planetesimals in a disc, area-uniform, with mixed sizes
        r = np.sqrt(self.rng.uniform(self.disc[0] ** 2, self.disc[1] ** 2, n))
        phi = self.rng.uniform(0.0, 2.0 * math.pi, n)
        positions = np.stack([r * np.cos(phi), r * np.sin(phi)], axis=1)
        radii = self.rng.uniform(0.15, 0.6, n)
        colors = hsv_colors(0.55 + 0.4 * (radii - 0.15) / 0.45, saturation=0.6)

        sun = self.world.create_dynamic_body(position=(0, 0))
        sun_density = self.sun_mass / (math.pi * self.sun_radius**2)
        sun.create_shape(
            b2d.shape_def(density=sun_density, material=b2d.surface_material(custom_color=b2d.HexColor.Gold)),
            b2d.circle(radius=self.sun_radius),
        )
        planets = create_circles(self.world, positions, radii, colors=colors, density=1.0, restitution=0.1, friction=0.6)
        self.bodies = b2d.Bodies([sun, *planets])

        # circular orbits: v = sqrt(G * M_inside / r), perpendicular to the radius
        masses = self.bodies.mass
        order = np.argsort(r)
        inside = self.sun_mass + np.cumsum(masses[1:][order]) - masses[1:][order]
        m_inside = np.empty(n)
        m_inside[order] = inside
        speed = np.sqrt(self.gravity * m_inside / r)
        velocities = np.zeros((n + 1, 2))
        velocities[1:] = speed[:, None] * np.stack([-np.sin(phi), np.cos(phi)], axis=1)
        self.bodies.linear_velocity = velocities

    # ---- n^2 gravity ----------------------------------------------------------------------

    def pre_update(self, dt):
        t0 = time.perf_counter()
        bodies = self.bodies
        positions = bodies.position.astype(np.float64)  # (n, 2)
        masses = bodies.mass.astype(np.float64)  # (n,)

        delta = positions[None, :, :] - positions[:, None, :]  # (n, n, 2): from i to j
        d2 = np.einsum("ijk,ijk->ij", delta, delta) + self.softening**2
        inv_d3 = d2**-1.5
        np.fill_diagonal(inv_d3, 0.0)
        # F_i = G m_i sum_j m_j (p_j - p_i) / |p_j - p_i|^3
        forces = self.gravity * masses[:, None] * np.einsum("ij,ijk->ik", inv_d3 * masses[None, :], delta)
        bodies.apply_force_to_center(forces)
        self.force_time(1000.0 * (time.perf_counter() - t0))

    # ---- drawing --------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        positions, masses = self.bodies.position, self.bodies.mass
        center = tuple((positions * masses[:, None]).sum(axis=0) / masses.sum())
        dd.draw_point(center, 6.0, b2d.HexColor.Red)
        n = len(self.bodies)
        text = f"{n} bodies, {n * (n - 1)} pair forces: {self.force_time.value or 0.0:.2f} ms"
        dd.draw_string((0.0, self.disc[1] + 1.0), text, b2d.HexColor.White)


if __name__ == "__main__":
    BatchNBody.run()
