"""Fireworks: a launcher emitter fires shells, each bursts into sparks colored by their age."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

WORLD, SHELL, SPARK = 0x1, 0x2, 0x4  # collision categories
FUSE = 1.3  # s, from the launch to the burst
GRAVITY = 10.0
LAUNCH_SPEED = ext.uniform(15.0, 19.0)
# one spark emitter per palette: white-hot, then the color, then dark (colors by age)
PALETTES = [
    [(0.0, 0xFFFFFF), (0.2, color), (0.8, color), (1.0, 0x202020)]
    for color in (0xFF3B30, 0x34C759, 0x0A84FF, 0xFFD60A, 0xBF5AF2, 0xFF9F0A)
]


@register_sample("Emitters", "Fireworks", video=True)
class Fireworks(SampleBase):
    """Fireworks: a launcher (an emitter) fires shells; when a shell's fuse burns out, a
    spark emitter bursts at its position, the sparks change color with their age.
    Mouse: double click to fire a shell there. Sliders: launch rate, sparks per shell.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -GRAVITY)))
        self.rng = np.random.default_rng(7)
        self.sparks_per_shell = 120
        self.interval = 0.6  # s between two automatic shells
        self.timer = self.interval  # the first shell right away
        self.next_burst = 0  # the spark emitters take turns
        self.create_ground()
        self.create_launcher()
        self.create_spark_emitters()
        for widget in (
            widgets.FloatSlider("shells / s", 0.2, 5.0, 0.1, 1.0 / self.interval, self.set_rate),
            widgets.IntSlider(
                "sparks / shell", 20, 400, 10, self.sparks_per_shell, self.set_sparks
            ),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-20.0, -1.0), upper_bound=(20.0, 24.0))

    def create_ground(self):
        ground = self.world.create_static_body()
        ground.create_shape(
            b2d.shape_def(filter=b2d.make_filter(category_bits=WORLD, mask_bits=0xFFFF)),
            b2d.segment((-30.0, 0.0), (30.0, 0.0)),
        )

    def create_launcher(self):
        # shells: from the ground, up (the emitter's x axis points up); launch() moves it
        self.launcher = ext.RadialEmitter(
            self.world,
            b2d.shape_def(
                density=1.0,
                filter=b2d.make_filter(category_bits=SHELL, mask_bits=WORLD),
                material=b2d.surface_material(custom_color=b2d.HexColor.Orange),
            ),
            b2d.circle(radius=0.12),
            rate=0.0,  # shells only by burst
            capacity=50,
            angle_min=-0.15,
            angle_max=0.15,
            speed=LAUNCH_SPEED,
            lifetime=10.0,
        )

    def create_spark_emitters(self):
        spark_def = b2d.shape_def(
            density=1.0,
            filter=b2d.make_filter(category_bits=SPARK, mask_bits=WORLD),  # not each other
            material=b2d.surface_material(restitution=0.3),
        )
        self.bursts = [
            ext.RadialEmitter(
                self.world,
                spark_def,
                b2d.circle(radius=0.1),
                body_def=b2d.body_def(gravity_scale=0.35, linear_damping=0.8),
                seed=i,
                rate=0.0,  # sparks only by burst
                capacity=1500,
                angle_min=-math.pi,
                angle_max=math.pi,
                speed=ext.uniform(3.0, 7.0),
                lifetime=ext.normal(1.6, 0.4),
                max_lifetime=2.5,
                colors=palette,
            )
            for i, palette in enumerate(PALETTES)
        ]

    def set_rate(self, value):
        self.interval = 1.0 / value

    def set_sparks(self, value):
        self.sparks_per_shell = int(value)

    def on_double_click(self, event):
        x, y = event.world_position
        # the speed that carries a shell to about that height within its fuse
        self.launch(x, speed=max(5.0, (y + 0.5 * GRAVITY * FUSE**2) / FUSE))

    def launch(self, x, speed=LAUNCH_SPEED):
        self.launcher.transform = b2d.transform((x, 0.2), b2d.make_rot(0.5 * math.pi))
        self.launcher.speed = speed
        self.launcher.burst(1)

    def burst(self, position):
        emitter = self.bursts[self.next_burst]
        self.next_burst = (self.next_burst + 1) % len(self.bursts)
        emitter.transform = b2d.transform(tuple(position))
        emitter.burst(self.sparks_per_shell)

    def pre_update(self, dt):
        self.timer += dt
        if self.timer >= self.interval:
            self.timer = 0.0
            self.launch(float(self.rng.uniform(-10.0, 10.0)))
        self.launcher.step(dt)
        # shells whose fuse burnt out: sparks there, the shell is gone
        shells = self.launcher.particles
        burnt = self.launcher.ages >= FUSE
        if burnt.any():
            for position in shells[burnt].position:
                self.burst(position)
            shells[burnt].destroy()
        for emitter in self.bursts:
            emitter.step(dt)

    def post_debug_draw(self):
        sparks = sum(len(e) for e in self.bursts)
        self.debug_draw.draw_string((-19.0, 23.0), f"{sparks} sparks", b2d.HexColor.White)
