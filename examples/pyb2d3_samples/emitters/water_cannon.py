"""A water cannon on a cart: the jet topples a tower, its recoil pushes the cart back."""

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

WORLD, CART, WATER, CRATE = 0x1, 0x2, 0x4, 0x8  # collision categories
BARREL = 1.2  # the jet starts at the end of the barrel
AIM_SPEED = 0.8  # rad / s while w / s is held
AIM_MIN, AIM_MAX = -0.2, 1.2  # radians above the horizon
DRIVE_SPEED = 8.0  # rad / s of the wheels while a / d is held
DRIVE_TORQUE = 60.0


@register_sample("Emitters", "Water Cannon")
class WaterCannon(SampleBase):
    """A water cannon on a cart shooting at a tower of crates; the recoil (the reaction
    step returns, applied to the cart) rolls the cart back.
    Keys: a / d drive, w / s aim, space toggles the cannon. Sliders: pressure, rate.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.aim = 0.35
        self.create_ground()
        self.create_cart()
        self.create_tower(x=10.0, rows=10)
        self.create_cannon()
        for widget in (
            widgets.FloatSlider("pressure (speed)", 5.0, 30.0, 0.5, 18.0, self.set_speed),
            widgets.FloatSlider("rate (1/s)", 20.0, 500.0, 10.0, self.cannon.rate, self.set_rate),
            widgets.Checkbox("fire (space)", self.cannon.enabled, self.set_firing),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-14.0, -1.0), upper_bound=(18.0, 16.0))

    def create_ground(self):
        ground = self.world.create_static_body()
        world_filter = b2d.make_filter(category_bits=WORLD, mask_bits=0xFFFF)
        ground.create_shape(
            b2d.shape_def(filter=world_filter), b2d.segment((-40.0, 0.0), (40.0, 0.0))
        )
        # a stopper behind the cart: the recoil pushes it against this, not out of view
        stopper_def = b2d.shape_def(
            filter=world_filter,
            material=b2d.surface_material(custom_color=b2d.HexColor.DimGray),
        )
        ground.create_shape(stopper_def, b2d.box(0.25, 0.6, center=(-10.0, 0.6)))

    def create_cart(self):
        shape_def = b2d.shape_def(
            density=5.0,
            filter=b2d.make_filter(category_bits=CART, mask_bits=WORLD | CRATE),
            material=b2d.surface_material(custom_color=b2d.HexColor.SlateGray),
        )
        self.cart = self.world.create_dynamic_body(position=(-8.0, 1.0))
        self.cart.create_shape(shape_def, b2d.box(1.4, 0.4))
        self.wheels = []  # the axles: motors drive the cart while a / d is held
        for x in (-1.0, 1.0):
            wheel = self.world.create_dynamic_body(position=(-8.0 + x, 0.45))
            wheel.create_shape(shape_def, b2d.circle(radius=0.45))
            axle = self.world.create_revolute_joint(
                self.cart, wheel, local_anchor_a=(x, -0.55), max_motor_torque=DRIVE_TORQUE
            )
            self.wheels.append(axle)

    def create_tower(self, x, rows):
        shape_def = b2d.shape_def(
            density=0.5,
            filter=b2d.make_filter(category_bits=CRATE, mask_bits=0xFFFF),
            material=b2d.surface_material(friction=0.6, custom_color=b2d.HexColor.Peru),
        )
        for row in range(rows):
            for column in range(2):
                body = self.world.create_dynamic_body(position=(x + column, 0.5 + row))
                body.create_shape(shape_def, b2d.box(0.48, 0.48))

    def create_cannon(self):
        # owned by the cart: the emitter follows it, and the cart takes the recoil
        self.cannon = ext.RadialEmitter(
            self.world,
            b2d.shape_def(
                density=0.3,  # light drops: the recoil rolls the cart back, not away
                filter=b2d.make_filter(category_bits=WATER, mask_bits=WORLD | CRATE),
                material=b2d.surface_material(friction=0.1, restitution=0.1),
            ),
            b2d.circle(radius=0.1),
            body=self.cart,
            rate=200.0,
            capacity=800,
            angle_min=-0.03,
            angle_max=0.03,
            radius=BARREL,
            speed=ext.uniform(17.0, 19.0),
            lifetime=ext.uniform(2.0, 3.0),
            max_lifetime=3.0,
            colors=[(0.0, 0xE0F4FF), (1.0, 0x2B6CB0)],  # by age
        )

    def set_speed(self, value):
        self.cannon.speed = ext.uniform(value - 1.0, value + 1.0)

    def set_rate(self, value):
        self.cannon.rate = value

    def set_firing(self, value):
        self.cannon.enabled = value

    def on_key_down(self, event):
        if event.key == "space":
            self.cannon.enabled = not self.cannon.enabled

    def pre_update(self, dt):
        self.aim += AIM_SPEED * dt * (self.is_key_pressed("w") - self.is_key_pressed("s"))
        self.aim = min(max(self.aim, AIM_MIN), AIM_MAX)
        self.cannon.local_frame = b2d.transform((0.6, 0.5), b2d.make_rot(self.aim))
        # a: left (counter-clockwise wheels), d: right; no key: the wheels roll freely
        drive = self.is_key_pressed("a") - self.is_key_pressed("d")
        for axle in self.wheels:
            axle.motor_enabled = drive != 0
            axle.target_motor_speed = DRIVE_SPEED * drive
        impulse, angular_impulse = self.cannon.step(dt)
        # the recoil
        self.cart.apply_linear_impulse_to_center(impulse)
        self.cart.apply_angular_impulse(angular_impulse)

    def post_debug_draw(self):
        # the barrel
        pose = self.cannon.pose
        end = pose.p + BARREL * b2d.Vec2(pose.q.c, pose.q.s)
        self.debug_draw.draw_segment(pose.p, end, b2d.HexColor.LightGray)
        self.debug_draw.draw_point(end, 8.0, b2d.HexColor.LightSkyBlue)
