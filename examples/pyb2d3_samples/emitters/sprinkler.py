"""A lawn sprinkler, turned only by the reaction of its own jets."""

import math

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

HUB = (0.0, 6.0)
ARM = 2.0  # half length of the arm: the jets sit at its ends
DROP_RADIUS = 0.08
DROP_DENSITY = 1.0
WATER = [(0.0, 0xBFE9FF), (1.0, 0x1E5AA8)]  # color by age


@register_sample("Emitters", "Sprinkler", video=True)
class Sprinkler(SampleBase):
    """A sprinkler: two jets on the ends of an arm on a pin; the arm turns only because of
    the jets' reaction (the angular impulse step returns). The water fills a basin.
    Sliders: jet speed, rate, friction of the pin.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.create_basin()
        self.create_rotor()
        self.create_jets()
        for widget in (
            widgets.FloatSlider("jet speed", 2.0, 14.0, 0.5, 7.5, self.set_speed),
            widgets.FloatSlider("rate (1/s)", 10.0, 300.0, 10.0, 120.0, self.set_rate),
            widgets.FloatSlider("pin friction", 0.0, 20.0, 0.5, 4.0, self.set_friction),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-13.0, -1.0), upper_bound=(13.0, 14.0))

    def create_basin(self):
        self.basin = self.world.create_static_body()
        wall = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.DimGray))
        for p, q in (((-12, 8), (-12, 0)), ((-12, 0), (12, 0)), ((12, 0), (12, 8))):
            self.basin.create_shape(wall, b2d.segment(p, q))
        self.basin.create_shape(wall, b2d.box(0.2, 0.5 * HUB[1], center=(0.0, 0.5 * HUB[1])))

    def create_rotor(self):
        self.rotor = self.world.create_dynamic_body(position=HUB)
        self.rotor.create_shape(
            b2d.shape_def(
                density=2.0,
                filter=b2d.make_filter(category_bits=0x2, mask_bits=0x0),  # touches nothing
                material=b2d.surface_material(custom_color=b2d.HexColor.Silver),
            ),
            b2d.box(ARM, 0.12),
        )
        # the pin, with a little friction (a motor that wants speed 0)
        self.pin = self.world.create_revolute_joint(
            self.basin, self.rotor, local_anchor_a=HUB, enable_motor=True, max_motor_torque=4.0
        )

    def create_jets(self):
        drop_def = b2d.shape_def(
            density=DROP_DENSITY, material=b2d.surface_material(friction=0.1, restitution=0.1)
        )
        # the jets point along the arm's turning direction: their reaction turns it backwards
        self.jets = [
            ext.RadialEmitter(
                self.world,
                drop_def,
                b2d.circle(radius=DROP_RADIUS),
                body=self.rotor,
                local_frame=b2d.transform(
                    (side * ARM, 0.0), b2d.make_rot(side * 0.5 * math.pi + 0.4)
                ),
                seed=side + 2,
                rate=120.0,
                capacity=700,
                angle_min=-0.06,
                angle_max=0.06,
                speed=ext.uniform(7.0, 8.0),
                lifetime=ext.uniform(4.0, 6.0),
                max_lifetime=6.0,
                colors=WATER,
            )
            for side in (1, -1)
        ]

    def set_speed(self, value):
        for jet in self.jets:
            jet.speed = ext.uniform(value - 0.5, value + 0.5)

    def set_rate(self, value):
        for jet in self.jets:
            jet.rate = value

    def set_friction(self, value):
        self.pin.max_motor_torque = value

    def pre_update(self, dt):
        drop_mass = DROP_DENSITY * math.pi * DROP_RADIUS**2
        omega = self.rotor.angular_velocity
        for jet in self.jets:
            impulse, angular_impulse = jet.step(dt)
            # the new drops leave with the arm's tip velocity: in a real sprinkler the arm
            # had to speed that water up (it enters at the hub), a drag that limits the spin
            new_drops = (jet.ages == 0.0).sum()
            angular_impulse -= new_drops * drop_mass * omega * ARM**2
            self.rotor.apply_linear_impulse_to_center(impulse)  # (the pin holds it)
            self.rotor.apply_angular_impulse(angular_impulse)  # this turns the arm

    def post_debug_draw(self):
        rpm = self.rotor.angular_velocity * 60.0 / (2.0 * math.pi)
        self.debug_draw.draw_string((-11.5, 13.0), f"{rpm:5.1f} rpm", b2d.HexColor.White)
