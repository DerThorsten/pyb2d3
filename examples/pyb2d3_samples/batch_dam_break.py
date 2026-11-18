"""Dam break: a water column collapses into a tank with an obstacle (SPH-style
pressure + viscosity from the neighbor densities, numpy over all particles)."""

import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import hsv_colors, pair_sum

# the particles never collide with each other (negative group): the SPH forces
# keep them apart, box2d only does the walls and the obstacle
FLUID_GROUP = -1
RADIUS = 0.1  # particle radius (drawing + walls)
SMOOTHING = 0.42  # SPH smoothing length h: the neighbor radius
TANK = (24.0, 12.0)
COLUMNS = 26  # width of the water column in particles
# explicit forces at 60 Hz: a squeezed particle would be shot out and the fluid "boils"
MAX_ACCEL = 120.0  # m/s^2, about 12 g


def sph_densities(positions, smoothing):
    """the neighbor pairs + density / near density per particle
    (kernels (1 - r/h)^2 and (1 - r/h)^3 over both pair ends, plus the particle itself)"""
    n = len(positions)
    i, j, delta, distance = ext.neighbor_pairs(positions, smoothing)
    q = 1.0 - distance / smoothing
    density = 1.0 + np.bincount(i, q**2, n) + np.bincount(j, q**2, n)
    near = 1.0 + np.bincount(i, q**3, n) + np.bincount(j, q**3, n)
    return (i, j, delta, distance, q), density, near


@register_sample("Fluids & Matter", "Dam Break", video=True)
class BatchDamBreak(SampleBase):
    """A water column (SPH particles) collapses over an obstacle: neighbor densities
    give the pressure, all with numpy and one batch call.
    Sliders: stiffness, viscosity, count.
    Mouse: drag the obstacle.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.stiffness = 10.0
        self.viscosity = 6.0
        self.count = 1200
        self.particles = b2d.Bodies()
        self.rng = np.random.default_rng(5)
        self.force_ms = 0.0  # time of the force computation, smoothed
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
        w, h = TANK
        return b2d.aabb(lower_bound=(-1.0, -1.0), upper_bound=(w + 1.0, h + 1.5))

    def create_tank(self):
        """the tank (static) and a dynamic obstacle block on its floor"""
        w, h = TANK
        tank = self.world.create_static_body()
        wall_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.1, custom_color=b2d.HexColor.SlateGray)
        )
        tank.create_shape(wall_def, b2d.box(w / 2 + 1.0, 0.5, center=(w / 2, -0.5)))
        tank.create_shape(wall_def, b2d.box(0.5, h, center=(-0.5, h)))
        tank.create_shape(wall_def, b2d.box(0.5, h, center=(w + 0.5, h)))
        obstacle = self.world.create_dynamic_body(position=(0.62 * w, 1.0))
        obstacle_material = b2d.surface_material(friction=0.6, custom_color=b2d.HexColor.Peru)
        obstacle.create_shape(
            b2d.shape_def(density=3.0, material=obstacle_material), b2d.box(1.0, 1.0)
        )

    def reset(self):
        """a fresh column of water at the left wall"""
        self.particles.destroy()
        spacing = 0.5 * SMOOTHING
        rows = int(np.ceil(self.count / COLUMNS))
        gx, gy = np.meshgrid(np.arange(COLUMNS), np.arange(rows))
        positions = 0.2 + spacing * np.stack([gx.ravel(), gy.ravel()], axis=1)[: self.count]
        positions += self.rng.uniform(-0.01, 0.01, positions.shape)
        colors = hsv_colors(0.55 + 0.05 * positions[:, 1] / positions[:, 1].max(), 0.7, 0.95)
        fluid_filter = b2d.make_filter(group_index=FLUID_GROUP)
        material = b2d.surface_material(friction=0.0)
        self.particles, shapes = self.world.create_bodies(
            positions,
            b2d.shape_def(material=material, filter=fluid_filter),
            b2d.circle(radius=RADIUS),
        )
        shapes.custom_color = colors
        # rest density: the density inside the initial packing
        _, density, _ = sph_densities(positions, SMOOTHING)
        self.rest_density = np.median(density)
        self.mass = self.particles.mass[0]

    def set_stiffness(self, value):
        self.stiffness = value

    def set_viscosity(self, value):
        self.viscosity = value

    def set_count(self, value):
        self.count = int(value)
        self.reset()

    def pre_update(self, dt):
        """pressure + viscosity forces of all pairs, one batch call"""
        t0 = time.perf_counter()
        # (the batch api returns float32: compute the forces in double precision)
        positions = self.particles.position.astype(np.float64)
        velocities = self.particles.linear_velocity.astype(np.float64)
        (i, j, delta, distance, q), density, near = sph_densities(positions, SMOOTHING)
        pressure = self.stiffness * (density - self.rest_density)
        near_pressure = self.stiffness * near  # short-range push: no clumping
        # push along the pair direction (positive: apart)
        push = (pressure[i] + pressure[j]) * q + (near_pressure[i] + near_pressure[j]) * q**2
        direction = delta / np.maximum(distance, 1e-6)[:, None]
        accel = -push[:, None] * direction  # on i (j gets the opposite)
        # viscosity: pull the velocities of close pairs together
        accel += self.viscosity * q[:, None] * (velocities[j] - velocities[i])
        total = pair_sum(len(positions), i, j, accel)
        magnitude = np.linalg.norm(total, axis=1)
        total *= np.minimum(1.0, MAX_ACCEL / np.maximum(magnitude, 1e-9))[:, None]
        self.particles.apply_force_to_center(total * self.mass)
        self.pairs = len(i)
        self.force_ms = 0.9 * self.force_ms + 0.1 * 1000.0 * (time.perf_counter() - t0)

    def post_debug_draw(self):
        speed = self.particles.speed
        position = self.particles.position
        text = (
            f"{len(self.particles)} particles, {self.pairs} pairs, forces {self.force_ms:.1f} ms   "
            f"speed mean {speed.mean():.2f} max {speed.max():.1f}  "
            f"front x {position[:, 0].max():.1f}  top y {position[:, 1].max():.1f}"
        )
        self.debug_draw.draw_string((0.0, TANK[1] + 1.0), text, b2d.HexColor.White)
