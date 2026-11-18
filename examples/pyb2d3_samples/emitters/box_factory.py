"""A box factory: a line emitter drops polygon crates onto conveyor belts."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from ..examples_common.batch import hsv_colors

# zig-zag belts (center x, center y, direction): each one runs towards its lower end
BELTS = [(2.0, 16.0, -1), (-2.0, 12.0, 1), (2.0, 8.0, -1)]
BELT_TILT = 0.08  # rad
# crates fade from bright to dark wood over this many seconds (they never expire, so the
# emitter's colors-by-life-fraction do not apply)
FADE_TIME = 60.0
CRATE_HUE, CRATE_SATURATION, CRATE_VALUE = 0.084, 0.67, 0.82


@register_sample("Emitters", "Box Factory", video=True)
class BoxFactory(SampleBase):
    """A box factory: a line emitter drops crates (polygons, not circles) onto zig-zag
    conveyor belts (a surface material's tangent speed); they end in a bin. Crates that never
    expire, the oldest ones are recycled when the factory is full.
    Sliders: rate, belt speed, crate size.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.rate = 2.5
        self.size = 0.4
        self.create_bin()
        self.create_belts()
        self.set_belt_speed(3.0)
        self.crates = None
        self.build_emitter()
        for widget in (
            widgets.FloatSlider("rate (1/s)", 0.5, 20.0, 0.5, self.rate, self.set_rate),
            widgets.FloatSlider("belt speed", 0.0, 8.0, 0.5, 3.0, self.set_belt_speed),
            widgets.FloatSlider("crate size", 0.15, 0.8, 0.05, self.size, self.set_size),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-16.0, -1.0), upper_bound=(12.0, 22.0))

    def create_bin(self):
        ground = self.world.create_static_body()
        wall = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.DimGray))
        for p, q in (((-14, 6), (-14, 0)), ((-14, 0), (-4, 0)), ((-4, 0), (-4, 3))):
            ground.create_shape(wall, b2d.segment(p, q))

    def create_belts(self):
        ground = self.world.create_static_body()
        belt_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.SlateGray)
        )
        self.belts = []
        for x, y, direction in BELTS:
            box = b2d.box(6.0, 0.2, center=(x, y), rotation=-direction * BELT_TILT)
            self.belts.append((ground.create_shape(belt_def, box), direction))

    def build_emitter(self):
        # the crate geometry is fixed per emitter: a new size needs a new emitter
        if self.crates is not None:
            self.crates.clear()
        # the hopper: a line above the top belt, from right to left (its left normal points down)
        self.crates = ext.LinearEmitter(
            self.world,
            b2d.shape_def(density=1.0, material=b2d.surface_material(friction=0.6)),
            b2d.box(self.size, self.size),
            p1=(6.0, 20.0),
            p2=(2.0, 20.0),
            seed=5,
            rate=self.rate,
            capacity=150,
            speed=ext.uniform(0.0, 1.0),
            lifetime=math.inf,
            on_capacity_reached=ext.OnCapacityReached.DESTROY_OLDEST,
        )

    def set_rate(self, value):
        self.rate = self.crates.rate = value

    def set_size(self, value):
        self.size = value
        self.build_emitter()

    def set_belt_speed(self, value):
        for shape, direction in self.belts:
            material = shape.surface_material
            material.tangent_speed = direction * value
            shape.surface_material = material

    def pre_update(self, dt):
        self.crates.step(dt)
        if len(self.crates):
            # one color per crate, by its age: fresh ones bright, old ones dark
            shade = np.clip(1.0 - self.crates.ages / FADE_TIME, 0.35, 1.0)
            hue = np.full(len(shade), CRATE_HUE)
            colors = hsv_colors(hue, CRATE_SATURATION, CRATE_VALUE * shade)
            self.crates.shapes.custom_color = colors

    def post_debug_draw(self):
        self.debug_draw.draw_string((-15.0, 21.0), f"{len(self.crates)} crates", b2d.HexColor.White)
