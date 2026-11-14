"""A swarm of thousands of bodies steered towards the mouse by a numpy force field.

Every step reads all positions and velocities as two arrays, computes a steering force per
body with numpy (seek + swirl + a bit of noise) and applies all forces in one call.
Hold the mouse button to scatter the swarm; without a mouse the swarm chases a wandering target.
"""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import create_circles, destroy_bodies, hsv_colors, perpendicular, unit_and_length


class BatchSwarm(SampleBase):
    """Thousands of bodies following the mouse, steered by vectorized numpy forces."""

    hx, hy = 40.0, 25.0  # arena half size
    radius = 0.2

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 1200
        self.max_speed = 14.0
        self.steering = 4.0
        self.swirl = 30.0  # degrees
        self.repel = False
        self.rng = np.random.default_rng(1)
        self.target = np.zeros(2)

        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=self.hx, hy=self.hy))
        self.bodies = b2d.Bodies()
        self.create_swarm()

        for widget in (
            widgets.IntSlider("bodies", 200, 6000, 100, self.count, self.set_count),
            widgets.FloatSlider("max speed", 2.0, 40.0, 1.0, self.max_speed, self.setter("max_speed")),
            widgets.FloatSlider("steering", 0.5, 20.0, 0.5, self.steering, self.setter("steering")),
            widgets.FloatSlider("swirl (deg)", 0.0, 90.0, 5.0, self.swirl, self.setter("swirl")),
        ):
            self.frontend.add_widget(widget)

    def setter(self, name):
        return lambda value: setattr(self, name, value)

    def aabb(self):
        return b2d.aabb(lower_bound=(-self.hx, -self.hy), upper_bound=(self.hx, self.hy))

    def create_swarm(self):
        destroy_bodies(self, self.bodies)
        n = self.count
        margin = 2.0 * self.radius
        positions = self.rng.uniform((-self.hx + margin, -self.hy + margin), (self.hx - margin, self.hy - margin), (n, 2))
        # color by the starting position: the swarm keeps mixing these up
        colors = hsv_colors(0.5 + 0.5 * np.arctan2(positions[:, 1], positions[:, 0]) / math.pi)
        self.bodies = create_circles(self.world, positions, self.radius, colors=colors, friction=0.0, restitution=0.3)
        # a small per-body speed variation makes the swarm look alive
        self.speed_factor = self.rng.uniform(0.6, 1.0, n)

    def set_count(self, value):
        self.count = int(value)
        self.create_swarm()

    # ---- the force field ------------------------------------------------------------------

    def wandering_target(self):
        t = self.world_time
        return np.array([0.7 * self.hx * math.sin(0.31 * t), 0.7 * self.hy * math.sin(0.47 * t + 1.0)])

    def pre_update(self, dt):
        self.target = np.array(self.mouse_pos, dtype=np.float64) if self.mouse_pos is not None else self.wandering_target()

        bodies = self.bodies
        positions = bodies.position  # (n, 2)
        velocities = bodies.linear_velocity  # (n, 2)
        masses = bodies.mass  # (n,)

        direction, distance = unit_and_length(self.target - positions)
        # seek the target, slowing down on arrival, and swirl around it
        speed = self.max_speed * self.speed_factor * np.minimum(1.0, distance / 4.0)
        angle = math.radians(self.swirl)
        desired = speed[:, None] * (math.cos(angle) * direction + math.sin(angle) * perpendicular(direction))
        desired += self.rng.normal(scale=0.5, size=desired.shape)

        force = self.steering * masses[:, None] * (desired - velocities)
        if self.repel:
            # an explosion-like push away from the mouse
            push = np.clip(1.0 - distance / 12.0, 0.0, 1.0)
            force -= (300.0 * masses * push)[:, None] * direction

        bodies.apply_force_to_center(force)

    # ---- mouse: hold to scatter -----------------------------------------------------------

    def on_mouse_down(self, event):
        self.mouse_pos = event.world_position
        self.repel = True

    def on_mouse_up(self, event):
        super().on_mouse_up(event)
        self.repel = False

    def on_mouse_leave(self, event):
        super().on_mouse_leave(event)
        self.repel = False

    # ---- drawing --------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        target = tuple(self.target)
        color = b2d.HexColor.OrangeRed if self.repel else b2d.HexColor.Gold
        dd.draw_circle(target, 12.0 if self.repel else 1.0, color)
        dd.draw_point(target, 8.0, color)
        dd.draw_string((0.0, self.hy - 1.5),f"{len(self.bodies)} bodies, one apply_force_to_center call", b2d.HexColor.White)


if __name__ == "__main__":
    BatchSwarm.run()
