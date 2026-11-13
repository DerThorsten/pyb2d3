"""Ports of box2d's samples/sample_world.cpp."""

import math
import random

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample, widgets

from ._common import Box2dSample
from ._world_helpers import Car, create_donut, create_human, parse_path, random_polygon


@register_sample("World", "Tiles")
class TileWorld(Box2dSample):
    """A long world of static tiles with stacks, ragdolls, donuts and a car (keys a / s / d drive the car)."""

    period = 40.0
    # box2d uses 10 cycles in debug builds and 600 in release builds
    cycle_count = 10
    grid_size = 1.0
    camera_zoom = 25.0 * 1.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        period, cycle_count, grid_size = self.period, self.cycle_count, self.grid_size
        omega = 2.0 * math.pi / period
        self.grid_count = int(cycle_count * period / grid_size)
        x_start = -0.5 * (cycle_count * period)
        self.view_position = b2d.Vec2(x_start, 15.0)
        self.camera_center = (x_start, 15.0)

        # not invoking contact creation significantly reduces the cost of creating static bodies and shapes
        shape_def = b2d.shape_def(invoke_contact_creation=False)
        height = 4.0
        x_body = x_start
        for i in range(self.grid_count):
            # create a new body regularly so that shapes are not too far from the body origin,
            # contact points are computed relative to the body origin
            if i % 10 == 0:
                ground = world.create_static_body(position=(x_body, 0))
                x_shape = 0.0
            y_count = round(height * math.cos(omega * x_body)) + 12
            for j in range(y_count):
                ground.create_shape(
                    shape_def,
                    b2d.box(0.4 * grid_size, 0.4 * grid_size, center=(x_shape, j * grid_size), rotation=0.0, radius=0.1),
                )
            x_body += grid_size
            x_shape += grid_size

        box = b2d.box(0.3, 0.2)
        human_index = 0
        for cycle_index in range(cycle_count):
            x_base = (0.5 + cycle_index) * period + x_start
            remainder = cycle_index % 3
            if remainder == 0:
                for i in range(10):
                    for j in range(5):
                        body = world.create_dynamic_body(position=(x_base - 3.0 + 0.6 * i, 10.0 + 0.5 * j))
                        body.create_shape(b2d.shape_def(), box)
            elif remainder == 1:
                for i in range(5):
                    human_index += 1
                    create_human(world, (x_base - 2.0 + i, 10.0), 1.5, 0.05, 0.0, 0.0, human_index)
            else:
                for i in range(5):
                    create_donut(world, (x_base - 4.0 + 2.0 * i, 12.0), 0.75)

        self.car = Car(world, (x_start + 20.0, 40.0), 10.0, 2.0, 0.7, 2000.0)

        self.cycle_index = 0
        self.speed = 0.0
        self.explosion_position = b2d.Vec2((0.5 + self.cycle_index) * period + x_start, 7.0)
        self.explode = True
        self.follow_car = False
        self.step_count = 0

        self.speed_slider = widgets.FloatSlider(
            label="speed", min_value=-400.0, max_value=400.0, step=1.0, value=self.speed, callback=self.set_speed
        )
        self.frontend.add_widget(self.speed_slider)
        self.frontend.add_widget(widgets.Button(label="stop", callback=self.stop))
        self.frontend.add_widget(widgets.Checkbox(label="explode", value=self.explode, callback=self.set_explode))
        self.frontend.add_widget(widgets.Checkbox(label="follow car", value=self.follow_car, callback=self.set_follow_car))

    def set_speed(self, speed):
        self.speed = speed

    def stop(self):
        self.speed = 0.0
        self.speed_slider.value = 0.0

    def set_explode(self, explode):
        self.explode = explode

    def set_follow_car(self, follow_car):
        self.follow_car = follow_car

    def move_camera_x(self, x):
        # the sandbox camera can only be dragged by a delta
        cx, cy = self.camera_center
        self.frontend.drag_camera((cx - x, 0.0))
        self.camera_center = (x, cy)

    def pre_update(self, dt):
        span = 0.5 * (self.period * self.cycle_count)
        self.view_position.x = min(max(self.view_position.x + dt * self.speed, -span), span)
        if self.speed != 0.0:
            self.move_camera_x(self.view_position.x)
        if self.follow_car:
            self.move_camera_x(self.car.chassis.position.x)

        if self.step_count % 2 == 1 and self.explode:
            self.explosion_position.x = (0.5 + self.cycle_index) * self.period - span
            self.world.explode(position=self.explosion_position, radius=2.0, falloff=0.1, impulse_per_length=1.0)
            self.cycle_index = (self.cycle_index + 1) % self.cycle_count

        for key, speed in (("a", 20.0), ("s", 0.0), ("d", -5.0)):
            if self.is_key_pressed(key):
                self.car.set_speed(speed)

    def post_update(self, dt):
        self.step_count += 1

    def post_debug_draw(self):
        if self.explode:
            self.debug_draw.draw_circle(self.explosion_position, 2.0, b2d.HexColor.Azure.value)


# 1e7 and 1e6 are exactly representable in float, so the placement adds no error of its own
FAR_ORIGIN = (10.0e6, 0.0)


def register_far_sample(category, name):
    """The far samples exercise box2d's double precision positions: with the default single
    precision build a float has 1 m resolution at 1e7 (6 cm at 1e6) and they fall apart,
    so they are only registered for double precision builds."""
    if b2d.is_double_precision():
        return register_sample(category, name)
    return lambda cls: cls


@register_far_sample("World", "Far Pyramid")
class FarPyramid(Box2dSample):
    """A pyramid built far from the origin. Box2d settles it like one at the origin in double precision builds."""

    camera_center = (FAR_ORIGIN[0], 12.0)
    camera_zoom = 17.0

    base_count = 50

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ox, oy = FAR_ORIGIN
        h = 0.25

        ground = self.world.create_static_body(position=FAR_ORIGIN)
        ground.create_shape(b2d.shape_def(), b2d.segment((-40, 0), (40, 0)))

        shape_def = b2d.shape_def()
        box = b2d.box(h, h)
        for i in range(self.base_count):
            y = (2.0 * i + 1.0) * h
            for j in range(i, self.base_count):
                x = (i + 1.0) * h + 2.0 * (j - i) * h - h * self.base_count
                self.world.create_dynamic_body(position=(ox + x, oy + y)).create_shape(shape_def, box)


@register_far_sample("World", "Far Ragdolls")
class FarRagdolls(Box2dSample):
    """A pile of ragdolls in a box far from the origin."""

    camera_center = (FAR_ORIGIN[0], 6.0)
    camera_zoom = 10.0

    row_count = 5
    column_count = 5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ox, oy = FAR_ORIGIN

        ground = self.world.create_static_body(position=FAR_ORIGIN)
        w, h = 6.0, 12.0
        for p1, p2 in (((-w, 0), (w, 0)), ((-w, 0), (-w, h)), ((w, 0), (w, h))):
            ground.create_shape(b2d.shape_def(), b2d.segment(p1, p2))

        scale = 1.0
        index = 0
        for i in range(self.row_count):
            for j in range(self.column_count):
                x = 2.4 * scale * (j - 0.5 * (self.column_count - 1)) + random.uniform(-0.3, 0.3)
                y = 2.0 + 2.2 * scale * i
                index += 1
                create_human(self.world, (ox + x, oy + y), scale, 0.05, 1.0, 0.5, index)


GATE_PATH = (
    "m 63.500002,201.08333 103.187498,0 1e-5,-37.04166 h -2.64584 l 0,34.39583 h -42.33333 v -2.64583 l "
    "-2.64584,-1e-5 v -2.64583 h -2.64583 v -2.64584 h -2.64584 v -2.64583 H 111.125 v -2.64583 h -2.64583 v "
    "-2.64583 h -2.64583 v -2.64584 l -2.64584,1e-5 v -2.64583 l -2.64583,-1e-5 V 174.625 h -2.645834 v -2.64584 l "
    "-2.645833,1e-5 v -2.64584 H 92.60417 v -2.64583 h -2.645834 v -2.64583 l -26.458334,0 0,37.04166"
)


@register_far_sample("World", "Far Gate")
class FarGate(Box2dSample):
    """The Gear Lift mechanism 1000 km from the origin: in single precision the float grid is coarser than
    the gear teeth, so the mechanism grinds and jitters (keys a / d change the motor speed)."""

    origin = (1.0e6, 0.0)
    camera_center = (1.0e6, 6.0)
    camera_zoom = 7.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ox, oy = self.origin

        ground = world.create_static_body(position=self.origin)
        points = parse_path(GATE_PATH, offset=(-120.0, -200.0), scale=0.2)
        ground.create_chain(
            b2d.chain_def(
                points, material=b2d.surface_material(custom_color=b2d.HexColor.DarkSeaGreen.value), is_loop=True
            )
        )

        gear_radius = 1.0
        tooth_half_width = 0.09
        tooth_half_height = 0.06
        tooth_radius = 0.03
        link_half_length = 0.07
        link_radius = 0.05
        link_count = 40
        door_half_height = 1.5

        gear_position1 = (ox - 4.25, oy + 9.75)
        gear_position2 = (gear_position1[0] + 2.0, gear_position1[1] + 1.0)
        link_attach_position = (gear_position2[0] + gear_radius + 2.0 * tooth_half_width + tooth_radius, gear_position2[1])
        door_position = (
            link_attach_position[0],
            link_attach_position[1] - (2.0 * link_count * link_half_length + door_half_height),
        )

        def create_gear(position, tooth_offset):
            body = world.create_dynamic_body(position=position)
            shape_def = b2d.shape_def(
                material=b2d.surface_material(friction=0.1, custom_color=b2d.HexColor.SaddleBrown.value)
            )
            body.create_shape(shape_def, b2d.circle(radius=gear_radius))
            shape_def.material.custom_color = b2d.HexColor.Gray.value
            dq = b2d.make_rot(2.0 * math.pi / 16)
            rotation = b2d.Rot()
            center = (gear_radius + tooth_offset, 0.0)
            for _ in range(16):
                body.create_shape(
                    shape_def,
                    b2d.box(tooth_half_width, tooth_half_height, center=center, rotation=rotation, radius=tooth_radius),
                )
                rotation = b2d.mul_rot(dq, rotation)
                center = b2d.rotate_vector(rotation, (gear_radius + tooth_offset, 0.0))
            return body

        self.motor_torque = 80.0
        self.motor_speed = -0.3
        self.enable_motor = True

        driver = create_gear(gear_position1, tooth_half_height)
        self.driver = world.create_revolute_joint(
            body_a=ground,
            body_b=driver,
            local_anchor_a=ground.local_point(gear_position1),
            local_anchor_b=(0, 0),
            enable_motor=self.enable_motor,
            max_motor_torque=self.motor_torque,
            motor_speed=self.motor_speed,
        )

        follower = create_gear(gear_position2, tooth_half_width)
        world.create_revolute_joint(
            body_a=ground,
            body_b=follower,
            local_frame_a=b2d.transform(p=ground.local_point(gear_position2), q=b2d.make_rot(0.25 * math.pi)),
            local_anchor_b=(0, 0),
            enable_motor=True,
            max_motor_torque=0.5,
            lower_angle=-0.3 * math.pi,
            upper_angle=0.8 * math.pi,
            enable_limit=True,
        )

        link_shape_def = b2d.shape_def(
            density=2.0, material=b2d.surface_material(custom_color=b2d.HexColor.LightSteelBlue.value)
        )
        capsule = b2d.capsule((0, -link_half_length), (0, link_half_length), link_radius)
        x, y = link_attach_position[0], link_attach_position[1] - link_half_length
        prev_body = follower
        for _ in range(link_count):
            body = world.create_dynamic_body(position=(x, y))
            body.create_shape(link_shape_def, capsule)
            pivot = (x, y + link_half_length)
            world.create_revolute_joint(
                body_a=prev_body,
                body_b=body,
                local_anchor_a=prev_body.local_point(pivot),
                local_anchor_b=body.local_point(pivot),
                max_motor_torque=0.05,
                enable_motor=True,
                draw_scale=0.2,
            )
            y -= 2.0 * link_half_length
            prev_body = body

        door = world.create_dynamic_body(position=door_position)
        door.create_shape(
            b2d.shape_def(material=b2d.surface_material(friction=0.1, custom_color=b2d.HexColor.DarkCyan.value)),
            b2d.box(0.15, door_half_height),
        )
        pivot = (door_position[0], door_position[1] + door_half_height)
        world.create_revolute_joint(
            body_a=prev_body,
            body_b=door,
            local_anchor_a=prev_body.local_point(pivot),
            local_anchor_b=(0, door_half_height),
            enable_motor=True,
            max_motor_torque=0.05,
        )
        axis = b2d.make_rot_from_unit_vector((0, 1))
        world.create_prismatic_joint(
            body_a=ground,
            body_b=door,
            local_frame_a=b2d.transform(p=ground.local_point(door_position), q=axis),
            local_frame_b=b2d.transform(p=(0, 0), q=axis),
            max_motor_force=0.2,
            enable_motor=True,
            collide_connected=True,
        )

        debris_def = b2d.shape_def(material=b2d.surface_material(rolling_resistance=0.3))
        colors = [
            c.value
            for c in (
                b2d.HexColor.Gray,
                b2d.HexColor.Gainsboro,
                b2d.HexColor.LightGray,
                b2d.HexColor.LightSlateGray,
                b2d.HexColor.DarkGray,
            )
        ]
        for i in range(20):
            for j in range(10):
                body = world.create_dynamic_body(position=(ox - 3.15 + 0.2 * j, oy + 4.25 + 0.2 * i))
                debris_def.material.custom_color = random.choice(colors)
                body.create_shape(debris_def, random_polygon(0.1, radius=random.uniform(0.01, 0.02)))

        self.frontend.add_widget(widgets.Checkbox(label="Motor", value=self.enable_motor, callback=self.set_enable_motor))
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Max Torque",
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                value=self.motor_torque,
                callback=self.set_motor_torque,
            )
        )
        self.speed_slider = widgets.FloatSlider(
            label="Speed", min_value=-0.3, max_value=0.3, step=0.01, value=self.motor_speed, callback=self.set_motor_speed
        )
        self.frontend.add_widget(self.speed_slider)

    def set_enable_motor(self, enable):
        self.enable_motor = enable
        self.driver.motor_enabled = enable
        self.driver.wake_bodies()

    def set_motor_torque(self, torque):
        self.driver.max_motor_torque = torque
        self.driver.wake_bodies()

    def set_motor_speed(self, speed):
        self.motor_speed = speed
        self.speed_slider.value = speed
        self.driver.target_motor_speed = speed
        self.driver.wake_bodies()

    def pre_update(self, dt):
        if self.is_key_pressed("a"):
            self.set_motor_speed(max(-0.3, self.motor_speed - 0.01))
        if self.is_key_pressed("d"):
            self.set_motor_speed(min(0.3, self.motor_speed + 0.01))
