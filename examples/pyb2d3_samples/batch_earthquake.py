"""An earthquake shakes a city of block towers; fallen blocks are counted with numpy."""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import Shaker, destroy_bodies, hsv_colors


class BatchEarthquake(SampleBase):
    """A city of block towers on a ground plate that shakes like an earthquake.

    Keys: space starts / stops the quake.
    Sliders: magnitude (amplitude) and frequency of the quake; "rebuild" puts the
    city back up.
    Hint: tall slim towers resonate at low frequencies, short wide ones at high;
    a block counts as fallen when it dropped more than half its height.
    """

    block = (0.4, 0.2)  # half extents
    ground_half_width = 30.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.magnitude = 0.12  # the city collapses over ~10 s; more is instant
        self.frequency = 1.5
        self.quaking = False
        self.time = 0.0
        self.rng = np.random.default_rng(11)
        self.blocks = b2d.Bodies()
        self.ground = self.world.create_kinematic_body(position=(0.0, 0.0), enable_sleep=False)
        ground_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.SaddleBrown)
        )
        self.ground.create_shape(
            ground_def, b2d.box(self.ground_half_width, 0.5, center=(0.0, -0.5))
        )
        self.shaker = Shaker(self.ground, axis=(1.0, 0.25), amplitude=0.0, frequency=self.frequency)
        self.build()
        for widget in (
            widgets.Button("quake on / off", self.toggle),
            widgets.FloatSlider("magnitude", 0.02, 0.6, 0.02, self.magnitude, self.set_magnitude),
            widgets.FloatSlider(
                "frequency (Hz)", 0.3, 5.0, 0.1, self.frequency, self.set_frequency
            ),
            widgets.Button("rebuild", self.build),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.ground_half_width, -2.0), upper_bound=(self.ground_half_width, 22.0)
        )

    def build(self):
        destroy_bodies(self, self.blocks)
        self.quaking = False
        self.shaker.amplitude = 0.0
        hx, hy = self.block
        blocks = b2d.Bodies()
        positions = []
        x = -self.ground_half_width + 2.0
        k = 0
        while x < self.ground_half_width - 2.0:
            width = int(self.rng.integers(1, 4))  # blocks side by side
            floors = int(
                self.rng.integers(3, 7 * width + 3)
            )  # slim towers stay short: they stand when calm
            color = int(hsv_colors(0.55 + 0.1 * self.rng.random(), 0.35, 0.9))
            material = b2d.surface_material(friction=0.6, custom_color=color)
            shape_def = b2d.shape_def(density=1.0, material=material)
            for floor in range(floors):
                y = (2 * floor + 1) * hy
                # brick bond: odd floors shifted by half a block, with half blocks at
                # both ends (a full block on a half one tips over)
                if floor % 2 and width > 1:
                    bricks = [(x + 0.5 * hx, 0.5 * hx), (x + (2 * width - 0.5) * hx, 0.5 * hx)]
                    bricks += [(x + 2 * (column + 1) * hx, hx) for column in range(width - 1)]
                else:
                    bricks = [(x + (2 * column + 1) * hx, hx) for column in range(width)]
                for bx, half in bricks:
                    body = self.world.create_dynamic_body(position=(bx, y))
                    body.create_shape(shape_def, b2d.box(half, hy))
                    blocks.append(body)
                    positions.append((bx, y))
            x += 2 * width * hx + 1.2
            k += 1
        self.blocks = blocks
        self.start_height = np.array(positions)[:, 1]

    def toggle(self):
        self.quaking = not self.quaking

    def on_key_down(self, event):
        if event.key == "space":
            self.toggle()

    def set_magnitude(self, value):
        self.magnitude = value

    def set_frequency(self, value):
        self.shaker.frequency = value

    def pre_update(self, dt):
        # ramp the amplitude: switching on / off mid-swing must not jerk the ground
        target = self.magnitude if self.quaking else 0.0
        self.shaker.amplitude += float(np.clip(target - self.shaker.amplitude, -0.5 * dt, 0.5 * dt))
        self.shaker.step(self.time, dt)
        self.time += dt

    def post_debug_draw(self):
        fallen = int(
            np.count_nonzero(self.blocks.position[:, 1] < self.start_height - self.block[1])
        )
        state = (
            f"quake {self.shaker.amplitude:.2f} @ {self.shaker.frequency:.1f} Hz"
            if self.quaking
            else "calm"
        )
        text = f"{state}   fallen blocks {fallen} / {len(self.blocks)}"
        self.debug_draw.draw_string((-self.ground_half_width + 1.0, 20.5), text, b2d.HexColor.White)
