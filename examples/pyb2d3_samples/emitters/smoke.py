"""Smoke from a chimney: buoyant puffs drift in the wind and fade."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

WORLD, SMOKE, CRATE = 0x1, 0x2, 0x4  # collision categories
CHIMNEY_HEIGHT = 6.0
GRAVITY = 10.0
DRAG = 1.2  # 1 / s, how fast the puffs take on the wind speed
WIND_HEIGHT = 10.0  # the wind grows from none at the ground to full strength here
# hot and dark at the mouth, then gray, then almost the background (by age)
SMOKE_COLORS = [(0.0, 0x3A3A3A), (0.15, 0x6E6E6E), (0.6, 0xA8A8A8), (1.0, 0x505050)]


@register_sample("Emitters", "Smoke", video=True)
class Smoke(SampleBase):
    """Smoke from a chimney: the puffs rise (a lift force on all of them), the wind drags them
    sideways, their color fades with their age. The puffs push each other apart.
    Mouse: drag or tip over the chimney, drag the crates into the smoke.
    Sliders: rate, wind, buoyancy.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -GRAVITY)))
        self.wind = 3.0
        self.buoyancy = 0.15  # upward acceleration in units of g
        self.create_chimney()
        self.create_crates()
        self.create_smoke()
        for widget in (
            widgets.FloatSlider("rate (1/s)", 5.0, 150.0, 5.0, 40.0, self.set_rate),
            widgets.FloatSlider("wind", -8.0, 8.0, 0.5, self.wind, self.set_wind),
            widgets.FloatSlider("buoyancy", 0.0, 0.6, 0.05, self.buoyancy, self.set_buoyancy),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-20.0, -1.0), upper_bound=(20.0, 26.0))

    def create_chimney(self):
        world_filter = b2d.make_filter(category_bits=WORLD, mask_bits=0xFFFF)
        ground = self.world.create_static_body()
        ground.create_shape(
            b2d.shape_def(filter=world_filter), b2d.segment((-30.0, 0.0), (30.0, 0.0))
        )
        # a dynamic body: drag it around or knock it over, the smoke comes out of its top
        self.chimney = self.world.create_dynamic_body(position=(0.0, 0.5 * CHIMNEY_HEIGHT))
        self.chimney.create_shape(
            b2d.shape_def(
                density=2.0,
                filter=world_filter,
                material=b2d.surface_material(custom_color=b2d.HexColor.Firebrick),
            ),
            b2d.box(0.8, 0.5 * CHIMNEY_HEIGHT),
        )

    def create_crates(self):
        crate = b2d.shape_def(
            density=0.3,
            filter=b2d.make_filter(category_bits=CRATE, mask_bits=0xFFFF),
            material=b2d.surface_material(custom_color=b2d.HexColor.Peru),
        )
        for x in (-6.0, 6.0):
            body = self.world.create_dynamic_body(position=(x, 1.0))
            body.create_shape(crate, b2d.box(1.0, 1.0))

    def create_smoke(self):
        self.smoke = ext.RadialEmitter(
            self.world,
            b2d.shape_def(
                density=0.1,
                filter=b2d.make_filter(category_bits=SMOKE, mask_bits=0xFFFF),
                material=b2d.surface_material(friction=0.0, restitution=0.0),
            ),
            b2d.circle(radius=0.3),
            # no gravity: the lift is applied in pre_update
            body_def=b2d.body_def(gravity_scale=0.0, linear_damping=1.0),
            # on the chimney: just above its top, along its axis (the emitter follows the body)
            body=self.chimney,
            local_frame=b2d.transform(
                (0.0, 0.5 * CHIMNEY_HEIGHT + 0.3), b2d.make_rot(0.5 * math.pi)
            ),
            rate=40.0,
            capacity=600,
            angle_min=-0.25,
            angle_max=0.25,
            speed=ext.uniform(2.0, 3.0),
            lifetime=ext.normal(9.0, 1.5),
            max_lifetime=12.0,
            colors=SMOKE_COLORS,
        )

    def set_rate(self, value):
        self.smoke.rate = value

    def set_wind(self, value):
        self.wind = value

    def set_buoyancy(self, value):
        self.buoyancy = value

    def pre_update(self, dt):
        self.smoke.step(dt)
        puffs = self.smoke.particles
        if not len(puffs):
            return
        # wind (stronger with the height) and lift, for all puffs in one call
        wind = self.wind * np.clip(puffs.position[:, 1] / WIND_HEIGHT, 0.0, 1.0)
        force = np.zeros((len(puffs), 2))
        force[:, 0] = DRAG * puffs.mass * (wind - puffs.linear_velocity[:, 0])
        force[:, 1] = self.buoyancy * GRAVITY * puffs.mass
        puffs.apply_force_to_center(force)

    def post_debug_draw(self):
        self.debug_draw.draw_string((-19.0, 25.0), f"{len(self.smoke)} puffs", b2d.HexColor.White)
