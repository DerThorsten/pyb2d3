"""Dam break: a water column collapses into a tank with an obstacle (SPH-style
pressure + viscosity from the neighbor densities, numpy over all particles)."""

import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .batch_common import Ema, destroy_bodies, hsv_colors, neighbor_pairs, pair_sum

# the particles never collide with each other (negative group): the SPH forces
# keep them apart, box2d only does the walls and the obstacle
FLUID_GROUP = -1


def sph_densities(positions, smoothing):
    """pairs within `smoothing` + density / near density per particle
    (kernels (1 - r/h)^2 and (1 - r/h)^3 over both pair ends, plus the particle itself)"""
    n = len(positions)
    i, j, delta, distance = neighbor_pairs(positions, smoothing)
    q = 1.0 - distance / smoothing
    density = 1.0 + np.bincount(i, q**2, n) + np.bincount(j, q**2, n)
    near = 1.0 + np.bincount(i, q**3, n) + np.bincount(j, q**3, n)
    return (i, j, delta, distance, q), density, near


@register_sample("Fluids & Matter", "Dam Break")
class BatchDamBreak(SampleBase):
    """A column of water collapses, splashes over an obstacle and settles.

    The particles do not collide with each other: one neighbor search over all
    particles gives the densities, pressure pushes from dense to thin, viscosity
    evens out the velocities, one batch call applies the forces.
    Sliders: stiffness (incompressibility), viscosity, particle count.
    Mouse: drag the obstacle (or the camera).
    Hint: low stiffness = squashy foam, high viscosity = honey; very stiff water
    "boils" (the forces are explicit, once per 60 Hz step).
    """

    radius = 0.1  # particle radius (drawing + walls)
    smoothing = 0.42  # SPH smoothing length h: the neighbor radius
    tank = (24.0, 12.0)
    max_accel = 120.0  # m/s^2, about 12 g

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.stiffness = 10.0
        self.viscosity = 6.0
        self.count = 1200
        self.particles = b2d.Bodies()
        self.rng = np.random.default_rng(5)
        self.timing = Ema()
        self.pairs = 0
        self.create_tank()
        self.reset()
        for widget in (
            widgets.Button("reset", self.reset),
            widgets.FloatSlider("stiffness", 2.0, 30.0, 0.5, self.stiffness, self.set_stiffness),
            widgets.FloatSlider("viscosity", 0.0, 15.0, 0.25, self.viscosity, self.set_viscosity),
            widgets.IntSlider("particles", 300, 2000, 100, self.count, self.set_count),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        w, h = self.tank
        return b2d.aabb(lower_bound=(-1.0, -1.0), upper_bound=(w + 1.0, h + 1.5))

    def create_tank(self):
        """the tank (static) and a dynamic obstacle block on its floor"""
        w, h = self.tank
        tank = self.world.create_static_body()
        wall_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.1, custom_color=b2d.HexColor.SlateGray)
        )
        tank.create_shape(wall_def, b2d.box(w / 2 + 1.0, 0.5, center=(w / 2, -0.5)))
        tank.create_shape(wall_def, b2d.box(0.5, h, center=(-0.5, h)))
        tank.create_shape(wall_def, b2d.box(0.5, h, center=(w + 0.5, h)))
        self.obstacle = self.world.create_dynamic_body(position=(0.62 * w, 1.0))
        self.obstacle.create_shape(
            b2d.shape_def(
                density=3.0,
                material=b2d.surface_material(friction=0.6, custom_color=b2d.HexColor.Peru),
            ),
            b2d.box(1.0, 1.0),
        )

    def reset(self):
        """a fresh column of water at the left wall"""
        destroy_bodies(self, self.particles)
        spacing = 0.5 * self.smoothing
        columns = 26
        rows = int(np.ceil(self.count / columns))
        gx, gy = np.meshgrid(np.arange(columns), np.arange(rows))
        positions = np.stack([gx.ravel() * spacing + 0.2, gy.ravel() * spacing + 0.2], axis=1)[
            : self.count
        ]
        positions += self.rng.uniform(-0.01, 0.01, positions.shape)
        colors = hsv_colors(0.55 + 0.05 * positions[:, 1] / positions[:, 1].max(), 0.7, 0.95)
        bodies = b2d.Bodies()
        fluid_filter = b2d.make_filter(group_index=FLUID_GROUP)
        for (x, y), color in zip(positions, colors):
            body = self.world.create_dynamic_body(position=(float(x), float(y)))
            material = b2d.surface_material(friction=0.0, custom_color=int(color))
            body.create_shape(
                b2d.shape_def(density=1.0, material=material, filter=fluid_filter),
                b2d.circle(radius=self.radius),
            )
            bodies.append(body)
        self.particles = bodies
        # rest density: the density inside the initial packing
        _, density, _ = sph_densities(positions, self.smoothing)
        self.rest_density = float(np.median(density))
        self.mass = float(self.particles.mass[0])

    def set_stiffness(self, value):
        self.stiffness = value

    def set_viscosity(self, value):
        self.viscosity = value

    def set_count(self, value):
        self.count = int(value)
        self.reset()

    # ---- SPH --------------------------------------------------------------------------------

    def pre_update(self, dt):
        """pressure + viscosity forces of all pairs, one batch call"""
        t0 = time.perf_counter()
        positions = self.particles.position.astype(np.float64)
        velocities = self.particles.linear_velocity.astype(np.float64)
        n = len(positions)
        (i, j, delta, distance, q), density, near = sph_densities(positions, self.smoothing)
        pressure = self.stiffness * (density - self.rest_density)
        near_pressure = self.stiffness * near  # short-range push: no clumping
        # pair push along the pair direction (positive: apart)
        push = (pressure[i] + pressure[j]) * q + (near_pressure[i] + near_pressure[j]) * q**2
        direction = delta / np.maximum(distance, 1e-6)[:, None]
        accel = -push[:, None] * direction  # on i (j gets the opposite)
        # viscosity: pull the velocities of close pairs together
        accel += self.viscosity * q[:, None] * (velocities[j] - velocities[i])
        total = pair_sum(n, i, j, accel)
        # explicit forces + 60 Hz: cap the acceleration (a squeezed particle
        # would otherwise be shot out and the fluid "boils")
        magnitude = np.linalg.norm(total, axis=1)
        total *= np.minimum(1.0, self.max_accel / np.maximum(magnitude, 1e-9))[:, None]
        self.particles.apply_force_to_center(total * self.mass)
        self.pairs = len(i)
        self.density = density
        self.timing(1000.0 * (time.perf_counter() - t0))

    def post_debug_draw(self):
        speed = self.particles.speed
        text = (
            f"{len(self.particles)} particles, {self.pairs} pairs, forces {self.timing.value or 0:.1f} ms   "
            f"speed mean {speed.mean():.2f} max {speed.max():.1f}  front x {self.particles.position[:, 0].max():.1f}  "
            f"top y {self.particles.position[:, 1].max():.1f}"
        )
        self.debug_draw.draw_string((0.0, self.tank[1] + 1.0), text, b2d.HexColor.White)
