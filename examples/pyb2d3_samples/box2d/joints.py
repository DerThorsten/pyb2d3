"""Ports of box2d's samples/sample_joints.cpp."""

import math
import random

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample
from pyb2d3_sandbox.widgets import Button, Checkbox, IntSlider

from ._joints_helpers import (
    Car,
    Donut,
    Doohickey,
    Human,
    JointSample,
    joint_setter,
    parse_path,
    pinned,
    random_polygon,
    slider,
)

WHITE = b2d.HexColor.White.value


def degrees_to_radians(degrees):
    return math.pi * degrees / 180.0


def create_joint_gallery(world, ground, kinds, start, spacing, body_def, collide_connected=False, motor_force=None, weld=None):
    """One box per joint kind, each attached to the ground. Returns the bodies and the joints."""
    box = b2d.box(1.0, 1.0)
    bodies, joints = [], []
    for i, kind in enumerate(kinds):
        x, y = start[0] + spacing * i, start[1]
        body = world.create_body(body_def, position=(x, y))
        body.create_shape(b2d.shape_def(), box)
        side = pinned(ground, body, (x - 1.0, y))
        if kind == "distance":
            length = 2.0
            joint = world.create_distance_joint(
                **pinned(ground, body, (x, y + 1.0 + length), (x, y + 1.0)),
                length=length,
                collide_connected=collide_connected,
            )
        elif kind == "motor":
            joint = world.create_motor_joint(
                body_a=ground,
                body_b=body,
                local_anchor_a=(x, y),
                max_velocity_force=motor_force[0],
                max_velocity_torque=motor_force[1],
                collide_connected=collide_connected,
            )
        elif kind == "prismatic":
            joint = world.create_prismatic_joint(**side, collide_connected=collide_connected)
        elif kind == "revolute":
            joint = world.create_revolute_joint(**side, collide_connected=collide_connected)
        elif kind == "weld":
            joint = world.create_weld_joint(**side, **(weld or {}), collide_connected=collide_connected)
        elif kind == "wheel":
            joint = world.create_wheel_joint(
                **side,
                hertz=1.0,
                damping_ratio=0.7,
                lower_translation=-1.0,
                upper_translation=1.0,
                enable_limit=True,
                enable_motor=True,
                max_motor_torque=10.0,
                motor_speed=1.0,
                collide_connected=collide_connected,
            )
        else:
            raise ValueError(kind)
        bodies.append(body)
        joints.append(joint)
    return bodies, joints


ALL_JOINT_KINDS = ("distance", "motor", "prismatic", "revolute", "weld", "wheel")


@register_sample("Joints", "Distance Joint")
class DistanceJoint(JointSample):
    """Test the distance joint and all options."""

    camera_center = (0.0, 12.0)
    camera_zoom = 25.0 * 0.35
    max_count = 10

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.ground = self.world.create_static_body()

        self.hertz = 5.0
        self.damping_ratio = 0.5
        self.length = 1.0
        self.min_length = self.length
        self.max_length = self.length
        self.tension_force = 2000.0
        self.compression_force = 100.0
        self.enable_spring = False
        self.enable_limit = False
        self.bodies, self.joints = [], []

        self.create_scene(1)

        self.add_widgets(
            slider("Length", 0.1, 4.0, self.length, self.set_length),
            Checkbox("Spring", self.enable_spring, self.set_enable_spring),
            slider("Tension", 0.0, 4000.0, self.tension_force, self.set_tension),
            slider("Compression", 0.0, 200.0, self.compression_force, self.set_compression),
            slider("Hertz", 0.0, 15.0, self.hertz, self.set_hertz),
            slider("Damping", 0.0, 4.0, self.damping_ratio, self.set_damping_ratio),
            Checkbox("Limit", self.enable_limit, self.set_enable_limit),
            slider("Min Length", 0.1, 4.0, self.min_length, self.set_min_length),
            slider("Max Length", 0.1, 4.0, self.max_length, self.set_max_length),
            IntSlider("Count", 1, self.max_count, 1, 1, self.create_scene),
        )

    def create_scene(self, count):
        for body in self.bodies:
            body.destroy()

        y_offset = 20.0
        shape_def = b2d.shape_def(density=20.0)
        circle = b2d.circle(radius=0.25)

        self.bodies, self.joints = [], []
        prev = self.ground
        for i in range(count):
            body = self.world.create_dynamic_body(angular_damping=1.0, position=(self.length * (i + 1), y_offset))
            body.create_shape(shape_def, circle)
            joint = self.world.create_distance_joint(
                **pinned(prev, body, (self.length * i, y_offset), (self.length * (i + 1), y_offset)),
                hertz=self.hertz,
                damping_ratio=self.damping_ratio,
                length=self.length,
                lower_spring_force=-self.tension_force,
                upper_spring_force=self.compression_force,
                min_length=self.min_length,
                max_length=self.max_length,
                enable_spring=self.enable_spring,
                enable_limit=self.enable_limit,
            )
            self.bodies.append(body)
            self.joints.append(joint)
            prev = body

    def for_each_joint(self, apply):
        for joint in self.joints:
            apply(joint)
            joint.wake_bodies()

    def set_length(self, value):
        self.length = value
        self.for_each_joint(lambda joint: setattr(joint, "rest_length", value))

    def set_enable_spring(self, value):
        self.enable_spring = value
        self.for_each_joint(lambda joint: setattr(joint, "spring_enabled", value))

    def set_spring_force_range(self):
        self.for_each_joint(lambda joint: joint.set_spring_force_range(-self.tension_force, self.compression_force))

    def set_tension(self, value):
        self.tension_force = value
        self.set_spring_force_range()

    def set_compression(self, value):
        self.compression_force = value
        self.set_spring_force_range()

    def set_hertz(self, value):
        self.hertz = value
        self.for_each_joint(lambda joint: setattr(joint, "spring_hertz", value))

    def set_damping_ratio(self, value):
        self.damping_ratio = value
        self.for_each_joint(lambda joint: setattr(joint, "spring_damping_ratio", value))

    def set_enable_limit(self, value):
        self.enable_limit = value
        self.for_each_joint(lambda joint: setattr(joint, "limit_enabled", value))

    def set_limits(self):
        self.for_each_joint(lambda joint: joint.set_limits(self.min_length, self.max_length))

    def set_min_length(self, value):
        self.min_length = value
        self.set_limits()

    def set_max_length(self, value):
        self.max_length = value
        self.set_limits()


@register_sample("Joints", "Motor Joint")
class MotorJoint(JointSample):
    """This test shows how to use a motor joint. A motor joint can be used to animate a dynamic body.
    With finite motor forces the body can be blocked by collision with other bodies."""

    camera_center = (0.0, 7.0)
    camera_zoom = 25.0 * 0.4

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = self.create_ground_segment()

        self.target_transform = b2d.transform(p=(0.0, 8.0))

        # a target body
        self.target = world.create_kinematic_body(position=self.target_transform.p)

        # the motorized body
        self.body = world.create_dynamic_body(position=self.target_transform.p)
        self.body.create_shape(b2d.shape_def(), b2d.box(2.0, 0.5))

        self.max_force = 5000.0
        self.max_torque = 500.0
        self.joint = world.create_motor_joint(
            body_a=self.target,
            body_b=self.body,
            linear_hertz=4.0,
            linear_damping_ratio=0.7,
            angular_hertz=4.0,
            angular_damping_ratio=0.7,
            max_spring_force=self.max_force,
            max_spring_torque=self.max_torque,
        )

        # a spring body
        position = (-2.0, 2.0)
        spring_body = world.create_dynamic_body(position=position)
        spring_body.create_shape(b2d.shape_def(), b2d.box(0.5, 0.5))
        world.create_motor_joint(
            body_a=ground,
            body_b=spring_body,
            local_anchor_a=(position[0] + 0.25, position[1] + 0.25),
            local_anchor_b=(0.25, 0.25),
            linear_hertz=7.5,
            linear_damping_ratio=0.7,
            angular_hertz=7.5,
            angular_damping_ratio=0.7,
            max_spring_force=500.0,
            max_spring_torque=10.0,
        )

        self.speed = 1.0
        self.time = 0.0

        joints = [self.joint]
        self.add_widgets(
            slider("Speed", -5.0, 5.0, self.speed, self.set_speed, step=1.0),
            slider("Max Force", 0.0, 10000.0, self.max_force, joint_setter(joints, "max_spring_force", False)),
            slider("Max Torque", 0.0, 10000.0, self.max_torque, joint_setter(joints, "max_spring_torque", False)),
            Button("Apply Impulse", lambda: self.body.apply_linear_impulse_to_center((100.0, 0.0), True)),
        )

    def set_speed(self, value):
        self.speed = value

    def pre_update(self, dt):
        if dt > 0.0:
            self.time += self.speed * dt
            t = self.time
            self.target_transform = b2d.transform(p=(6.0 * math.sin(2.0 * t), 8.0 + 4.0 * math.sin(t)), q=2.0 * t)
            self.target.set_target_transform(self.target_transform, dt, True)

    def post_debug_draw(self):
        self.debug_draw.draw_transform(self.target_transform)


@register_sample("Joints", "Top Down Friction")
class TopDownFriction(JointSample):
    """Motor joints with zero target velocity act as top down friction."""

    camera_center = (0.0, 10.0)
    camera_zoom = 12.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        corners = ((-10.0, 0.0), (10.0, 0.0), (10.0, 20.0), (-10.0, 20.0))
        for i, corner in enumerate(corners):
            ground.create_shape(b2d.shape_def(), b2d.segment(corner, corners[(i + 1) % 4]))

        shape_def = b2d.shape_def(material=b2d.surface_material(restitution=0.8))
        shapes = (
            lambda: b2d.capsule((-0.25, 0.0), (0.25, 0.0), 0.25),
            lambda: b2d.circle(radius=0.35),
            lambda: b2d.box(0.35, 0.35),
            lambda: random_polygon(0.75, radius=0.1),
        )

        n = 10
        for i in range(n):
            for j in range(n):
                body = world.create_dynamic_body(position=(-5.0 + j, 15.0 - i), gravity_scale=0.0)
                body.create_shape(shape_def, shapes[(n * i + j) % 4]())
                world.create_motor_joint(
                    body_a=ground,
                    body_b=body,
                    collide_connected=True,
                    max_velocity_force=10.0,
                    max_velocity_torque=10.0,
                )

        self.add_widgets(Button("Explode", self.explode))

    def explode(self):
        self.world.explode(position=(0.0, 10.0), radius=10.0, falloff=5.0, impulse_per_length=10.0)


@register_sample("Joints", "Filter Joint")
class FilterJoint(JointSample):
    """This sample shows how to use a filter joint to prevent collision between two bodies.
    This is more specific than shape filters. It also shows that sleeping is coupled by the filter joint."""

    camera_center = (0.0, 7.0)
    camera_zoom = 25.0 * 0.4

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment()

        bodies = []
        for x in (-4.0, 4.0):
            body = self.world.create_dynamic_body(position=(x, 2.0))
            body.create_shape(b2d.shape_def(), b2d.box(2.0, 2.0))
            bodies.append(body)

        self.world.create_filter_joint(*bodies)


@register_sample("Joints", "Revolute")
class RevoluteJoint(JointSample):
    """Revolute joints with limits, motors and springs."""

    camera_center = (0.0, 15.5)
    camera_zoom = 25.0 * 0.7

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body(position=(0.0, -1.0))
        ground.create_shape(b2d.shape_def(), b2d.box(40.0, 1.0))

        self.enable_spring = False
        self.enable_limit = False
        self.enable_motor = False
        self.hertz = 2.0
        self.damping_ratio = 0.5
        self.target_degrees = 45.0
        self.motor_speed = 1.0
        self.motor_torque = 1000.0

        body = world.create_dynamic_body(position=(-10.0, 20.0))
        body.create_shape(b2d.shape_def(density=1.0), b2d.capsule((0.0, -1.0), (0.0, 6.0), 0.5))
        self.joint1 = world.create_revolute_joint(
            **pinned(ground, body, (-10.0, 20.5), q_a=0.5 * math.pi),
            target_angle=degrees_to_radians(self.target_degrees),
            enable_spring=self.enable_spring,
            hertz=self.hertz,
            damping_ratio=self.damping_ratio,
            motor_speed=self.motor_speed,
            max_motor_torque=self.motor_torque,
            enable_motor=self.enable_motor,
            lower_angle=-0.5 * math.pi,
            upper_angle=0.05 * math.pi,
            enable_limit=self.enable_limit,
        )
        self.joint1.set_constraint_tuning(60.0, 20.0)

        self.ball = world.create_dynamic_body(position=(5.0, 30.0))
        self.ball.create_shape(b2d.shape_def(density=1.0), b2d.circle(radius=2.0))

        body = world.create_dynamic_body(position=(20.0, 10.0))
        body.create_shape(b2d.shape_def(density=1.0), b2d.box(10.0, 0.5, center=(-10.0, 0.0)))
        self.joint2 = world.create_revolute_joint(
            **pinned(ground, body, (19.0, 10.0)),
            lower_angle=-0.25 * math.pi,
            upper_angle=0.0,
            enable_limit=True,
            enable_motor=True,
            motor_speed=0.0,
            max_motor_torque=self.motor_torque,
        )

        joints = [self.joint1]
        self.add_widgets(
            Checkbox("Limit", self.enable_limit, joint_setter(joints, "limit_enabled")),
            Checkbox("Motor", self.enable_motor, joint_setter(joints, "motor_enabled")),
            slider("Max Torque", 0.0, 5000.0, self.motor_torque, joint_setter(joints, "max_motor_torque")),
            slider("Speed", -20.0, 20.0, self.motor_speed, joint_setter(joints, "target_motor_speed"), step=1.0),
            Checkbox("Spring", self.enable_spring, joint_setter(joints, "spring_enabled")),
            slider("Hertz", 0.0, 30.0, self.hertz, joint_setter(joints, "spring_hertz")),
            slider("Damping", 0.0, 2.0, self.damping_ratio, joint_setter(joints, "spring_damping_ratio")),
            slider("Degrees", -180.0, 180.0, self.target_degrees, self.set_target_degrees, step=1.0),
        )

    def set_target_degrees(self, degrees):
        self.joint1.target_angle = degrees_to_radians(degrees)
        self.joint1.wake_bodies()


@register_sample("Joints", "Prismatic")
class PrismaticJoint(JointSample):
    """A prismatic joint along a diagonal axis with limit, motor and spring."""

    camera_center = (0.0, 8.0)
    camera_zoom = 25.0 * 0.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = world.create_static_body()

        self.enable_spring = False
        self.enable_limit = True
        self.enable_motor = False
        self.motor_speed = 2.0
        self.motor_force = 25.0
        self.hertz = 1.0
        self.damping_ratio = 0.5
        self.translation = 0.0

        body = world.create_dynamic_body(position=(0.0, 10.0))
        body.create_shape(b2d.shape_def(), b2d.box(0.5, 2.0))

        axis = b2d.make_rot_from_unit_vector(b2d.normalize((1.0, 1.0)))
        self.joint = world.create_prismatic_joint(
            **pinned(ground, body, (0.0, 9.0), q_a=axis, q_b=axis),
            draw_scale=2.0,
            motor_speed=self.motor_speed,
            max_motor_force=self.motor_force,
            enable_motor=self.enable_motor,
            lower_translation=-10.0,
            upper_translation=10.0,
            enable_limit=self.enable_limit,
            enable_spring=self.enable_spring,
            hertz=self.hertz,
            damping_ratio=self.damping_ratio,
        )

        joints = [self.joint]
        self.add_widgets(
            Checkbox("Limit", self.enable_limit, joint_setter(joints, "limit_enabled")),
            Checkbox("Motor", self.enable_motor, joint_setter(joints, "motor_enabled")),
            slider("Max Force", 0.0, 200.0, self.motor_force, joint_setter(joints, "max_motor_force")),
            slider("Speed", -40.0, 40.0, self.motor_speed, joint_setter(joints, "target_motor_speed"), step=1.0),
            Checkbox("Spring", self.enable_spring, joint_setter(joints, "spring_enabled")),
            slider("Hertz", 0.0, 10.0, self.hertz, joint_setter(joints, "spring_hertz")),
            slider("Damping", 0.0, 2.0, self.damping_ratio, joint_setter(joints, "spring_damping_ratio")),
            slider("Translation", -15.0, 15.0, self.translation, joint_setter(joints, "target_translation")),
        )


@register_sample("Joints", "Wheel")
class WheelJoint(JointSample):
    """A wheel joint along a diagonal axis with limit, motor and spring."""

    camera_center = (0.0, 10.0)
    camera_zoom = 25.0 * 0.15

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = world.create_static_body()

        self.enable_spring = True
        self.enable_limit = True
        self.enable_motor = True
        self.motor_speed = 2.0
        self.motor_torque = 5.0
        self.hertz = 1.0
        self.damping_ratio = 0.7

        body = world.create_dynamic_body(position=(0.0, 10.25))
        body.create_shape(b2d.shape_def(), b2d.capsule((0.0, -0.5), (0.0, 0.5), 0.5))

        axis = b2d.make_rot_from_unit_vector(b2d.normalize((1.0, 1.0)))
        self.joint = world.create_wheel_joint(
            **pinned(ground, body, (0.0, 10.0), q_a=axis),
            motor_speed=self.motor_speed,
            max_motor_torque=self.motor_torque,
            enable_motor=self.enable_motor,
            lower_translation=-3.0,
            upper_translation=3.0,
            enable_limit=self.enable_limit,
            hertz=self.hertz,
            damping_ratio=self.damping_ratio,
        )

        joints = [self.joint]
        self.add_widgets(
            Checkbox("Limit", self.enable_limit, joint_setter(joints, "limit_enabled", False)),
            Checkbox("Motor", self.enable_motor, joint_setter(joints, "motor_enabled", False)),
            slider("Torque", 0.0, 20.0, self.motor_torque, joint_setter(joints, "max_motor_torque", False)),
            slider("Speed", -20.0, 20.0, self.motor_speed, joint_setter(joints, "target_motor_speed", False)),
            Checkbox("Spring", self.enable_spring, joint_setter(joints, "spring_enabled", False)),
            slider("Hertz", 0.0, 10.0, self.hertz, joint_setter(joints, "spring_hertz", False)),
            slider("Damping", 0.0, 2.0, self.damping_ratio, joint_setter(joints, "spring_damping_ratio", False)),
        )


@register_sample("Joints", "Bridge")
class Bridge(JointSample):
    """A suspension bridge."""

    camera_center = (0.0, 20.0)
    camera_zoom = 25.0 * 2.5
    count = 160

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = world.create_static_body()

        self.constraint_hertz = 60.0
        self.constraint_damping_ratio = 0.0
        self.spring_hertz = 2.0
        self.spring_damping_ratio = 0.7
        self.friction_torque = 200.0

        shape_def = b2d.shape_def(density=20.0)
        box = b2d.box(0.5, 0.125)
        joint_def = dict(
            enable_motor=True,
            max_motor_torque=self.friction_torque,
            enable_spring=True,
            hertz=self.spring_hertz,
            damping_ratio=self.spring_damping_ratio,
        )

        x_base = -80.0
        self.joints = []
        prev = ground
        for i in range(self.count):
            body = world.create_dynamic_body(
                position=(x_base + 0.5 + i, 20.0), linear_damping=0.1, angular_damping=0.1
            )
            body.create_shape(shape_def, box)
            self.joints.append(world.create_revolute_joint(**pinned(prev, body, (x_base + i, 20.0)), **joint_def))
            prev = body
        self.joints.append(
            world.create_revolute_joint(**pinned(prev, ground, (x_base + self.count, 20.0)), **joint_def)
        )

        triangle = b2d.polygon([(-0.5, 0.0), (0.5, 0.0), (0.0, 1.5)])
        for i in range(2):
            body = world.create_dynamic_body(position=(-8.0 + 8.0 * i, 22.0))
            body.create_shape(shape_def, triangle)

        for i in range(3):
            body = world.create_dynamic_body(position=(-6.0 + 6.0 * i, 25.0))
            body.create_shape(shape_def, b2d.circle(radius=0.5))

        joints = self.joints
        self.add_widgets(
            slider("Joint Friction", 0.0, 10000.0, self.friction_torque, joint_setter(joints, "max_motor_torque", False)),
            slider("Spring hertz", 0.0, 30.0, self.spring_hertz, joint_setter(joints, "spring_hertz", False)),
            slider("Spring damping", 0.0, 2.0, self.spring_damping_ratio, joint_setter(joints, "spring_damping_ratio", False)),
            slider("Constraint hertz", 15.0, 240.0, self.constraint_hertz, self.set_constraint_hertz),
            slider("Constraint damping", 0.0, 10.0, self.constraint_damping_ratio, self.set_constraint_damping_ratio),
        )

    def update_constraint_tuning(self):
        for joint in self.joints:
            joint.set_constraint_tuning(self.constraint_hertz, self.constraint_damping_ratio)

    def set_constraint_hertz(self, value):
        self.constraint_hertz = value
        self.update_constraint_tuning()

    def set_constraint_damping_ratio(self, value):
        self.constraint_damping_ratio = value
        self.update_constraint_tuning()


@register_sample("Joints", "Ball & Chain")
class BallAndChain(JointSample):
    """A heavy ball hanging on a chain of capsules with joint friction."""

    camera_center = (0.0, -8.0)
    camera_zoom = 27.5
    count = 30

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = world.create_static_body()

        self.friction_torque = 100.0

        hx = 0.5
        y = self.count * hx
        capsule = b2d.capsule((-hx, 0.0), (hx, 0.0), 0.125)
        link_def = b2d.shape_def(density=20.0, filter=b2d.make_filter(category_bits=0x1, mask_bits=0x2))

        self.joints = []
        prev = ground
        for i in range(self.count):
            body = world.create_dynamic_body(position=((1.0 + 2.0 * i) * hx, y))
            body.create_shape(link_def, capsule)
            self.joints.append(self.create_link_joint(prev, body, (2.0 * i * hx, y), enable_spring=i > 0))
            prev = body

        radius = 4.0
        ball = world.create_dynamic_body(position=((1.0 + 2.0 * self.count) * hx + radius - hx, y))
        ball_def = b2d.shape_def(density=20.0, filter=b2d.make_filter(category_bits=0x2, mask_bits=0x1))
        ball.create_shape(ball_def, b2d.circle(radius=radius))
        self.joints.append(self.create_link_joint(prev, ball, (2.0 * self.count * hx, y), enable_spring=True))

        self.add_widgets(
            slider("Joint Friction", 0.0, 1000.0, self.friction_torque, joint_setter(self.joints, "max_motor_torque", False))
        )

    def create_link_joint(self, body_a, body_b, pivot, enable_spring):
        return self.world.create_revolute_joint(
            **pinned(body_a, body_b, pivot),
            enable_motor=True,
            max_motor_torque=self.friction_torque,
            enable_spring=enable_spring,
            hertz=4.0,
        )


@register_sample("Joints", "Cantilever")
class Cantilever(JointSample):
    """This sample shows the limitations of an iterative solver. The cantilever sags even though the weld
    joint is stiff as possible."""

    camera_center = (0.0, 0.0)
    camera_zoom = 25.0 * 0.35
    count = 8

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = world.create_static_body()

        self.linear_hertz = 15.0
        self.linear_damping_ratio = 0.5
        self.angular_hertz = 5.0
        self.angular_damping_ratio = 0.5
        self.gravity_scale = 1.0
        self.collide_connected = False

        hx = 0.5
        capsule = b2d.capsule((-hx, 0.0), (hx, 0.0), 0.125)
        shape_def = b2d.shape_def(density=20.0)

        self.bodies, self.joints = [], []
        prev = ground
        for i in range(self.count):
            body = world.create_dynamic_body(position=((1.0 + 2.0 * i) * hx, 0.0), is_awake=False)
            body.create_shape(shape_def, capsule)
            joint = world.create_weld_joint(
                **pinned(prev, body, (2.0 * i * hx, 0.0)),
                linear_hertz=self.linear_hertz,
                linear_damping_ratio=self.linear_damping_ratio,
                angular_hertz=self.angular_hertz,
                angular_damping_ratio=self.angular_damping_ratio,
                collide_connected=self.collide_connected,
            )
            # experimental tuning
            joint.set_constraint_tuning(120.0, 10.0)
            self.bodies.append(body)
            self.joints.append(joint)
            prev = body

        joints = self.joints
        self.add_widgets(
            slider("Linear Hertz", 0.0, 20.0, self.linear_hertz, joint_setter(joints, "linear_hertz", False)),
            slider(
                "Linear Damping Ratio",
                0.0,
                10.0,
                self.linear_damping_ratio,
                joint_setter(joints, "linear_damping_ratio", False),
            ),
            slider("Angular Hertz", 0.0, 20.0, self.angular_hertz, joint_setter(joints, "angular_hertz", False)),
            slider(
                "Angular Damping Ratio",
                0.0,
                10.0,
                self.angular_damping_ratio,
                joint_setter(joints, "angular_damping_ratio", False),
            ),
            slider("Gravity Scale", -1.0, 1.0, self.gravity_scale, self.set_gravity_scale),
            Checkbox("Collide Connected", self.collide_connected, joint_setter(joints, "collide_connected", False)),
        )

    def set_gravity_scale(self, value):
        for body in self.bodies:
            body.gravity_scale = value


@register_sample("Joints", "Motion Locks")
class MotionLocks(JointSample):
    """This test ensures joints work correctly with bodies that have motion locks. Press 'l' to push the first box."""

    camera_center = (0.0, 8.0)
    camera_zoom = 25.0 * 0.7

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()

        self.motion_locks = b2d.MotionLocks(linear_x=False, linear_y=False, angular_z=True)
        body_def = b2d.body_def(type=b2d.BodyType.DYNAMIC, motion_locks=self.motion_locks)
        self.bodies, _ = create_joint_gallery(
            self.world,
            ground,
            ALL_JOINT_KINDS,
            start=(-12.5, 10.0),
            spacing=5.0,
            body_def=body_def,
            motor_force=(200.0, 200.0),
            weld=dict(angular_hertz=1.0, angular_damping_ratio=0.5, linear_hertz=1.0, linear_damping_ratio=0.5),
        )

        self.add_widgets(
            *(
                Checkbox(label, getattr(self.motion_locks, attr), self.lock_setter(attr))
                for label, attr in (
                    ("Lock Linear X", "linear_x"),
                    ("Lock Linear Y", "linear_y"),
                    ("Lock Angular Z", "angular_z"),
                )
            )
        )

    def lock_setter(self, attr):
        def callback(value):
            setattr(self.motion_locks, attr, value)
            for body in self.bodies:
                body.motion_locks = self.motion_locks
                body.awake = True

        return callback

    def pre_update(self, dt):
        if self.is_key_pressed("l"):
            self.bodies[0].apply_linear_impulse_to_center((100.0, 0.0), True)


@register_sample("Joints", "Breakable")
class BreakableJoint(JointSample):
    """This sample shows how to break joints when the internal reaction force becomes large."""

    camera_center = (0.0, 8.0)
    camera_zoom = 25.0 * 0.7

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.create_ground_segment(-40.0, 40.0)

        body_def = b2d.body_def(type=b2d.BodyType.DYNAMIC, enable_sleep=False)
        _, self.joints = create_joint_gallery(
            self.world,
            ground,
            ALL_JOINT_KINDS,
            start=(-12.5, 10.0),
            spacing=5.0,
            body_def=body_def,
            collide_connected=True,
            motor_force=(1000.0, 20.0),
        )
        self.forces = []
        self.break_force = 1000.0

        self.add_widgets(
            slider("break force", 0.0, 10000.0, self.break_force, self.set_break_force),
            slider("gravity", -50.0, 50.0, self.world.gravity.y, self.set_gravity),
        )

    def set_break_force(self, value):
        self.break_force = value

    def set_gravity(self, value):
        self.world.gravity = (self.world.gravity.x, value)

    def pre_update(self, dt):
        self.forces = []
        for i, joint in enumerate(self.joints):
            if joint is None:
                continue
            force = joint.constraint_force
            if b2d.length_squared(force) > self.break_force * self.break_force:
                joint.destroy()
                self.joints[i] = None
            else:
                self.forces.append((joint.local_frame_a.p, force))

    def post_debug_draw(self):
        for p, force in self.forces:
            self.debug_draw.draw_string(p, f"({force.x:.1f}, {force.y:.1f})", WHITE)


@register_sample("Joints", "Separation")
class JointSeparation(JointSample):
    """This sample shows how to measure joint separation. This is the unresolved constraint error."""

    camera_center = (0.0, 8.0)
    camera_zoom = 25.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.create_ground_segment(-40.0, 40.0)

        body_def = b2d.body_def(type=b2d.BodyType.DYNAMIC, enable_sleep=False)
        self.bodies, self.joints = create_joint_gallery(
            self.world,
            ground,
            ("distance", "prismatic", "revolute", "weld", "wheel"),
            start=(-20.0, 10.0),
            spacing=10.0,
            body_def=body_def,
            collide_connected=True,
        )

        self.impulse = 500.0
        self.joint_hertz = 60.0
        self.joint_damping_ratio = 2.0

        self.add_widgets(
            slider("gravity", -500.0, 500.0, self.world.gravity.y, self.set_gravity, step=1.0),
            slider("magnitude", 0.0, 1000.0, self.impulse, self.set_impulse, step=1.0),
            slider("hertz", 15.0, 120.0, self.joint_hertz, self.set_joint_hertz, step=1.0),
            slider("damping", 0.0, 10.0, self.joint_damping_ratio, self.set_joint_damping_ratio),
            Button("impulse", self.apply_impulse),
        )

    def set_gravity(self, value):
        self.world.gravity = (self.world.gravity.x, value)

    def set_impulse(self, value):
        self.impulse = value

    def update_constraint_tuning(self):
        for joint in self.joints:
            joint.set_constraint_tuning(self.joint_hertz, self.joint_damping_ratio)

    def set_joint_hertz(self, value):
        self.joint_hertz = value
        self.update_constraint_tuning()

    def set_joint_damping_ratio(self, value):
        self.joint_damping_ratio = value
        self.update_constraint_tuning()

    def apply_impulse(self):
        for body in self.bodies:
            body.apply_linear_impulse((self.impulse, -self.impulse), body.world_point((1.0, 1.0)), True)

    def post_debug_draw(self):
        for joint in self.joints:
            linear = joint.linear_separation
            angular = math.degrees(joint.angular_separation)
            self.debug_draw.draw_string(joint.local_frame_a.p, f"{linear:.2f} m, {angular:.1f} deg", WHITE)


@register_sample("Joints", "User Constraint")
class UserConstraint(JointSample):
    """This shows how you can implement a constraint outside of Box2D."""

    camera_center = (3.0, -1.0)
    camera_zoom = 25.0 * 0.15

    hertz = 3.0
    zeta = 0.7
    max_force = 1000.0
    local_anchors = ((1.0, -0.5), (1.0, 0.5))
    anchor_a = (3.0, 0.0)
    slack_length = 1.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.body = self.world.create_dynamic_body(gravity_scale=1.0, angular_damping=0.5, linear_damping=0.2)
        self.body.create_shape(b2d.shape_def(density=20.0), b2d.box(1.0, 0.5))
        self.impulses = [0.0, 0.0]
        self.lines = []

    def post_update(self, dt):
        self.lines = []
        if dt == 0.0:
            return

        omega = 2.0 * math.pi * self.hertz
        sigma = 2.0 * self.zeta + dt * omega
        s = dt * omega * sigma
        impulse_coefficient = 1.0 / (1.0 + s)
        mass_coefficient = s * impulse_coefficient
        bias_coefficient = omega / sigma

        body = self.body
        mass = body.mass
        inv_mass = 0.0 if mass < 0.0001 else 1.0 / mass
        inertia = body.rotational_inertia
        inv_i = 0.0 if inertia < 0.0001 else 1.0 / inertia

        v_b = body.linear_velocity
        omega_b = body.angular_velocity
        p_b = body.world_center

        for i, local_anchor in enumerate(self.local_anchors):
            anchor_b = body.world_point(local_anchor)
            delta_anchor = anchor_b - self.anchor_a

            length = b2d.length(delta_anchor)
            c = length - self.slack_length
            if c < 0.0 or length < 0.001:
                self.lines.append((anchor_b, b2d.HexColor.LightCyan.value))
                self.impulses[i] = 0.0
                continue

            self.lines.append((anchor_b, b2d.HexColor.Violet.value))
            axis = b2d.normalize(delta_anchor)

            r_b = anchor_b - p_b
            jb = b2d.cross(r_b, axis)
            k = inv_mass + jb * inv_i * jb
            inv_k = 0.0 if k < 0.0001 else 1.0 / k

            c_dot = b2d.dot(v_b, axis) + jb * omega_b
            impulse = -mass_coefficient * inv_k * (c_dot + bias_coefficient * c)
            applied_impulse = min(max(impulse, -self.max_force * dt), 0.0)

            v_b = b2d.mul_add(v_b, inv_mass * applied_impulse, axis)
            omega_b += applied_impulse * inv_i * jb

            self.impulses[i] = applied_impulse

        body.linear_velocity = v_b
        body.angular_velocity = omega_b

    def post_debug_draw(self):
        self.debug_draw.draw_transform(b2d.transform())
        for anchor_b, color in self.lines:
            self.debug_draw.draw_segment(self.anchor_a, anchor_b, color)


@register_sample("Joints", "Driving")
class Driving(JointSample):
    """This is a fun demo that shows off the wheel joint. Keys: left = a, brake = s, right = d."""

    camera_center = (0.0, 5.0)
    camera_zoom = 25.0 * 0.4

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = world.create_static_body()

        # the terrain, in reverse to match the line list convention
        heights = (0.25, 1.0, 4.0, 0.0, 0.0, -1.0, -2.0, -2.0, -1.25, 0.0)
        x, dx = 20.0, 5.0
        points = [(-20.0, -20.0), (-20.0, 0.0), (20.0, 0.0)]
        for _ in range(2):
            for h in heights:
                x += dx
                points.append((x, h))
        # flat before bridge
        points += [(x + 40.0, 0.0), (x + 40.0, -20.0)]
        ground.create_chain(b2d.chain_def(points=points[::-1], is_loop=True))

        shape_def = b2d.shape_def()
        # flat after bridge, jump ramp, final corner
        x += 80.0
        segments = [((x, 0.0), (x + 40.0, 0.0))]
        x += 40.0
        segments.append(((x, 0.0), (x + 10.0, 5.0)))
        x += 20.0
        segments.append(((x, 0.0), (x + 40.0, 0.0)))
        x += 40.0
        segments.append(((x, 0.0), (x, 20.0)))
        for p1, p2 in segments:
            ground.create_shape(shape_def, b2d.segment(p1, p2))

        # teeter
        teeter = world.create_dynamic_body(position=(140.0, 1.0), angular_velocity=1.0)
        teeter.create_shape(b2d.shape_def(), b2d.box(10.0, 0.25))
        world.create_revolute_joint(
            **pinned(ground, teeter, (140.0, 1.0)),
            lower_angle=degrees_to_radians(-8.0),
            upper_angle=degrees_to_radians(8.0),
            enable_limit=True,
        )

        # bridge
        n = 20
        capsule = b2d.capsule((-1.0, 0.0), (1.0, 0.0), 0.125)
        prev = ground
        for i in range(n):
            body = world.create_dynamic_body(position=(161.0 + 2.0 * i, -0.125))
            body.create_shape(shape_def, capsule)
            world.create_revolute_joint(**pinned(prev, body, (160.0 + 2.0 * i, -0.125)))
            prev = body
        world.create_revolute_joint(
            **pinned(prev, ground, (160.0 + 2.0 * n, -0.125)), enable_motor=True, max_motor_torque=50.0
        )

        # boxes
        box_def = b2d.shape_def(density=0.25, material=b2d.surface_material(friction=0.25, restitution=0.25))
        for y in (0.5, 1.5, 2.5, 3.5, 4.5):
            body = world.create_dynamic_body(position=(230.0, y))
            body.create_shape(box_def, b2d.box(0.5, 0.5))

        self.throttle = 0.0
        self.speed = 35.0
        self.torque = 5.0
        self.hertz = 5.0
        self.damping_ratio = 0.7
        self.car = Car(world, (0.0, 0.0), 1.0, self.hertz, self.damping_ratio, self.torque)
        self.camera_x = self.camera_center[0]

        self.add_widgets(
            slider("Spring Hertz", 0.0, 20.0, self.hertz, self.car.set_hertz, step=1.0),
            slider("Damping Ratio", 0.0, 10.0, self.damping_ratio, self.car.set_damping_ratio),
            slider("Speed", 0.0, 50.0, self.speed, self.set_speed, step=1.0),
            slider("Torque", 0.0, 10.0, self.torque, self.car.set_torque),
        )

    def set_speed(self, value):
        self.speed = value
        self.car.set_speed(self.throttle * self.speed)

    def on_key_down(self, event):
        throttle = {"a": 1.0, "s": 0.0, "d": -1.0}.get(event.key)
        if throttle is not None:
            self.throttle = throttle
            self.car.set_speed(throttle * self.speed)

    def post_update(self, dt):
        # the camera follows the car
        x = self.car.chassis.position.x
        self.frontend.drag_camera((self.camera_x - x, 0.0))
        self.camera_x = x


class RagdollBase(JointSample):
    """Spawns a Human; derived classes set the spawn parameters."""

    spawn_position = (0.0, 0.0)
    joint_friction_torque = 0.03
    joint_hertz = 5.0
    joint_damping_ratio = 0.5

    def spawn(self, scale=1.0):
        self.human = Human(
            self.world,
            self.spawn_position,
            scale,
            self.joint_friction_torque,
            self.joint_hertz,
            self.joint_damping_ratio,
            group_index=1,
        )


@register_sample("Joints", "Ragdoll")
class Ragdoll(RagdollBase):
    """A ragdoll with joint friction and joint springs."""

    camera_center = (0.0, 12.0)
    camera_zoom = 16.0
    spawn_position = (0.0, 25.0)

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment()
        self.spawn()
        self.world.set_contact_tuning(240.0, 0.0, 2.0)

        self.add_widgets(
            slider("Friction", 0.0, 1.0, self.joint_friction_torque, self.set_friction),
            slider("Hertz", 0.0, 10.0, self.joint_hertz, self.set_hertz),
            slider("Damping", 0.0, 4.0, self.joint_damping_ratio, self.set_damping_ratio),
            Button("Respawn", self.respawn),
        )

    def set_friction(self, value):
        self.joint_friction_torque = value
        self.human.set_joint_friction_torque(value)

    def set_hertz(self, value):
        self.joint_hertz = value
        self.human.set_joint_spring_hertz(value)

    def set_damping_ratio(self, value):
        self.joint_damping_ratio = value
        self.human.set_joint_damping_ratio(value)

    def respawn(self):
        self.human.destroy()
        self.spawn()


@register_sample("Joints", "Soft Body")
class SoftBody(JointSample):
    """A donut made of capsules and soft weld joints."""

    camera_center = (0.0, 5.0)
    camera_zoom = 25.0 * 0.25

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment()
        self.donut = Donut(self.world, (0.0, 10.0), 2.0)


@register_sample("Joints", "Doohickey")
class DoohickeyFarm(JointSample):
    """Wheels and bars connected by revolute and prismatic joints."""

    camera_center = (0.0, 5.0)
    camera_zoom = 25.0 * 0.35

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.create_ground_segment()
        ground.create_shape(b2d.shape_def(), b2d.box(1.0, 1.0, center=(0.0, 1.0)))

        self.doohickeys = [Doohickey(self.world, (0.0, 4.0 + 2.0 * i), 0.5) for i in range(4)]


@register_sample("Joints", "Scissor Lift")
class ScissorLift(JointSample):
    """A scissor lift driven by a distance joint motor, carrying a car."""

    camera_center = (0.0, 9.0)
    camera_zoom = 25.0 * 0.4
    # need 8 sub-steps for smoother operation
    substeps = 8

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = self.create_ground_segment()

        body_def = b2d.body_def(type=b2d.BodyType.DYNAMIC, sleep_threshold=0.01)
        shape_def = b2d.shape_def()
        capsule = b2d.capsule((-2.5, 0.0), (2.5, 0.0), 0.15)
        tuning = dict(constraint_damping_ratio=20.0, constraint_hertz=240.0)

        def revolute(body_a, body_b, anchor_a, anchor_b, collide_connected):
            world.create_revolute_joint(
                body_a=body_a,
                body_b=body_b,
                local_anchor_a=anchor_a,
                local_anchor_b=anchor_b,
                collide_connected=collide_connected,
                **tuning,
            )

        def wheel(body_a, body_b, anchor_a, anchor_b):
            world.create_wheel_joint(
                body_a=body_a,
                body_b=body_b,
                local_anchor_a=anchor_a,
                local_anchor_b=anchor_b,
                enable_spring=False,
                collide_connected=True,
                **tuning,
            )

        base1 = base2 = ground
        base_anchor1, base_anchor2 = (-2.5, 0.2), (2.5, 0.2)
        y = 0.5
        link1 = None
        for i in range(3):
            body1 = world.create_body(body_def, position=(0.0, y), rotation=0.15)
            body1.create_shape(shape_def, capsule)
            body2 = world.create_body(body_def, position=(0.0, y), rotation=-0.15)
            body2.create_shape(shape_def, capsule)
            if i == 1:
                link1 = body2

            # left pin
            revolute(base1, body1, base_anchor1, (-2.5, 0.0), collide_connected=i == 0)
            # right pin
            if i == 0:
                wheel(base2, body2, base_anchor2, (2.5, 0.0))
            else:
                revolute(base2, body2, base_anchor2, (2.5, 0.0), collide_connected=False)
            # middle pin
            revolute(body1, body2, (0.0, 0.0), (0.0, 0.0), collide_connected=False)

            base1, base2 = body2, body1
            base_anchor1, base_anchor2 = (-2.5, 0.0), (2.5, 0.0)
            y += 1.0

        platform = world.create_body(body_def, position=(0.0, y), rotation=0.0)
        platform.create_shape(shape_def, b2d.box(3.0, 0.2))
        revolute(platform, base1, (-2.5, -0.4), base_anchor1, collide_connected=True)
        wheel(platform, base2, (2.5, -0.4), base_anchor2)

        self.enable_motor = False
        self.motor_speed = 0.25
        self.motor_force = 2000.0
        self.lift_joint = world.create_distance_joint(
            body_a=ground,
            body_b=link1,
            local_anchor_a=(-2.5, 0.2),
            local_anchor_b=(0.5, 0.0),
            enable_spring=True,
            min_length=0.2,
            max_length=5.5,
            enable_limit=True,
            enable_motor=self.enable_motor,
            motor_speed=self.motor_speed,
            max_motor_force=self.motor_force,
        )

        self.car = Car(world, (0.0, y + 2.0), 1.0, 3.0, 0.7, 0.0)

        joints = [self.lift_joint]
        self.add_widgets(
            Checkbox("Motor", self.enable_motor, joint_setter(joints, "motor_enabled")),
            slider("Max Force", 0.0, 3000.0, self.motor_force, joint_setter(joints, "max_motor_force")),
            slider("Speed", -0.3, 0.3, self.motor_speed, joint_setter(joints, "target_motor_speed")),
        )


GEAR_LIFT_PATH = (
    "m 63.500002,201.08333 103.187498,0 1e-5,-37.04166 h -2.64584 l 0,34.39583 h -42.33333 v -2.64583 l "
    "-2.64584,-1e-5 v -2.64583 h -2.64583 v -2.64584 h -2.64584 v -2.64583 H 111.125 v -2.64583 h -2.64583 v "
    "-2.64583 h -2.64583 v -2.64584 l -2.64584,1e-5 v -2.64583 l -2.64583,-1e-5 V 174.625 h -2.645834 v -2.64584 l "
    "-2.645833,1e-5 v -2.64584 H 92.60417 v -2.64583 h -2.645834 v -2.64583 l -26.458334,0 0,37.04166"
)


@register_sample("Joints", "Gear Lift")
class GearLift(JointSample):
    """A motorized gear pulls a door up with a chain. Keys: a / d change the motor speed."""

    camera_center = (0.0, 6.0)
    camera_zoom = 7.0

    gear_radius = 1.0
    tooth_half_width = 0.09
    tooth_half_height = 0.06
    tooth_radius = 0.03
    link_half_length = 0.07
    link_radius = 0.05
    link_count = 40
    door_half_height = 1.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        points = parse_path(GEAR_LIFT_PATH, offset=(-120.0, -200.0), scale=0.2)
        material = b2d.surface_material(custom_color=b2d.HexColor.DarkSeaGreen.value)
        ground.create_chain(b2d.chain_def(points=points, material=material, is_loop=True))

        gear_position1 = b2d.Vec2(-4.25, 9.75)
        gear_position2 = gear_position1 + (2.0, 1.0)
        link_attach_position = gear_position2 + (self.gear_radius + 2.0 * self.tooth_half_width + self.tooth_radius, 0.0)
        door_position = link_attach_position - (0.0, 2.0 * self.link_count * self.link_half_length + self.door_half_height)

        # the driver gear
        self.motor_torque = 80.0
        self.motor_speed = 0.0
        self.enable_motor = True
        driver = self.create_gear(gear_position1, self.tooth_half_height)
        self.driver_joint = world.create_revolute_joint(
            body_a=ground,
            body_b=driver,
            local_anchor_a=ground.local_point(gear_position1),
            local_anchor_b=(0.0, 0.0),
            enable_motor=self.enable_motor,
            max_motor_torque=self.motor_torque,
            motor_speed=self.motor_speed,
        )

        # the follower gear
        follower = self.create_gear(gear_position2, self.tooth_half_width)
        world.create_revolute_joint(
            body_a=ground,
            body_b=follower,
            local_frame_a=b2d.transform(p=ground.local_point(gear_position2), q=0.25 * math.pi),
            local_anchor_b=(0.0, 0.0),
            enable_motor=True,
            max_motor_torque=0.5,
            lower_angle=-0.3 * math.pi,
            upper_angle=0.8 * math.pi,
            enable_limit=True,
        )

        # the chain
        link_capsule = b2d.capsule((0.0, -self.link_half_length), (0.0, self.link_half_length), self.link_radius)
        link_def = b2d.shape_def(density=2.0, material=b2d.surface_material(custom_color=b2d.HexColor.LightSteelBlue.value))
        position = link_attach_position - (0.0, self.link_half_length)
        prev = follower
        for _ in range(self.link_count):
            body = world.create_dynamic_body(position=position)
            body.create_shape(link_def, link_capsule)
            world.create_revolute_joint(
                **pinned(prev, body, position + (0.0, self.link_half_length)),
                max_motor_torque=0.05,
                enable_motor=True,
                draw_scale=0.2,
            )
            position = position - (0.0, 2.0 * self.link_half_length)
            prev = body

        # the door
        door = world.create_dynamic_body(position=door_position)
        door_def = b2d.shape_def(material=b2d.surface_material(friction=0.1, custom_color=b2d.HexColor.DarkCyan.value))
        door.create_shape(door_def, b2d.box(0.15, self.door_half_height))
        world.create_revolute_joint(
            body_a=prev,
            body_b=door,
            local_anchor_a=prev.local_point(door_position + (0.0, self.door_half_height)),
            local_anchor_b=(0.0, self.door_half_height),
            enable_motor=True,
            max_motor_torque=0.05,
        )
        axis = b2d.make_rot_from_unit_vector((0.0, 1.0))
        world.create_prismatic_joint(
            body_a=ground,
            body_b=door,
            local_frame_a=b2d.transform(p=ground.local_point(door_position), q=axis),
            local_frame_b=b2d.transform(q=axis),
            max_motor_force=0.2,
            enable_motor=True,
            collide_connected=True,
        )

        # the rubble
        colors = [
            getattr(b2d.HexColor, name).value for name in ("Gray", "Gainsboro", "LightGray", "LightSlateGray", "DarkGray")
        ]
        for i in range(20):
            for j in range(10):
                body = world.create_dynamic_body(position=(-3.15 + 0.2 * j, 4.25 + 0.2 * i))
                shape_def = b2d.shape_def(
                    material=b2d.surface_material(rolling_resistance=0.3, custom_color=random.choice(colors))
                )
                body.create_shape(shape_def, random_polygon(0.1, radius=random.uniform(0.01, 0.02)))

        joints = [self.driver_joint]
        self.add_widgets(
            Checkbox("Motor", self.enable_motor, joint_setter(joints, "motor_enabled")),
            slider("Max Torque", 0.0, 100.0, self.motor_torque, joint_setter(joints, "max_motor_torque")),
            slider("Speed", -0.3, 0.3, self.motor_speed, self.set_motor_speed),
        )

    def create_gear(self, position, tooth_offset):
        body = self.world.create_dynamic_body(position=position)
        hub_def = b2d.shape_def(material=b2d.surface_material(friction=0.1, custom_color=b2d.HexColor.SaddleBrown.value))
        body.create_shape(hub_def, b2d.circle(radius=self.gear_radius))

        tooth_def = b2d.shape_def(material=b2d.surface_material(friction=0.1, custom_color=b2d.HexColor.Gray.value))
        count = 16
        for i in range(count):
            angle = 2.0 * math.pi * i / count
            center = b2d.rotate_vector(b2d.make_rot(angle), (self.gear_radius + tooth_offset, 0.0))
            tooth = b2d.box(
                self.tooth_half_width, self.tooth_half_height, center=center, rotation=angle, radius=self.tooth_radius
            )
            body.create_shape(tooth_def, tooth)
        return body

    def set_motor_speed(self, value):
        self.motor_speed = value
        self.driver_joint.target_motor_speed = value
        self.driver_joint.wake_bodies()

    def pre_update(self, dt):
        if self.is_key_pressed("a"):
            self.set_motor_speed(max(-0.3, self.motor_speed - 0.01))
        if self.is_key_pressed("d"):
            self.set_motor_speed(min(0.3, self.motor_speed + 0.01))


@register_sample("Joints", "Door")
class Door(JointSample):
    """A top down door."""

    camera_center = (0.0, 0.0)
    camera_zoom = 4.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = world.create_static_body(position=(0.0, 0.0))

        self.enable_limit = True
        self.impulse = 50000.0
        self.translation_error = 0.0
        self.joint_hertz = 240.0
        self.joint_damping_ratio = 1.0

        self.door = world.create_dynamic_body(position=(0.0, 1.5), gravity_scale=0.0)
        self.door.create_shape(b2d.shape_def(density=1000.0), b2d.box(0.1, 1.5))
        self.joint = world.create_revolute_joint(
            body_a=ground,
            body_b=self.door,
            local_anchor_a=(0.0, 0.0),
            local_anchor_b=(0.0, -1.5),
            constraint_hertz=self.joint_hertz,
            constraint_damping_ratio=self.joint_damping_ratio,
            target_angle=0.0,
            enable_spring=True,
            hertz=1.0,
            damping_ratio=0.5,
            motor_speed=0.0,
            max_motor_torque=0.0,
            enable_motor=False,
            lower_angle=-0.5 * math.pi,
            upper_angle=0.5 * math.pi,
            enable_limit=self.enable_limit,
        )

        self.add_widgets(
            Button("impulse", self.apply_impulse),
            slider("magnitude", 1000.0, 100000.0, self.impulse, self.set_impulse, step=1000.0),
            slider("hertz", 15.0, 480.0, self.joint_hertz, self.set_joint_hertz, step=1.0),
            slider("damping", 0.0, 10.0, self.joint_damping_ratio, self.set_joint_damping_ratio),
            Checkbox("limit", self.enable_limit, joint_setter([self.joint], "limit_enabled", False)),
        )

    def apply_impulse(self):
        self.door.apply_linear_impulse((self.impulse, 0.0), self.door.world_point((0.0, 1.5)), True)
        self.translation_error = 0.0

    def set_impulse(self, value):
        self.impulse = value

    def set_joint_hertz(self, value):
        self.joint_hertz = value
        self.joint.set_constraint_tuning(self.joint_hertz, self.joint_damping_ratio)

    def set_joint_damping_ratio(self, value):
        self.joint_damping_ratio = value
        self.joint.set_constraint_tuning(self.joint_hertz, self.joint_damping_ratio)

    def post_update(self, dt):
        self.translation_error = max(self.translation_error, self.joint.linear_separation)

    def post_debug_draw(self):
        self.debug_draw.draw_point(self.door.world_point((0.0, 1.5)), 5.0, b2d.HexColor.DarkKhaki.value)


@register_sample("Joints", "Scale Ragdoll")
class ScaleRagdoll(RagdollBase):
    """Scale a ragdoll at runtime by resizing its shapes and joint frames."""

    camera_center = (0.0, 4.5)
    camera_zoom = 6.0
    spawn_position = (0.0, 5.0)
    joint_hertz = 1.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        ground.create_shape(b2d.shape_def(), b2d.box(20.0, 1.0, center=(0.0, -1.0)))

        self.scale = 1.0
        self.spawn(self.scale)
        self.human.apply_random_angular_impulse(0.1)

        self.add_widgets(slider("Scale", 0.1, 10.0, self.scale, self.human.set_scale))


@register_sample("Joints", "Theo Jansen")
class TheoJansen(JointSample):
    """Theo Jansen's walking machine, inspired by a contribution from roman_m.
    Keys: left = a, brake = s, right = d, toggle motor = f."""

    camera_center = (0.0, 6.0)
    camera_zoom = 25.0 * 0.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        self.offset = b2d.Vec2(0.0, 8.0)
        self.motor_speed = 2.0
        self.enable_motor = True
        pivot = b2d.Vec2(0.0, 0.8)

        ground = world.create_static_body()
        for p1, p2 in (((-50.0, 0.0), (50.0, 0.0)), ((-50.0, 0.0), (-50.0, 10.0)), ((50.0, 0.0), (50.0, 10.0))):
            ground.create_shape(b2d.shape_def(), b2d.segment(p1, p2))

        for i in range(40):
            ball = world.create_dynamic_body(position=(-40.0 + 2.0 * i, 0.5))
            ball.create_shape(b2d.shape_def(density=1.0), b2d.circle(radius=0.25))

        # negative group index keeps the legs from colliding with the chassis and wheel
        self.shape_def = b2d.shape_def(density=1.0, filter=b2d.make_filter(group_index=-1))

        self.chassis = world.create_dynamic_body(position=pivot + self.offset)
        self.chassis.create_shape(self.shape_def, b2d.box(2.5, 1.0))

        self.wheel = world.create_dynamic_body(position=pivot + self.offset)
        self.wheel.create_shape(self.shape_def, b2d.circle(radius=1.6))

        self.motor_joint = world.create_revolute_joint(
            **pinned(self.wheel, self.chassis, pivot + self.offset),
            enable_motor=self.enable_motor,
            motor_speed=self.motor_speed,
            max_motor_torque=400.0,
        )

        wheel_anchor = pivot + (0.0, -0.8)

        # stagger three leg pairs around the wheel so some feet always touch the ground
        for angle in (0.0, 120.0, -120.0):
            if angle != 0.0:
                self.wheel.set_transform(self.wheel.position, b2d.make_rot(degrees_to_radians(angle)))
            self.create_leg(-1.0, wheel_anchor)
            self.create_leg(1.0, wheel_anchor)

        joints = [self.motor_joint]
        self.add_widgets(
            Checkbox("Motor", self.enable_motor, joint_setter(joints, "motor_enabled", False)),
            slider("Speed", -5.0, 5.0, self.motor_speed, self.set_motor_speed),
        )

    def create_leg(self, s, wheel_anchor):
        world = self.world
        offset = self.offset
        p1 = b2d.Vec2(5.4 * s, -6.1)
        p2 = b2d.Vec2(7.2 * s, -1.2)
        p3 = b2d.Vec2(4.3 * s, -1.9)
        p4 = b2d.Vec2(3.1 * s, 0.8)
        p5 = b2d.Vec2(6.0 * s, 1.5)
        p6 = b2d.Vec2(2.5 * s, 3.7)

        # the hull computation handles the mirrored winding for s < 0
        body1 = world.create_dynamic_body(position=offset, angular_damping=10.0)
        body1.create_shape(self.shape_def, b2d.polygon([p1, p2, p3]))
        body2 = world.create_dynamic_body(position=p4 + offset, angular_damping=10.0)
        body2.create_shape(self.shape_def, b2d.polygon([(0.0, 0.0), p5 - p4, p6 - p4]))

        # soft distance constraints reduce jitter and act like a suspension system
        def spring(body_a, body_b, anchor_a, anchor_b):
            world.create_distance_joint(
                **pinned(body_a, body_b, anchor_a, anchor_b),
                length=b2d.length(anchor_a - anchor_b),
                enable_spring=True,
                hertz=10.0,
                damping_ratio=0.5,
            )

        spring(body1, body2, p2 + offset, p5 + offset)
        spring(body1, body2, p3 + offset, p4 + offset)
        spring(body1, self.wheel, p3 + offset, wheel_anchor + offset)
        spring(body2, self.wheel, p6 + offset, wheel_anchor + offset)

        world.create_revolute_joint(**pinned(body2, self.chassis, p4 + offset))

    def set_motor_speed(self, value):
        self.motor_speed = value
        self.motor_joint.target_motor_speed = value

    def on_key_down(self, event):
        if event.key == "a":
            self.motor_joint.target_motor_speed = -self.motor_speed
        elif event.key == "s":
            self.motor_joint.target_motor_speed = 0.0
        elif event.key == "d":
            self.motor_joint.target_motor_speed = self.motor_speed
        elif event.key == "f":
            self.motor_joint.motor_enabled = not self.motor_joint.motor_enabled


@register_sample("Joints", "Desk Lamp")
class DeskLamp(JointSample):
    """The Anglepoise Original 1227 desk lamp (https://www.anglepoise.com/usa/product-category/original-1227/)."""

    camera_center = (0.2, 1.42)
    camera_zoom = 1.6
    # the parallelogram is narrow, so it wants the extra resolution
    substeps = 8

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        self.create_ground_segment()

        # Dimensions taken off an Original 1227 in meters, then scaled up. At life size the silver
        # link is two centimeters, which is far too close to the linear slop.
        scale = 5.0
        base_half_width = 0.070 * scale
        base_half_height = 0.018 * scale
        post_half_width = 0.008 * scale
        pivot_height = 0.185 * scale
        spring_anchor_height = 0.095 * scale
        top_link_length = 0.296 * scale
        silver_foot = 0.024 * scale
        top_lever_length = 0.019 * scale
        lower_lever_length = 0.028 * scale
        upper_arm_length = 0.324 * scale
        tube_radius = 0.0036 * scale
        shade_length = 0.161 * scale
        shade_neck_radius = 0.020 * scale
        shade_mouth_radius = 0.061 * scale

        # The silver link measured in the top link frame. The same span separates the two pins on the
        # upper arm, which is what closes the parallelogram.
        silver_span = (0.0212 * scale, 0.0109 * scale)
        silver_length = b2d.length(silver_span)

        top_link_angle = -0.878
        upper_arm_angle = 1.192
        shade_tilt = -0.41

        # The arm spring balances the elevation, the head spring balances the upper arm through the
        # parallelogram. That is what the real lamp uses two springs for.
        self.spring_hertz = [5.0, 5.0]
        self.spring_damping = 4.0
        self.lower_friction = 100.0
        self.elbow_friction = 100.0
        self.head_angle = 0.0
        top_rotation = b2d.make_rot(top_link_angle)
        upper_rotation = b2d.make_rot(upper_arm_angle)

        top_axis = top_rotation.y_axis
        silver_world = b2d.rotate_vector(top_rotation, silver_span)

        post_pivot = b2d.Vec2(0.0, pivot_height)
        upper_pin = post_pivot + top_axis * top_link_length
        silver_base = post_pivot + top_axis * silver_foot
        lower_foot = silver_base + silver_world
        lower_pin = upper_pin + silver_world

        # the lower link is parallel to the top link and shorter by the silver link foot
        lower_link_length = top_link_length - silver_foot
        silver_rotation = b2d.make_rot_from_unit_vector(b2d.right_perp(b2d.normalize(silver_world)))

        head_pivot = upper_pin + upper_rotation.y_axis * upper_arm_length

        # the base is static so the linkage is all that moves
        base = world.create_static_body()
        post_half_height = 0.5 * (pivot_height - 2.0 * base_half_height)
        base.create_shape(b2d.shape_def(), b2d.box(base_half_width, base_half_height, center=(0.0, base_half_height)))
        base.create_shape(
            b2d.shape_def(), b2d.box(post_half_width, post_half_height, center=(0.0, pivot_height - post_half_height))
        )

        link_def = b2d.shape_def(density=20.0)

        def link(position, rotation, capsules, shape_def=link_def):
            body = world.create_dynamic_body(position=position, rotation=rotation)
            for capsule in capsules:
                body.create_shape(shape_def, capsule)
            return body

        # both long links run past their feet into the levers the springs pull on
        self.top_link = link(
            post_pivot, top_rotation, [b2d.capsule((0.0, -top_lever_length), (0.0, top_link_length), tube_radius)]
        )
        lower_link = link(
            lower_foot, top_rotation, [b2d.capsule((0.0, -lower_lever_length), (0.0, lower_link_length), tube_radius)]
        )
        silver_def = b2d.shape_def(density=20.0, material=b2d.surface_material(custom_color=b2d.HexColor.Silver.value))
        silver = link(
            silver_base, silver_rotation, [b2d.capsule((0.0, 0.0), (0.0, silver_length), 1.4 * tube_radius)], silver_def
        )
        upper_arm = link(upper_pin, upper_rotation, [b2d.capsule((0.0, 0.0), (0.0, upper_arm_length), 0.8 * tube_radius)])
        # the coupler span reaches back to the lower link pin
        upper_arm.create_shape(link_def, b2d.capsule((0.0, 0.0), upper_arm.local_point(lower_pin), tube_radius))

        pin_def = dict(draw_scale=0.03 * scale, constraint_hertz=240.0, constraint_damping_ratio=2.0)

        def pin(body_a, body_b, anchor_a, anchor_b=(0.0, 0.0), **kwargs):
            return world.create_revolute_joint(
                body_a=body_a, body_b=body_b, local_anchor_a=anchor_a, local_anchor_b=anchor_b, **pin_def, **kwargs
            )

        # only the top link reaches the post, the springs carry it, so it needs little friction
        self.post_joint = pin(
            base, self.top_link, base.local_point(post_pivot), enable_motor=True, max_motor_torque=self.lower_friction
        )
        # the silver link hangs off the top link and carries the foot of the lower link
        pin(self.top_link, silver, (0.0, silver_foot))
        pin(silver, lower_link, (0.0, silver_length))
        # both long links reach the upper arm, at points a silver link apart
        pin(lower_link, upper_arm, (0.0, lower_link_length), upper_arm.local_point(lower_pin))
        # no spring reaches the elbow, so it is a friction pivot like the real one
        self.elbow_joint = pin(
            self.top_link, upper_arm, (0.0, top_link_length), enable_motor=True, max_motor_torque=self.elbow_friction
        )

        # Carwardine's trick. With almost no free length the spring torque about the pivot is
        # k times cross(lever, anchor), which tracks the gravity torque as the arm swings, so the
        # arm balances over its whole range instead of at one angle.
        spring_base = (0.0, spring_anchor_height)
        self.spring_joints = [
            world.create_distance_joint(
                body_a=base,
                body_b=lever,
                local_anchor_a=base.local_point(spring_base),
                local_anchor_b=(0.0, -lever_length),
                draw_scale=0.03 * scale,
                enable_spring=True,
                damping_ratio=self.spring_damping,
                length=0.01,
                hertz=hertz,
            )
            for lever, lever_length, hertz in (
                (self.top_link, top_lever_length, self.spring_hertz[0]),
                (lower_link, lower_lever_length, self.spring_hertz[1]),
            )
        ]

        # The pivot is on the shade center line, where the arm capsule ends. The shade opens along
        # the local negative y.
        neck = 0.45 * shade_length
        mouth = neck - shade_length
        shade = b2d.polygon(
            [
                (-shade_neck_radius, neck),
                (shade_neck_radius, neck),
                (shade_mouth_radius, mouth),
                (-shade_mouth_radius, mouth),
            ],
            radius=0.01 * scale,
        )
        # the shade is a thin shell
        head = link(head_pivot, shade_tilt, [shade], b2d.shape_def(density=1.0))

        # offset the reference frame so the head slider reads zero at the pose above
        self.head_joint = world.create_revolute_joint(
            body_a=upper_arm,
            body_b=head,
            local_frame_a=b2d.transform(
                p=(0.0, upper_arm_length), q=b2d.inv_mul_rot(upper_rotation, b2d.make_rot(shade_tilt))
            ),
            enable_motor=False,
            max_motor_torque=10.0,
            enable_spring=True,
            hertz=8.0,
            damping_ratio=2.0,
            target_angle=self.head_angle,
            enable_limit=True,
            lower_angle=-1.2,
            upper_angle=1.2,
            **pin_def,
        )

        springs = self.spring_joints
        self.add_widgets(
            slider("Arm Spring", 0.0, 20.0, self.spring_hertz[0], joint_setter(springs[:1], "spring_hertz")),
            slider("Head Spring", 0.0, 20.0, self.spring_hertz[1], joint_setter(springs[1:], "spring_hertz")),
            slider("Spring Damping", 0.0, 5.0, self.spring_damping, joint_setter(springs, "spring_damping_ratio")),
            slider("Post Friction", 0.0, 20.0, self.lower_friction, joint_setter([self.post_joint], "max_motor_torque")),
            slider("Elbow Friction", 0.0, 60.0, self.elbow_friction, joint_setter([self.elbow_joint], "max_motor_torque")),
            slider("Head", -1.2, 1.2, self.head_angle, joint_setter([self.head_joint], "target_angle")),
        )
