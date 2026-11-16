"""A snow globe you shake with the mouse: hundreds of slow flakes swirl up in the
liquid and settle on a little village (numpy forces + one batch call per step)."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .batch_common import create_circles, hsv_colors


@register_sample("Fluids & Matter", "Snow Globe")
class BatchSnowGlobe(SampleBase):
    """A snow globe on a springy stand. The flakes sink slowly through the liquid and
    settle on the village; shake the globe and they swirl up again.

    Keys: space gives the globe a shake.
    Mouse: grab the globe and shake it (it springs back to its stand).
    Sliders: flutter (little eddies), turbulence (how much a shake stirs the liquid).
    Hint: the liquid moves with the globe: every flake is dragged towards the
    velocity of the glass around it, a shake (the globe's acceleration) stirs up
    random eddies. All of it is numpy + one batch force call for all flakes.
    """

    center = (0.0, 6.0)
    radius = 5.0
    glass_radius = 0.3  # thick glass: a shaken globe moves fast, flakes must not tunnel out
    max_speed = 10.0  # m/s of the globe (a step moves it less than the glass thickness)
    drag = 6.0  # 1/s, flakes follow the liquid
    count = 800

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.mouse_joint_force_multiplier = 40.0  # strong enough to shake against the spring
        self.flutter = 3.0
        self.turbulence = 1.0
        self.stirring = 0.0  # current strength of the eddies (decays after a shake)
        self.rng = np.random.default_rng(17)
        self.build_globe()
        self.previous_velocity = np.zeros(2)
        for widget in (
            widgets.Button("shake (space)", self.shake),
            widgets.FloatSlider("flutter", 0.0, 10.0, 0.25, self.flutter, self.set_flutter),
            widgets.FloatSlider("turbulence", 0.0, 3.0, 0.1, self.turbulence, self.set_turbulence),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-9.0, -1.0), upper_bound=(9.0, 13.0))

    def build_globe(self):
        """a dynamic globe (a ring of capsules + a village inside) on a spring, full of flakes"""
        cx, cy = self.center
        r = self.radius
        globe = self.world.create_dynamic_body(
            position=(cx, cy), enable_sleep=False, angular_damping=1.0
        )
        glass = b2d.shape_def(
            density=2.0,
            material=b2d.surface_material(friction=0.2, custom_color=b2d.HexColor.LightSkyBlue),
        )
        n = 48
        angles = np.linspace(0.0, 2.0 * math.pi, n + 1)
        ring = (r + self.glass_radius) * np.stack([np.cos(angles), np.sin(angles)], axis=1)
        for p, q in zip(ring[:-1], ring[1:]):
            globe.create_shape(glass, b2d.capsule(tuple(p), tuple(q), self.glass_radius))
        # the village: a snow field, two houses, a fir tree (part of the globe)
        wood = b2d.shape_def(
            material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.SaddleBrown)
        )
        roof = b2d.shape_def(
            material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.Firebrick)
        )
        fir = b2d.shape_def(
            material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.ForestGreen)
        )
        floor = -0.6 * r
        globe.create_shape(wood, b2d.box(0.8 * r, 0.15, center=(0.0, floor - 0.15)))
        for x, w, h in ((-2.0, 0.8, 0.7), (1.2, 0.6, 0.55)):
            globe.create_shape(wood, b2d.box(w, h, center=(x, floor + h)))
            top = floor + 2 * h
            globe.create_shape(
                roof,
                b2d.polygon(points=[(x - w - 0.2, top), (x + w + 0.2, top), (x, top + 0.9 * w)]),
            )
        globe.create_shape(
            fir, b2d.polygon(points=[(3.0, floor), (3.9, floor), (3.45, floor + 2.4)])
        )
        self.globe = globe

        # the stand, the globe hangs on a springy motor joint above it (no contact
        # between jointed bodies)
        stand = self.world.create_static_body(position=(cx, cy - r - 0.9))
        stand.create_shape(wood, b2d.box(3.0, 0.6))
        spring = b2d.motor_joint_def(
            body_a=self.anchor_body,
            body_b=globe,
            linear_hertz=2.0,
            linear_damping_ratio=0.2,
            max_spring_force=1e6,
            angular_hertz=1.5,
            angular_damping_ratio=0.3,
            max_spring_torque=1e6,
        )
        spring.local_anchor_a = (cx, cy)
        self.world.create_motor_joint(spring)

        # flakes: a jittered disc inside the globe, above the village
        radius = r * np.sqrt(self.rng.uniform(0.0, 0.8, self.count))
        angle = self.rng.uniform(0.0, 2.0 * math.pi, self.count)
        positions = np.stack([cx + radius * np.cos(angle), cy + radius * np.sin(angle)], axis=1)
        positions[:, 1] = np.maximum(positions[:, 1], cy + floor + 1.5)
        whites = hsv_colors(np.full(self.count, 0.6), self.rng.uniform(0.0, 0.12, self.count), 1.0)
        self.flakes = create_circles(
            self.world,
            positions,
            self.rng.uniform(0.04, 0.08, self.count),
            colors=whites,
            density=0.5,
            friction=0.6,
            gravity_scale=0.3,  # buoyancy: they sink slowly
            enable_sleep=False,
        )

    # ---- controls -------------------------------------------------------------------------

    def set_flutter(self, value):
        self.flutter = value

    def set_turbulence(self, value):
        self.turbulence = value

    def shake(self):
        """a kick in a random (mostly sideways) direction"""
        angle = self.rng.uniform(-0.6, 0.6) + self.rng.choice([0.0, math.pi])
        direction = (math.cos(angle), math.sin(angle))
        impulse = 8.0 * self.globe.mass
        self.globe.apply_linear_impulse_to_center((impulse * direction[0], impulse * direction[1]))

    def on_key_down(self, event):
        if event.key == "space":
            self.shake()

    def on_mouse_down(self, event):
        """a click inside the globe grabs the globe (not a flake)"""
        x, y = event.world_position
        position = self.globe.position
        if math.hypot(x - position.x, y - position.y) < self.radius + 2.0 * self.glass_radius:
            self.is_mouse_down = True
            self.mouse_pos = event.world_position
            self._mouse_drag.begin(event.world_position, body=self.globe)
        else:
            super().on_mouse_down(event)

    # ---- simulation -----------------------------------------------------------------------

    def pre_update(self, dt):
        globe = self.globe
        velocity = np.array(tuple(globe.linear_velocity))
        speed = float(np.linalg.norm(velocity))
        if speed > self.max_speed:  # faster glass lets flakes tunnel out
            velocity *= self.max_speed / speed
            globe.linear_velocity = tuple(velocity)

        # a shake (the globe's acceleration) stirs the liquid, the eddies calm down slowly
        acceleration = float(np.linalg.norm(velocity - self.previous_velocity)) / dt
        self.previous_velocity = velocity
        self.stirring = max(self.stirring * math.exp(-dt / 1.5), 0.4 * acceleration)
        self.stirring = min(self.stirring, 80.0)

        # the liquid moves with the glass: drag every flake towards the glass velocity there
        center = np.array(tuple(globe.position))
        offset = self.flakes.position - center
        liquid = velocity + globe.angular_velocity * np.stack([-offset[:, 1], offset[:, 0]], axis=1)
        accel = self.drag * (liquid - self.flakes.linear_velocity)
        n = len(self.flakes)
        eddies = self.flutter + self.turbulence * self.stirring
        accel += self.rng.normal(0.0, 1.0, (n, 2)) * eddies
        self.flakes.apply_force_to_center(self.flakes.mass[:, None] * accel)

        # flakes that escaped anyway (a wild shake) are put back inside
        outside = np.linalg.norm(offset, axis=1) > self.radius + 0.5
        if outside.any():
            k = int(outside.sum())
            back = center + self.rng.uniform(-1.5, 1.5, (k, 2)) + (0.0, 1.5)
            escaped = self.flakes[outside]
            escaped.set_transform(back, (1.0, 0.0))
            escaped.linear_velocity = np.tile(velocity, (k, 1))

    def post_debug_draw(self):
        floating = int(np.count_nonzero(self.flakes.speed > 0.15))
        text = f"{len(self.flakes)} flakes, {floating} floating"
        self.debug_draw.draw_string((-8.5, 12.5), text, b2d.HexColor.White)
