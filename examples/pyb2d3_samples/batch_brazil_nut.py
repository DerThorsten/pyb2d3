"""The Brazil nut effect: shaken mixed grains sort themselves, the big ones rise."""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .batch_common import Shaker, create_circles, destroy_bodies, draw_plot


@register_sample("Granular", "Brazil Nut Shaker")
class BatchBrazilNut(SampleBase):
    """Shaking a box of small grains makes the big "nuts" rise to the top: the
    Brazil nut effect.
    Sliders: amplitude, frequency, nuts.
    Plot: the mean nut height.
    """

    half_width = 5.0
    height = 9.0
    fill_height = 4.5  # a shallow pile: deep ones damp the shaking away
    small_radius = 0.16
    nut_radius = 0.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        # slow long strokes ("taps") that lift the pile: box2d's soft contacts
        # swallow small fast vibrations
        self.amplitude = 0.5
        self.frequency = 2.5
        self.nut_count = 6
        self.rng = np.random.default_rng(7)
        self.time = 0.0
        self.small = b2d.Bodies()
        self.nuts = b2d.Bodies()
        self.history = []
        self.box = self.world.create_kinematic_body(position=(0.0, 0.0), enable_sleep=False)
        wall_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.6, custom_color=b2d.HexColor.SlateGray)
        )
        w, h = self.half_width, self.height
        self.box.create_shape(wall_def, b2d.box(w + 0.3, 0.3, center=(0.0, -0.3)))
        for side in (-1.0, 1.0):
            self.box.create_shape(
                wall_def, b2d.box(0.3, 0.5 * h + 0.3, center=(side * (w + 0.3), 0.5 * h))
            )
        self.shaker = Shaker(
            self.box, axis=(0.0, 1.0), amplitude=self.amplitude, frequency=self.frequency
        )
        self.fill()
        for widget in (
            widgets.FloatSlider("amplitude", 0.0, 1.0, 0.05, self.amplitude, self.set_amplitude),
            widgets.FloatSlider(
                "frequency (Hz)", 0.5, 6.0, 0.1, self.frequency, self.set_frequency
            ),
            widgets.IntSlider("nuts", 1, 12, 1, self.nut_count, self.set_nut_count),
            widgets.Button("refill", self.fill),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.half_width - 2.0, -2.0),
            upper_bound=(self.half_width + 2.0, self.height + 5.0),
        )

    def fill(self):
        destroy_bodies(self, self.small)
        destroy_bodies(self, self.nuts)
        w = self.half_width
        # nuts in a row at the bottom, small grains on a jittered grid above
        xs = np.linspace(-w + 1.0, w - 1.0, self.nut_count) if self.nut_count > 1 else np.zeros(1)
        nuts = np.stack([xs, np.full(self.nut_count, self.nut_radius + 0.05)], axis=1)
        self.nuts = create_circles(
            self.world,
            nuts,
            self.nut_radius,
            colors=int(b2d.HexColor.Orange.value),
            density=1.0,
            friction=0.5,
            enable_sleep=False,
        )
        step = 2.2 * self.small_radius
        gx, gy = np.meshgrid(
            np.arange(-w + step, w - 0.5 * step, step), np.arange(1.1, self.fill_height, step)
        )
        grid = np.stack([gx.ravel(), gy.ravel()], axis=1) + self.rng.uniform(
            -0.01, 0.01, (gx.size, 2)
        )
        self.small = create_circles(
            self.world,
            grid,
            self.small_radius,
            colors=int(b2d.HexColor.Wheat.value),
            density=1.0,
            friction=0.5,
            enable_sleep=False,
        )
        # (no sleeping: a resting pile on a kinematic box would not wake up again)
        self.history = []

    def set_amplitude(self, value):
        self.shaker.amplitude = value

    def set_frequency(self, value):
        self.shaker.frequency = value

    def set_nut_count(self, value):
        self.nut_count = int(value)
        self.fill()

    def pre_update(self, dt):
        self.shaker.step(self.time, dt)
        self.time += dt

    def post_update(self, dt):
        box_y = self.box.position.y
        self.history.append(float(np.mean(self.nuts.position[:, 1])) - box_y)
        del self.history[:-600]

    def post_debug_draw(self):
        if not self.history:
            return
        origin = (self.half_width + 0.8, 0.0)
        draw_plot(
            self.debug_draw,
            origin,
            (4.0, self.height),
            [self.history],
            [b2d.HexColor.Orange],
            y_max=self.height,
        )
        grains_top = float(np.percentile(self.small.position[:, 1], 98)) - self.box.position.y
        self.debug_draw.draw_string(
            (-self.half_width, self.height + 1.5),
            f"nut height {self.history[-1]:.1f}  pile top {grains_top:.1f}",
            b2d.HexColor.White,
        )
