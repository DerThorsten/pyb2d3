"""Helpers for the ports of box2d's samples/sample_joints.cpp.

Car, Donut and Doohickey port samples/car.cpp, donut.cpp and doohickey.cpp,
Human ports shared/human.c.
"""

import math
import random

import pyb2d3 as b2d
from pyb2d3_sandbox import widgets

from ..examples_common.joints import pinned  # noqa: F401  (re-exported for the joint samples)
from ..examples_common.ragdoll import Human  # noqa: F401  (re-exported for the joint samples)
from ._common import Box2dSample

LINEAR_SLOP = 0.005


class JointSample(Box2dSample):
    """Box2dSample with widget shortcuts."""

    def add_widgets(self, *elements):
        for element in elements:
            self.frontend.add_widget(element)


def slider(label, min_value, max_value, value, callback, step=None):
    """A FloatSlider with 100 steps by default."""
    step = (max_value - min_value) / 100 if step is None else step
    return widgets.FloatSlider(label, min_value, max_value, step, value, callback)


def joint_setter(joints, attr, wake=True):
    """Widget callback setting `attr` on every joint (`joints` may be a callable returning them)."""

    def callback(value):
        for joint in joints() if callable(joints) else joints:
            setattr(joint, attr, value)
            if wake:
                joint.wake_bodies()

    return callback


def random_polygon(extent, radius=0.0):
    """Port of RandomPolygon (shared/utils.c), optionally rounded."""
    count = random.randint(3, 8)
    points = [
        (random.uniform(-extent, extent), random.uniform(-extent, extent)) for _ in range(count)
    ]
    hull = b2d.compute_hull(points)
    if hull.count > 0:
        return b2d.make_polygon(hull, radius)
    return b2d.box(extent, extent, radius=radius)


def parse_path(svg_path, offset, scale):
    """Port of Sample::ParsePath: an svg path with straight lines only, the loop point removed."""
    points = []
    x = y = 0.0
    command = None
    for token in svg_path.split():
        if token[0].isalpha():
            command = token
            if command == "z":
                break
            continue
        if command in "MLml":
            dx, dy = (float(v) for v in token.split(","))
            x, y = (dx, dy) if command in "ML" else (x + dx, y + dy)
        elif command in "Hh":
            x = float(token) + (x if command == "h" else 0.0)
        elif command in "Vv":
            y = float(token) + (y if command == "v" else 0.0)
        points.append((scale * (x + offset[0]), -scale * (y + offset[1])))
    if len(points) > 2 and math.dist(points[0], points[-1]) <= LINEAR_SLOP:
        points.pop()
    return points


# Car (samples/car.cpp)
class Car:
    vertices = ((-1.5, -0.5), (1.5, -0.5), (1.5, 0.0), (0.0, 0.9), (-1.15, 0.9), (-1.5, 0.2))

    def __init__(self, world, position, scale, hertz, damping_ratio, torque):
        position = b2d.Vec2(position)
        chassis = b2d.polygon(
            [(0.85 * scale * x, 0.85 * scale * y) for x, y in self.vertices], radius=0.15 * scale
        )

        self.chassis = world.create_dynamic_body(position=position + (0.0, scale))
        self.chassis.create_shape(
            b2d.shape_def(density=1.0 / scale, material=b2d.surface_material(friction=0.2)), chassis
        )

        wheel_def = b2d.shape_def(
            density=2.0 / scale, material=b2d.surface_material(friction=1.5, rolling_resistance=0.1)
        )
        self.wheels = []
        for offset in ((-1.0, 0.35), (1.0, 0.4)):
            wheel = world.create_dynamic_body(
                position=position + (offset[0] * scale, offset[1] * scale), allow_fast_rotation=True
            )
            wheel.create_shape(wheel_def, b2d.circle(radius=0.4 * scale))
            self.wheels.append(wheel)

        self.rear_wheel, self.front_wheel = self.wheels
        self.axles = [
            world.create_wheel_joint(
                **pinned(self.chassis, wheel, wheel.position, q_a=0.5 * math.pi),
                motor_speed=0.0,
                max_motor_torque=torque,
                enable_motor=True,
                hertz=hertz,
                damping_ratio=damping_ratio,
                lower_translation=-0.25 * scale,
                upper_translation=0.25 * scale,
                enable_limit=True,
            )
            for wheel in self.wheels
        ]

    def set_speed(self, speed):
        for axle in self.axles:
            axle.target_motor_speed = speed
        self.axles[0].wake_bodies()

    def set_torque(self, torque):
        for axle in self.axles:
            axle.max_motor_torque = torque

    def set_hertz(self, hertz):
        for axle in self.axles:
            axle.spring_hertz = hertz

    def set_damping_ratio(self, damping_ratio):
        for axle in self.axles:
            axle.spring_damping_ratio = damping_ratio


# Donut (samples/donut.cpp)
class Donut:
    sides = 7

    def __init__(self, world, position, scale, group_index=0, enable_sensor_events=False):
        radius = scale
        delta_angle = 2.0 * math.pi / self.sides
        length = 2.0 * math.pi * radius / self.sides

        capsule = b2d.capsule((0.0, -0.5 * length), (0.0, 0.5 * length), 0.25 * scale)
        shape_def = b2d.shape_def(
            enable_sensor_events=enable_sensor_events,
            filter=b2d.make_filter(group_index=-group_index),
            material=b2d.surface_material(friction=0.3),
        )

        self.bodies = []
        for i in range(self.sides):
            angle = i * delta_angle
            body = world.create_dynamic_body(
                position=(
                    radius * math.cos(angle) + position[0],
                    radius * math.sin(angle) + position[1],
                ),
                rotation=angle,
            )
            body.create_shape(shape_def, capsule)
            self.bodies.append(body)

        self.joints = []
        prev = self.bodies[-1]
        for body in self.bodies:
            self.joints.append(
                world.create_weld_joint(
                    body_a=prev,
                    body_b=body,
                    angular_hertz=5.0,
                    angular_damping_ratio=0.0,
                    local_frame_a=b2d.transform(
                        p=(0.0, 0.5 * length), q=b2d.inv_mul_rot(prev.rotation, body.rotation)
                    ),
                    local_frame_b=b2d.transform(p=(0.0, -0.5 * length)),
                    draw_scale=0.5 * scale,
                )
            )
            prev = body

    def destroy(self):
        for body in self.bodies:
            body.destroy()
        self.bodies, self.joints = [], []


# Doohickey (samples/doohickey.cpp)
class Doohickey:
    def __init__(self, world, position, scale):
        position = b2d.Vec2(position)
        shape_def = b2d.shape_def(material=b2d.surface_material(rolling_resistance=0.1))
        circle = b2d.circle(radius=scale)
        capsule = b2d.capsule((-3.5 * scale, 0.0), (3.5 * scale, 0.0), 0.15 * scale)

        def create(x, geometry):
            body = world.create_dynamic_body(position=position + (scale * x, scale * 3.0))
            body.create_shape(shape_def, geometry)
            return body

        self.wheel1, self.wheel2 = create(-5.0, circle), create(5.0, circle)
        self.bar1, self.bar2 = create(-1.5, capsule), create(1.5, capsule)

        self.axles = [
            world.create_revolute_joint(
                body_a=wheel,
                body_b=bar,
                local_anchor_a=(0.0, 0.0),
                local_anchor_b=(x * scale, 0.0),
                enable_motor=True,
                max_motor_torque=2.0 * scale,
            )
            for wheel, bar, x in ((self.wheel1, self.bar1, -3.5), (self.wheel2, self.bar2, 3.5))
        ]

        self.slider = world.create_prismatic_joint(
            body_a=self.bar1,
            body_b=self.bar2,
            local_anchor_a=(2.0 * scale, 0.0),
            local_anchor_b=(-2.0 * scale, 0.0),
            lower_translation=-2.0 * scale,
            upper_translation=2.0 * scale,
            enable_limit=True,
            enable_motor=True,
            max_motor_force=2.0 * scale,
            enable_spring=True,
            hertz=1.0,
            damping_ratio=0.5,
        )


# Human (shared/human.c): examples_common/ragdoll.py, re-exported above
