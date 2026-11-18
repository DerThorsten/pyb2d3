"""An earthquake shakes a city of block towers; fallen blocks are counted with numpy."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import hsv_colors

BLOCK = (0.4, 0.2)  # half extents
GROUND_HALF_WIDTH = 30.0
SHAKE_AXIS = np.array([1.0, 0.25]) / math.hypot(1.0, 0.25)
RAMP_SPEED = 0.5  # amplitude change per second when the quake starts / stops


@register_sample("Granular", "Earthquake City", video=True)
class BatchEarthquake(SampleBase):
    """A city of block towers on a shaking ground plate.
    Keys: space starts / stops the quake.
    Sliders: magnitude, frequency; "rebuild".
    Hint: tall slim towers fall at low frequencies, short wide ones at high.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.magnitude = 0.12  # the city collapses over ~10 s; more is instant
        self.frequency = 1.5
        self.amplitude = 0.0
        self.quaking = False
        self.time = 0.0
        self.rng = np.random.default_rng(11)
        self.blocks = b2d.Bodies()  # all blocks of all towers
        self.create_ground()
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
            lower_bound=(-GROUND_HALF_WIDTH, -2.0), upper_bound=(GROUND_HALF_WIDTH, 22.0)
        )

    def create_ground(self):
        """a kinematic plate: moved by setting its target position every step"""
        self.ground = self.world.create_kinematic_body(position=(0.0, 0.0), enable_sleep=False)
        ground_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.SaddleBrown)
        )
        self.ground.create_shape(ground_def, b2d.box(GROUND_HALF_WIDTH, 0.5, center=(0.0, -0.5)))

    def build(self):
        """a row of towers of random width and height"""
        self.blocks.destroy()
        self.blocks = b2d.Bodies()
        self.quaking = False
        self.amplitude = 0.0
        x = -GROUND_HALF_WIDTH + 2.0
        while x < GROUND_HALF_WIDTH - 2.0:
            width = int(self.rng.integers(1, 4))  # blocks side by side
            floors = int(self.rng.integers(3, 7 * width + 3))  # slim towers stay short
            self.create_tower(x, width, floors)
            x += 2 * width * BLOCK[0] + 1.2
        self.start_height = self.blocks.position[:, 1]

    def create_tower(self, x, width, floors):
        hx, hy = BLOCK
        color = int(hsv_colors(0.55 + 0.1 * self.rng.random(), 0.35, 0.9))
        material = b2d.surface_material(friction=0.6, custom_color=color)
        shape_def = b2d.shape_def(density=1.0, material=material)
        for floor in range(floors):
            y = (2 * floor + 1) * hy
            # brick bond: odd floors are shifted by half a block, with half blocks at
            # both ends (a full block on a half one tips over)
            if floor % 2 and width > 1:
                bricks = [(x + 0.5 * hx, 0.5 * hx), (x + (2 * width - 0.5) * hx, 0.5 * hx)]
                bricks += [(x + 2 * (column + 1) * hx, hx) for column in range(width - 1)]
            else:
                bricks = [(x + (2 * column + 1) * hx, hx) for column in range(width)]
            for bx, half_width in bricks:
                body = self.world.create_dynamic_body(position=(bx, y))
                body.create_shape(shape_def, b2d.box(half_width, hy))
                self.blocks.append(body)

    def toggle(self):
        self.quaking = not self.quaking

    def on_key_down(self, event):
        if event.key == "space":
            self.toggle()

    def set_magnitude(self, value):
        self.magnitude = value

    def set_frequency(self, value):
        self.frequency = value

    def pre_update(self, dt):
        # ramp the amplitude: switching on / off mid-swing must not jerk the ground
        target = self.magnitude if self.quaking else 0.0
        step = RAMP_SPEED * dt
        self.amplitude += min(max(target - self.amplitude, -step), step)
        # where the ground has to be at the end of this step
        self.time += dt
        offset = self.amplitude * math.sin(2.0 * math.pi * self.frequency * self.time)
        position = tuple(offset * SHAKE_AXIS)
        self.ground.set_target_transform(b2d.transform(p=position), dt, wake=True)

    def post_debug_draw(self):
        fallen = np.count_nonzero(self.blocks.position[:, 1] < self.start_height - BLOCK[1])
        state = f"quake {self.amplitude:.2f} @ {self.frequency:.1f} Hz" if self.quaking else "calm"
        text = f"{state}   fallen blocks {fallen} / {len(self.blocks)}"
        self.debug_draw.draw_string((-GROUND_HALF_WIDTH + 1.0, 20.5), text, b2d.HexColor.White)
