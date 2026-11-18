"""A spinning nozzle in zero gravity, in a box: straight jets that draw spiral arms."""

import math

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

WALL, DROP, THING = 0x1, 0x2, 0x4  # collision categories
HALF = 18.0  # half size of the box
# one color ramp per arm, by age
RAMPS = [
    [(0.0, 0xFFFFFF), (0.3, color), (1.0, 0x101018)] for color in (0x5AC8FA, 0xFF2D55, 0xFFCC00)
]


@register_sample("Emitters", "Spiral", video=True)
class Spiral(SampleBase):
    """Three emitters on a spinning hub, zero gravity: each drop flies straight, the turning
    nozzles lay them out as spiral arms. Drops bounce off the walls and push the floating
    things. Mouse: drag them. Sliders: spin, jet speed, rate; whether drops collide.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.speed = 6.0
        self.rate = 60.0
        self.self_collide = False
        self.arms = []
        self.create_box()
        self.create_things()
        self.create_hub()
        self.create_arms()
        for widget in (
            widgets.FloatSlider("spin (rad/s)", -4.0, 4.0, 0.1, 1.0, self.set_spin),
            widgets.FloatSlider("jet speed", 1.0, 15.0, 0.5, self.speed, self.set_speed),
            widgets.FloatSlider("rate (1/s)", 5.0, 200.0, 5.0, self.rate, self.set_rate),
            widgets.Checkbox("drops collide", self.self_collide, self.set_self_collide),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-HALF - 1, -HALF - 1), upper_bound=(HALF + 1, HALF + 1))

    def create_box(self):
        box = self.world.create_static_body()
        corners = [
            (-HALF, -HALF),
            (-HALF, HALF),
            (HALF, HALF),
            (HALF, -HALF),
        ]  # clockwise: the walls face inwards
        box.create_chain(
            b2d.chain_def(
                points=corners,
                is_loop=True,
                filter=b2d.make_filter(category_bits=WALL, mask_bits=0xFFFF),
                material=b2d.surface_material(restitution=0.8, custom_color=b2d.HexColor.DimGray),
            )
        )

    def create_things(self):
        thing_def = b2d.shape_def(
            density=0.5,
            filter=b2d.make_filter(category_bits=THING, mask_bits=0xFFFF),
            material=b2d.surface_material(restitution=0.5, custom_color=b2d.HexColor.Peru),
        )
        for x, y in ((-10.0, 9.0), (11.0, -8.0), (8.0, 12.0)):
            crate = self.world.create_dynamic_body(position=(x, y), angular_damping=0.5)
            crate.create_shape(thing_def, b2d.box(1.2, 1.2))
        for x, y in ((-9.0, -11.0), (13.0, 3.0), (-14.0, 0.0)):
            ball = self.world.create_dynamic_body(position=(x, y))
            ball.create_shape(thing_def, b2d.circle(radius=1.0))

    def create_hub(self):
        self.hub = self.world.create_kinematic_body(position=(0.0, 0.0), angular_velocity=1.0)
        self.hub.create_shape(
            b2d.shape_def(
                filter=b2d.make_filter(category_bits=WALL, mask_bits=0xFFFF),
                material=b2d.surface_material(custom_color=b2d.HexColor.DimGray),
            ),
            b2d.circle(radius=0.6),
        )

    def create_arms(self):
        """the three emitters; the drops collide with each other only if `self_collide`
        (the shape def of an emitter is fixed: a change builds new emitters)"""
        for arm in self.arms:
            arm.clear()
        mask = WALL | THING | (DROP if self.self_collide else 0)
        drop_def = b2d.shape_def(
            density=1.0,
            filter=b2d.make_filter(category_bits=DROP, mask_bits=mask),
            material=b2d.surface_material(restitution=0.8, friction=0.0),
        )
        self.arms = [
            ext.RadialEmitter(
                self.world,
                drop_def,
                b2d.circle(radius=0.12),
                body=self.hub,
                local_frame=b2d.transform((0.0, 0.0), b2d.make_rot(2.0 * math.pi * i / len(RAMPS))),
                seed=i,
                rate=self.rate,
                capacity=1000,
                radius=0.75,  # just outside the hub
                speed=self.speed,
                lifetime=5.0,
                colors=ramp,
            )
            for i, ramp in enumerate(RAMPS)
        ]

    def set_spin(self, value):
        self.hub.angular_velocity = value

    def set_speed(self, value):
        self.speed = value
        for arm in self.arms:
            arm.speed = value

    def set_rate(self, value):
        self.rate = value
        for arm in self.arms:
            arm.rate = value

    def set_self_collide(self, value):
        self.self_collide = value
        self.create_arms()

    def pre_update(self, dt):
        for arm in self.arms:
            arm.step(dt)  # (a kinematic hub: the reaction cannot turn it)
