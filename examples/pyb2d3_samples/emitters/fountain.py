"""A fountain: a radial emitter (narrow upward cone) and a few batch calls on its particles.

The emitter creates the drops and expires them after their lifetime; a mask over
`particles` drains the ones that came to rest or left the basin, wind drags all of them with
one `apply_force_to_center`, and `shapes.custom_color` colors them by speed in one call.
"""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from ..examples_common.batch import hsv_colors

NOZZLE = (0.0, 4.0)
REST_SPEED = 1.5  # drops slower than this (and older than a second) drain away
WIND_DRAG = 0.6  # 1 / s

# speed bands -> colors (slow: deep blue ... fast: white-ish cyan)
SPEED_BANDS = np.array([3.0, 6.0, 10.0, 15.0])
BAND_COLORS = hsv_colors(
    np.linspace(0.66, 0.5, len(SPEED_BANDS) + 1),
    np.linspace(0.9, 0.2, len(SPEED_BANDS) + 1),
    1.0,
)


@register_sample("Emitters", "Fountain", video=True)
class Fountain(SampleBase):
    """A fountain: a radial emitter shooting drops upward; resting drops drain away, wind
    blows them sideways, the color shows the speed.
    Sliders: rate, capacity, jet speed, spread, wind.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.wind = 0.0
        self.create_basin()
        self.create_emitter()
        self.create_widgets()

    def aabb(self):
        return b2d.aabb(lower_bound=(-22.0, -4.0), upper_bound=(22.0, 32.0))

    def create_basin(self):
        # the nozzle sits on a column; sloped basins on both sides run off into drains
        ground = self.world.create_static_body()
        shape_def = b2d.shape_def(material=b2d.surface_material(friction=0.2))
        h = NOZZLE[1]
        ground.create_shape(shape_def, b2d.box(0.5, 0.5 * h - 0.2, center=(0.0, 0.5 * h - 0.4)))
        for side in (-1.0, 1.0):
            ground.create_shape(shape_def, b2d.segment((side * 0.5, 2.5), (side * 14.0, 0.0)))
            ground.create_shape(shape_def, b2d.segment((side * 16.0, -1.0), (side * 20.0, 7.0)))

    def create_emitter(self):
        # the emitter's x axis points up: angles are measured from the vertical
        self.drops = ext.RadialEmitter(
            self.world,
            b2d.shape_def(
                density=1.0,
                material=b2d.surface_material(
                    restitution=0.2, friction=0.1, custom_color=int(BAND_COLORS[0])
                ),
            ),
            b2d.circle(radius=0.15),
            seed=3,
            transform=b2d.transform(NOZZLE, b2d.make_rot(0.5 * math.pi)),
            rate=250.0,
            capacity=1000,
            lifetime=7.0,
        )
        self.set_jet_speed(20.0)
        self.set_spread(8.0)

    def create_widgets(self):
        for widget in (
            widgets.FloatSlider("rate (1/s)", 20.0, 1000.0, 10.0, 250.0, self.set_rate),
            widgets.IntSlider("capacity", 200, 4000, 100, 1000, self.set_capacity),
            widgets.FloatSlider("jet speed", 5.0, 35.0, 1.0, 20.0, self.set_jet_speed),
            widgets.FloatSlider("spread (deg)", 0.0, 30.0, 1.0, 8.0, self.set_spread),
            widgets.FloatSlider("wind", -15.0, 15.0, 0.5, self.wind, self.set_wind),
        ):
            self.frontend.add_widget(widget)

    def set_rate(self, value):
        self.drops.rate = value

    def set_capacity(self, value):
        self.drops.capacity = int(value)

    def set_jet_speed(self, value):
        self.drops.speed = ext.uniform(0.9 * value, 1.05 * value)

    def set_spread(self, degrees):
        self.drops.angle_min = -math.radians(degrees)
        self.drops.angle_max = math.radians(degrees)

    def set_wind(self, value):
        self.wind = value

    def pre_update(self, dt):
        self.drops.step(dt)  # (no owner body: the reaction is not used)
        drops = self.drops.particles
        if not len(drops):
            return
        # drain: drops that came to rest (the puddle) or left the basin
        speed = drops.speed
        resting = (self.drops.ages > 1.0) & (speed < REST_SPEED)
        drained = resting | (drops.position[:, 1] < -5.0)
        drops[drained].destroy()  # the emitter forgets them on its next step
        if self.wind != 0.0:  # no wind: no air drag either
            relative = np.array([self.wind, 0.0]) - drops.linear_velocity
            drops.apply_force_to_center(WIND_DRAG * drops.mass[:, None] * relative)
        # color by speed band, all drops in one call
        self.drops.shapes.custom_color = BAND_COLORS[np.searchsorted(SPEED_BANDS, speed)]

    def post_debug_draw(self):
        dd = self.debug_draw
        dd.draw_point(NOZZLE, 10.0, b2d.HexColor.LightSkyBlue)
        if self.wind != 0.0:
            arrow = (8.0 + 0.4 * self.wind, 28.0)
            dd.draw_segment((8.0, 28.0), arrow, b2d.HexColor.LightGray)
            dd.draw_point(arrow, 6.0, b2d.HexColor.LightGray)
        text = f"{len(self.drops)} / {self.drops.capacity} drops"
        dd.draw_string((0.0, 30.0), text, b2d.HexColor.White)
