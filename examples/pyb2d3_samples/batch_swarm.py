"""A swarm of thousands of bodies steered towards the mouse by a numpy force field.

Every step reads all positions and velocities as two arrays, computes a steering force per
body with numpy (seek + swirl + a bit of noise) and applies all forces in one call.
Hold the mouse button to scatter the swarm; without a mouse the swarm chases a wandering target.
"""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import hsv_colors

HX, HY = 40.0, 25.0  # arena half size
RADIUS = 0.2
ARRIVAL_RADIUS = 4.0  # the bodies slow down within this distance of the target
SCATTER_RADIUS = 12.0


@register_sample("Batch API", "Swarm", video=True)
class BatchSwarm(SampleBase):
    """Thousands of bodies following the mouse, steered by vectorized numpy forces.

    Mouse: the swarm chases the cursor, hold the button to scatter it.
    Hint: raise "bodies" to see how far one batch call per step scales.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 1200
        self.max_speed = 14.0
        self.steering = 4.0
        self.swirl = 30.0  # degrees
        self.rng = np.random.default_rng(1)
        self.target = np.zeros(2)
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=HX, hy=HY))
        self.bodies = b2d.Bodies()
        self.create_swarm()
        for widget in (
            widgets.IntSlider("bodies", 200, 6000, 100, self.count, self.set_count),
            widgets.FloatSlider("max speed", 2.0, 40.0, 1.0, self.max_speed, self.set_max_speed),
            widgets.FloatSlider("steering", 0.5, 20.0, 0.5, self.steering, self.set_steering),
            widgets.FloatSlider("swirl (deg)", 0.0, 90.0, 5.0, self.swirl, self.set_swirl),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-HX, -HY), upper_bound=(HX, HY))

    def create_swarm(self):
        self.bodies.destroy()
        margin = 2.0 * RADIUS
        positions = self.rng.uniform(
            (-HX + margin, -HY + margin), (HX - margin, HY - margin), (self.count, 2)
        )
        # color by the starting position: the swarm keeps mixing these up
        colors = hsv_colors(0.5 + 0.5 * np.arctan2(positions[:, 1], positions[:, 0]) / math.pi)
        material = b2d.surface_material(friction=0.0, restitution=0.3)
        self.bodies, shapes = self.world.create_bodies(
            positions, b2d.shape_def(material=material), b2d.circle(radius=RADIUS)
        )
        shapes.custom_color = colors
        # a small per-body speed variation makes the swarm look alive
        self.speed_factor = self.rng.uniform(0.6, 1.0, self.count)

    def set_count(self, value):
        self.count = int(value)
        self.create_swarm()

    def set_max_speed(self, value):
        self.max_speed = value

    def set_steering(self, value):
        self.steering = value

    def set_swirl(self, value):
        self.swirl = value

    def on_mouse_down(self, event):
        # no super(): the button scatters the swarm instead of dragging bodies / the camera
        self.is_mouse_down = True
        self.mouse_pos = event.world_position

    def pre_update(self, dt):
        if self.mouse_pos is not None:
            self.target = np.array(self.mouse_pos)
        else:  # no mouse: a target wandering on a Lissajous curve
            t = self.world_time
            self.target = np.array(
                [0.7 * HX * math.sin(0.31 * t), 0.7 * HY * math.sin(0.47 * t + 1.0)]
            )

        masses = self.bodies.mass[:, None]
        to_target = self.target - self.bodies.position
        distance = np.linalg.norm(to_target, axis=1)
        direction = to_target / np.maximum(distance, 1e-6)[:, None]
        sideways = np.stack([-direction[:, 1], direction[:, 0]], axis=1)  # rotated by +90 deg

        # seek the target, slowing down on arrival, and swirl around it
        speed = self.max_speed * self.speed_factor * np.minimum(1.0, distance / ARRIVAL_RADIUS)
        angle = math.radians(self.swirl)
        desired = speed[:, None] * (math.cos(angle) * direction + math.sin(angle) * sideways)
        desired += self.rng.normal(scale=0.5, size=desired.shape)
        force = self.steering * masses * (desired - self.bodies.linear_velocity)

        if self.is_mouse_down:
            # an explosion-like push away from the mouse
            push = np.clip(1.0 - distance / SCATTER_RADIUS, 0.0, 1.0)[:, None]
            force -= 300.0 * masses * push * direction

        self.bodies.apply_force_to_center(force)

    def post_debug_draw(self):
        dd = self.debug_draw
        target = tuple(self.target)
        color = b2d.HexColor.OrangeRed if self.is_mouse_down else b2d.HexColor.Gold
        dd.draw_circle(target, SCATTER_RADIUS if self.is_mouse_down else 1.0, color)
        dd.draw_point(target, 8.0, color)
        text = f"{len(self.bodies)} bodies, one apply_force_to_center call"
        dd.draw_string((0.0, HY - 1.5), text, b2d.HexColor.White)
