"""Two disc galaxies pass each other: tidal forces pull out long tails and bridges."""

import math
import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import (
    Ema,
    create_points,
    destroy_bodies,
    hsv_colors,
)  # create_points: stars and cores only feel gravity


class BatchGalaxyCollision(SampleBase):
    """Two disc galaxies on a close flyby: the stars feel both
    galaxy cores, the cores feel each other; one batch force call per step.

    Mouse: drag a galaxy by its core (the disc moves along, the tails stay);
    let go while moving to throw it at the other one.
    Sliders: closest approach of the cores, stars per galaxy.
    Hint: discs rotating along the flyby (prograde) throw out long tidal tails and a
    bridge, a retrograde disc loses far fewer stars; the cores stay bound and pass
    again (each pass shreds more, "reset" starts over).
    """

    gravity = 1.0  # G
    core_mass = 1200.0
    softening = 0.6
    disc = (1.5, 7.0)  # inner / outer radius of the star discs
    start_distance = 40.0  # core separation at the start
    # bound: the galaxies come back for more passes (apocenter ~1.9x the closest approach)
    eccentricity = 0.3
    grab_radius = 2.0  # a press this close to a core grabs it
    drag_rate = 8.0  # 1/s: a dragged core closes this share of the gap to the mouse per second
    max_drag_speed = 40.0  # also the fastest throw

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.stars_per_galaxy = 500
        # closest approach of the cores: ~3.4 disc radii pulls ~1/3 of the stars into tails,
        # closer encounters shred the discs
        self.impact = 24.0
        self.retrograde = False
        self.rng = np.random.default_rng(3)
        self.force_time = Ema()
        self.bodies = b2d.Bodies()
        self.dragged = None  # index of the core being dragged
        self.drag_target = np.zeros(2)
        self.reset()
        for widget in (
            widgets.FloatSlider("closest approach", 14.0, 34.0, 0.5, self.impact, self.set_impact),
            widgets.IntSlider(
                "stars per galaxy", 100, 1000, 50, self.stars_per_galaxy, self.set_stars
            ),
            widgets.Checkbox("second disc retrograde", self.retrograde, self.set_retrograde),
            widgets.Button("reset", self.reset),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-36.0, -30.0), upper_bound=(36.0, 31.0))

    def set_impact(self, value):
        self.impact = value
        self.reset()

    def set_stars(self, value):
        self.stars_per_galaxy = int(value)
        self.reset()

    def set_retrograde(self, value):
        self.retrograde = bool(value)
        self.reset()

    # ---- setup ------------------------------------------------------------------------------

    def galaxy_disc(self, center, velocity, spin, hue):
        """star positions / velocities of one disc on circular orbits around its core"""
        n = self.stars_per_galaxy
        r = np.sqrt(self.rng.uniform(self.disc[0] ** 2, self.disc[1] ** 2, n))
        phi = self.rng.uniform(0.0, 2.0 * math.pi, n)
        offset = np.stack([r * np.cos(phi), r * np.sin(phi)], axis=1)
        # circular speed with the softened force: v^2 = G M r^2 / (r^2 + eps^2)^1.5
        speed = np.sqrt(self.gravity * self.core_mass * r**2 / (r**2 + self.softening**2) ** 1.5)
        tangent = spin * np.stack([-np.sin(phi), np.cos(phi)], axis=1)
        colors = hsv_colors(
            hue + 0.08 * (r - self.disc[0]) / (self.disc[1] - self.disc[0]), 0.45, 1.0
        )
        return center + offset, velocity + speed[:, None] * tangent, colors

    def reset(self):
        """two cores on a bound two-body orbit (eccentricity `eccentricity`, closest
        approach = the impact parameter) + their discs, starting on the way in"""
        destroy_bodies(self, self.bodies)
        mu = self.gravity * 2.0 * self.core_mass
        e, q = self.eccentricity, self.impact
        semi_latus = q * (1.0 + e)  # r(theta) = p / (1 + e cos theta)
        r0 = min(self.start_distance, 0.95 * semi_latus / (1.0 - e))  # inside the apocenter
        theta = -math.acos((semi_latus / r0 - 1.0) / e)  # negative: approaching
        k = math.sqrt(mu / semi_latus)
        # in the orbit frame (pericenter direction along +x)
        rel_p = r0 * np.array([math.cos(theta), math.sin(theta)])
        radial = np.array([math.cos(theta), math.sin(theta)])
        tangential = np.array([-math.sin(theta), math.cos(theta)])
        rel_v = k * e * math.sin(theta) * radial + k * (1.0 + e * math.cos(theta)) * tangential
        # turn the start direction to the right (+x) for the view
        turn = -theta
        c0, s0 = math.cos(turn), math.sin(turn)
        rel_p = np.array([c0 * rel_p[0] - s0 * rel_p[1], s0 * rel_p[0] + c0 * rel_p[1]])
        rel_v = np.array([c0 * rel_v[0] - s0 * rel_v[1], s0 * rel_v[0] + c0 * rel_v[1]])
        centers = [-0.5 * rel_p, 0.5 * rel_p]
        velocities = [-0.5 * rel_v, 0.5 * rel_v]
        # the orbit runs counter-clockwise (h > 0): prograde discs spin counter-clockwise too
        spins = [1.0, -1.0 if self.retrograde else 1.0]

        core_density = self.core_mass / (math.pi * 0.8**2)
        cores = create_points(
            self.world, np.array(centers), 0.8, [0xFFE08A, 0xFFE08A], core_density
        )
        cores.linear_velocity = np.array(velocities)
        star_p, star_v, star_c = [], [], []
        for center, velocity, spin, hue in zip(centers, velocities, spins, (0.55, 0.0)):
            p, v, color = self.galaxy_disc(center, velocity, spin, hue)
            star_p.append(p), star_v.append(v), star_c.append(color)
        stars = create_points(self.world, np.concatenate(star_p), 0.08, np.concatenate(star_c), 1.0)
        stars.linear_velocity = np.concatenate(star_v)
        self.cores, self.stars = cores, stars
        self.core_list = list(cores)  # single bodies, for dragging
        self.dragged = None
        self.bodies = b2d.Bodies([*cores, *stars])
        self.galaxy_of = np.repeat([0, 1], self.stars_per_galaxy)
        self.closest = math.inf

    # ---- mouse: drag a core (elsewhere: the usual camera dragging) ---------------------------

    def on_mouse_down(self, event):
        """a press close to a core grabs it"""
        p = np.array([event.world_position[0], event.world_position[1]])
        d = np.linalg.norm(self.cores.position - p, axis=1)
        if d.min() < self.grab_radius:
            self.dragged = int(np.argmin(d))
            self.drag_target = p
            return
        super().on_mouse_down(event)

    def on_mouse_move(self, event):
        """a grabbed core follows the mouse"""
        if self.dragged is not None:
            self.drag_target = np.array([event.world_position[0], event.world_position[1]])
            return
        super().on_mouse_move(event)

    def on_mouse_up(self, event):
        """release: the core keeps its velocity (a throw)"""
        self.dragged = None
        super().on_mouse_up(event)

    def on_mouse_leave(self, event):
        """the mouse left the canvas: release the core"""
        self.dragged = None
        super().on_mouse_leave(event)

    def steer_dragged_core(self):
        """the dragged galaxy towards the mouse: the core's velocity change goes to
        its disc stars too (they move along; stars already in the tails do not)"""
        core = self.core_list[self.dragged]
        position, old = core.position, core.linear_velocity
        center = np.array([position.x, position.y])
        velocity = self.drag_rate * (self.drag_target - center)
        speed = float(np.hypot(*velocity))
        if speed > self.max_drag_speed:
            velocity *= self.max_drag_speed / speed
        core.linear_velocity = (float(velocity[0]), float(velocity[1]))
        change = velocity - np.array([old.x, old.y])
        p = self.stars.position
        in_disc = (self.galaxy_of == self.dragged) & (
            np.linalg.norm(p - center, axis=1) < 1.5 * self.disc[1]
        )
        if in_disc.any():
            disc = self.stars[in_disc]
            disc.linear_velocity = disc.linear_velocity + change

    # ---- gravity of the two cores -----------------------------------------------------------

    def pre_update(self, dt):
        """forces of both cores on every star, the cores on each other: one batch call"""
        if self.dragged is not None:
            self.steer_dragged_core()
        t0 = time.perf_counter()
        p = self.bodies.position.astype(np.float64)
        m = self.bodies.mass.astype(np.float64)
        core_p = p[:2]
        delta = core_p[None, :, :] - p[:, None, :]  # (n, 2 cores, 2): body -> core
        d2 = np.einsum("ijk,ijk->ij", delta, delta) + self.softening**2
        weight = self.gravity * self.core_mass * d2**-1.5
        weight[0, 0] = weight[1, 1] = 0.0  # a core does not pull on itself
        forces = m[:, None] * np.einsum("ij,ijk->ik", weight, delta)
        self.bodies.apply_force_to_center(forces)
        self.closest = min(self.closest, float(np.linalg.norm(core_p[1] - core_p[0])))
        self.force_time(1000.0 * (time.perf_counter() - t0))

    # ---- drawing ----------------------------------------------------------------------------

    def tidal_fraction(self):
        """stars more than 1.5 disc radii away from both cores (tails, bridge, escapers)"""
        p = self.stars.position
        core_p = self.cores.position
        d = np.linalg.norm(p[:, None, :] - core_p[None, :, :], axis=2)
        return float(np.mean(d.min(axis=1) > 1.5 * self.disc[1]))

    def post_debug_draw(self):
        dd = self.debug_draw
        sep = float(np.linalg.norm(self.cores.position[1] - self.cores.position[0]))
        text = (
            f"{len(self.stars)} stars, core distance {sep:.1f} (closest {self.closest:.1f}), "
            f"in tails {100 * self.tidal_fraction():.0f}%, forces {self.force_time.value or 0.0:.2f} ms"
        )
        dd.draw_string((-35.0, 30.0), text, b2d.HexColor.White)
