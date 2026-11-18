"""Rain and sand from a line emitter over bumpy terrain."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

RAIN, SAND = "rain", "sand"


@register_sample("Emitters", "Rain & Sand", video=True)
class RainAndSand(SampleBase):
    """A line emitter over bumpy terrain: rain from the whole line, or sand from a narrow
    spot of it (a normal distribution along the line) that heaps up.
    Mouse: drag the crates into the stream. Sliders: rate, where the sand pours.
    """

    width = 20.0
    height = 18.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.mode = SAND
        self.rate = 150.0
        self.spot = 0.5
        self.create_terrain()
        self.create_crates()
        self.emitter = None
        self.build_emitter()

        for widget in (
            widgets.RadioButtons("what", [RAIN, SAND], self.mode, self.set_mode),
            widgets.FloatSlider("rate (1/s)", 20.0, 800.0, 10.0, self.rate, self.set_rate),
            widgets.FloatSlider("sand spot", 0.05, 0.95, 0.01, self.spot, self.set_spot),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.width, -1.0), upper_bound=(self.width, self.height + 1.0)
        )

    def create_terrain(self):
        x = np.linspace(-self.width, self.width, 81)
        y = 1.5 + 1.2 * np.sin(0.45 * x) + 0.6 * np.sin(1.3 * x + 1.0)
        points = [(-self.width, self.height), *zip(x, y), (self.width, self.height)]
        ground = self.world.create_static_body()
        ground.create_chain(
            b2d.chain_def(
                points=points[::-1],  # (the solid side of a chain is to its right)
                material=b2d.surface_material(
                    friction=0.8, custom_color=b2d.HexColor.DarkOliveGreen
                ),
            )
        )

    def create_crates(self):
        crate = b2d.shape_def(
            density=1.0, material=b2d.surface_material(custom_color=b2d.HexColor.Peru)
        )
        for x in (-8.0, 6.0, 10.0):
            body = self.world.create_dynamic_body(position=(x, 6.0))
            body.create_shape(crate, b2d.box(0.8, 0.8))

    def build_emitter(self):
        # rain and sand differ in almost every setting: a new emitter per mode
        if self.emitter is not None:
            self.emitter.clear()
        rain = self.mode == RAIN
        shape_def = b2d.shape_def(
            density=1.0,
            material=b2d.surface_material(
                friction=0.1 if rain else 0.9,
                restitution=0.3 if rain else 0.0,
                custom_color=b2d.HexColor.LightSkyBlue if rain else b2d.HexColor.SandyBrown,
            ),
        )
        # the line from right to left: its left normal points down
        y = self.height - 0.5
        self.emitter = ext.LinearEmitter(
            self.world,
            shape_def,
            b2d.circle(radius=0.07 if rain else 0.1),
            p1=(self.width - 0.5, y),
            p2=(-self.width + 0.5, y),
            rate=self.rate,
            capacity=1500 if rain else 2500,
            # (sand: fast enough that new grains do not overlap in the stream)
            speed=ext.uniform(4.0, 6.0) if rain else 4.0,
            lifetime=ext.uniform(2.5, 4.0) if rain else math.inf,
            on_capacity_reached=ext.OnCapacityReached.DESTROY_OLDEST,
        )
        self.set_spot(self.spot)

    def set_mode(self, value):
        self.mode = value
        self.build_emitter()

    def set_rate(self, value):
        self.rate = self.emitter.rate = value

    def set_spot(self, value):
        self.spot = value
        # rain from the whole line, sand from a narrow spot (t in [0, 1]: 0 is the right end)
        self.emitter.along = (
            ext.uniform(0.0, 1.0) if self.mode == RAIN else ext.normal(1.0 - value, 0.03)
        )

    def pre_update(self, dt):
        self.emitter.step(dt)

    def post_debug_draw(self):
        text = f"{len(self.emitter)} {'drops' if self.mode == RAIN else 'grains'}"
        self.debug_draw.draw_string(
            (-self.width + 0.5, self.height + 0.5), text, b2d.HexColor.White
        )
