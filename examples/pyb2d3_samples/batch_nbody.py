"""N-body gravity: every body attracts every other body.

The pairwise forces are one (n, n, 2) numpy computation per step (n^2 pairs: 90 000 for
300 bodies), applied with a single batch call. Bodies collide and clump into planets.
Drag the sun around with the mouse.
"""

import math
import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import hsv_colors


@register_sample("Batch API", "N-Body Gravity", video=True)
class BatchNBody(SampleBase):
    """A protoplanetary disc: n^2 gravitational forces per step with numpy.

    Mouse: drag the sun (or any planet) around.
    Hint: a higher G clumps the disc into planets faster; the text shows the force time.
    """

    sun_mass = 4000.0
    sun_radius = 2.0
    softening = 0.5
    disc = (6.0, 40.0)  # inner / outer radius

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 300
        self.gravity = 1.0  # the gravitational constant
        self.rng = np.random.default_rng(7)
        self.force_ms = 0.0  # time of the force computation, smoothed
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
        self.bodies.destroy()
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
            b2d.shape_def(
                density=sun_density, material=b2d.surface_material(custom_color=b2d.HexColor.Gold)
            ),
            b2d.circle(radius=self.sun_radius),
        )
        self.bodies = b2d.Bodies([sun])
        for (x, y), radius, color in zip(positions, radii, colors):
            body = self.world.create_dynamic_body(position=(x, y))
            material = b2d.surface_material(friction=0.6, restitution=0.1, custom_color=int(color))
            body.create_shape(b2d.shape_def(material=material), b2d.circle(radius=radius))
            self.bodies.append(body)

        # circular orbits: v = sqrt(G * M_inside / r), perpendicular to the radius
        planet_masses = self.bodies.mass[1:]
        m_inside = self.sun_mass + np.array([planet_masses[r < ri].sum() for ri in r])
        speed = np.sqrt(self.gravity * m_inside / r)
        velocities = np.zeros((n + 1, 2))
        velocities[1:] = speed[:, None] * np.stack([-np.sin(phi), np.cos(phi)], axis=1)
        self.bodies.linear_velocity = velocities

    def pre_update(self, dt):
        """n^2 gravity: all pair forces with numpy, applied in one batch call"""
        t0 = time.perf_counter()
        positions = self.bodies.position  # (n, 2)
        masses = self.bodies.mass  # (n,)
        # F_i = G m_i sum_j m_j (p_j - p_i) / |p_j - p_i|^3, softened: no huge forces
        # when two bodies come close
        delta = positions[None, :, :] - positions[:, None, :]  # (n, n, 2): from i to j
        d2 = np.sum(delta**2, axis=2) + self.softening**2  # (n, n)
        weight = masses[None, :] / d2**1.5  # (n, n): m_j / |p_j - p_i|^3
        np.fill_diagonal(weight, 0.0)  # no force of a body on itself
        forces = self.gravity * masses[:, None] * np.sum(weight[:, :, None] * delta, axis=1)
        self.bodies.apply_force_to_center(forces)
        self.force_ms = 0.9 * self.force_ms + 0.1 * 1000.0 * (time.perf_counter() - t0)

    def post_debug_draw(self):
        """the center of mass (red) and the force time"""
        dd = self.debug_draw
        positions, masses = self.bodies.position, self.bodies.mass
        center = tuple((positions * masses[:, None]).sum(axis=0) / masses.sum())
        dd.draw_point(center, 6.0, b2d.HexColor.Red)
        n = len(self.bodies)
        text = f"{n} bodies, {n * (n - 1)} pair forces: {self.force_ms:.2f} ms"
        dd.draw_string((0.0, self.disc[1] + 1.0), text, b2d.HexColor.White)
