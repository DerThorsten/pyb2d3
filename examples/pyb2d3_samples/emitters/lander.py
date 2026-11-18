"""A lander flown by its exhaust: the thrust is the reaction of the emitted particles."""

import math

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

WORLD, LANDER, EXHAUST, PEBBLE = 0x1, 0x2, 0x4, 0x8  # collision categories
START = (-10.0, 18.0)
# key, nozzle position and direction on the lander, exhaust speed, spread, full rate: the main
# engine points down, the side thrusters on the upper corners point sideways (and a bit up)
ENGINES = [
    ("w", (0.0, -0.6), -0.5 * math.pi, 16.0, 0.12, 400.0),
    ("a", (0.9, 0.5), 0.3, 10.0, 0.1, 120.0),  # the right thruster pushes to the left
    ("d", (-0.9, 0.5), math.pi - 0.3, 10.0, 0.1, 120.0),
]
FLAME = [(0.0, 0xFFF3B0), (0.25, 0xFF8C00), (0.6, 0xB03A00), (1.0, 0x404040)]  # by age


@register_sample("Emitters", "Lander")
class Lander(SampleBase):
    """A lander: its main engine and two side thrusters are emitters, the thrust is the
    reaction of the exhaust (what step returns). Land softly on the pad.
    Keys: w main engine, a / d steer (side thrusters), r restart.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.throttle = 1.0
        self.create_ground()
        self.create_pebbles()
        self.create_lander()
        self.create_engines()
        for widget in (
            widgets.FloatSlider("throttle", 0.2, 1.0, 0.05, self.throttle, self.set_throttle),
            widgets.Button("restart (r)", self.restart),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-20.0, -1.0), upper_bound=(20.0, 24.0))

    def create_ground(self):
        ground = self.world.create_static_body()
        shape_def = b2d.shape_def(
            filter=b2d.make_filter(category_bits=WORLD, mask_bits=0xFFFF),
            material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.DimGray),
        )
        points = [(-20, 4), (-14, 2), (-9, 3), (-4, 0), (4, 0), (9, 2.5), (14, 1.5), (20, 5)]
        for p, q in zip(points[:-1], points[1:]):
            ground.create_shape(shape_def, b2d.segment(p, q))
        pad_def = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.Gold))
        ground.create_shape(pad_def, b2d.box(2.0, 0.1, center=(0.0, 0.1)))

    def create_pebbles(self):
        # loose pebbles on both sides of the pad: the exhaust blows them away
        pebble_def = b2d.shape_def(
            density=0.5,
            filter=b2d.make_filter(category_bits=PEBBLE, mask_bits=0xFFFF),
            material=b2d.surface_material(friction=0.6, custom_color=b2d.HexColor.Tan),
        )
        for i in range(24):
            x = -3.6 + 0.3 * i + (0.0 if i < 12 else 0.6)
            if abs(x) > 2.1:
                body = self.world.create_dynamic_body(position=(x, 0.2))
                body.create_shape(pebble_def, b2d.circle(radius=0.12))

    def create_lander(self):
        self.lander = self.world.create_dynamic_body(position=START, angular_damping=2.0)
        hull_def = b2d.shape_def(
            density=1.0,
            filter=b2d.make_filter(category_bits=LANDER, mask_bits=WORLD | PEBBLE),
            material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.LightSteelBlue),
        )
        self.lander.create_shape(hull_def, b2d.box(0.9, 0.6))
        for side in (-1.0, 1.0):  # legs
            self.lander.create_shape(
                hull_def, b2d.box(0.08, 0.5, center=(side * 0.9, -0.8), rotation=side * 0.3)
            )
            self.lander.create_shape(hull_def, b2d.box(0.3, 0.06, center=(side * 1.1, -1.25)))

    def create_engines(self):
        # exhaust: hits the world and pebbles, not itself (cheap) and not the lander
        exhaust_def = b2d.shape_def(
            density=0.4,
            filter=b2d.make_filter(category_bits=EXHAUST, mask_bits=WORLD | PEBBLE),
            material=b2d.surface_material(restitution=0.3, friction=0.2),
        )
        self.engines = []  # (emitter, key, full rate)
        for key, position, angle, speed, spread, full_rate in ENGINES:
            emitter = ext.RadialEmitter(
                self.world,
                exhaust_def,
                b2d.circle(radius=0.08),
                body=self.lander,
                local_frame=b2d.transform(position, b2d.make_rot(angle)),
                rate=self.throttle * full_rate,
                enabled=False,  # fires while its key is held
                capacity=600,
                angle_min=-spread,
                angle_max=spread,
                speed=ext.uniform(0.9 * speed, 1.1 * speed),
                lifetime=ext.normal(0.7, 0.2),
                max_lifetime=1.2,
                colors=FLAME,
            )
            self.engines.append((emitter, key, full_rate))

    def set_throttle(self, value):
        self.throttle = value
        for emitter, _, full_rate in self.engines:
            emitter.rate = value * full_rate

    def restart(self):
        for emitter, _, _ in self.engines:
            emitter.clear()
        self.lander.set_transform(START, b2d.make_rot(0.0))
        self.lander.linear_velocity = (0.0, 0.0)
        self.lander.angular_velocity = 0.0

    def on_key_down(self, event):
        if event.key == "r":
            self.restart()

    def pre_update(self, dt):
        for emitter, key, _ in self.engines:
            emitter.enabled = self.is_key_pressed(key)
            # the thrust: the reaction of this step's exhaust
            impulse, angular_impulse = emitter.step(dt)
            self.lander.apply_linear_impulse_to_center(impulse)
            self.lander.apply_angular_impulse(angular_impulse)

    def post_debug_draw(self):
        v = self.lander.linear_velocity
        speed = math.hypot(v.x, v.y)
        color = b2d.HexColor.LightGreen if speed < 2.0 else b2d.HexColor.OrangeRed
        self.debug_draw.draw_string((-19.0, 23.0), f"speed {speed:4.1f} m/s", color)
