"""Helpers for the ports of box2d's samples/sample_joints.cpp.

Car, Donut and Doohickey port samples/car.cpp, donut.cpp and doohickey.cpp,
Human ports shared/human.c.
"""

import math
import random
from collections import namedtuple

import pyb2d3 as b2d
from pyb2d3_sandbox import widgets

from ..examples_common.joints import pinned  # noqa: F401  (re-exported for the joint samples)
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
    points = [(random.uniform(-extent, extent), random.uniform(-extent, extent)) for _ in range(count)]
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


# --------------------------------------------------------------------------------------
# Car (samples/car.cpp)
# --------------------------------------------------------------------------------------


class Car:
    vertices = ((-1.5, -0.5), (1.5, -0.5), (1.5, 0.0), (0.0, 0.9), (-1.15, 0.9), (-1.5, 0.2))

    def __init__(self, world, position, scale, hertz, damping_ratio, torque):
        position = b2d.Vec2(position)
        chassis = b2d.polygon([(0.85 * scale * x, 0.85 * scale * y) for x, y in self.vertices], radius=0.15 * scale)

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


# --------------------------------------------------------------------------------------
# Donut (samples/donut.cpp)
# --------------------------------------------------------------------------------------


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
                position=(radius * math.cos(angle) + position[0], radius * math.sin(angle) + position[1]),
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


# --------------------------------------------------------------------------------------
# Doohickey (samples/doohickey.cpp)
# --------------------------------------------------------------------------------------


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


# --------------------------------------------------------------------------------------
# Human (shared/human.c)
# --------------------------------------------------------------------------------------

# heights / pivots are in units of the human scale, limits in units of pi
BoneSpec = namedtuple(
    "BoneSpec",
    "name parent height linear_damping friction_scale capsule pivot limits frame_angle foot",
)


def _bone_specs():
    yield BoneSpec("hip", None, 0.95, 0.0, 1.0, (-0.02, 0.02, 0.095), None, None, 0.0, False)
    yield BoneSpec("torso", "hip", 1.2, 0.0, 0.5, (-0.135, 0.135, 0.09), 1.0, (-0.25, 0.0), 0.0, False)
    yield BoneSpec("head", "torso", 1.475, 0.1, 0.25, (-0.038, 0.039, 0.075), 1.4, (-0.3, 0.1), 0.0, False)
    for side in ("left", "right"):
        upper, lower = f"upper_{side}_leg", f"lower_{side}_leg"
        yield BoneSpec(upper, "hip", 0.775, 0.0, 1.0, (-0.125, 0.125, 0.06), 0.9, (-0.05, 0.4), 0.0, False)
        yield BoneSpec(lower, upper, 0.475, 0.0, 0.5, (-0.155, 0.125, 0.045), 0.625, (-0.5, -0.02), 0.0, True)
    for side in ("left", "right"):
        upper, lower = f"upper_{side}_arm", f"lower_{side}_arm"
        yield BoneSpec(upper, "torso", 1.225, 0.0, 0.5, (-0.125, 0.125, 0.035), 1.35, (-0.1, 0.8), 0.0, False)
        yield BoneSpec(lower, upper, 0.975, 0.1, 0.1, (-0.125, 0.125, 0.03), 1.1, (-0.2, 0.3), 0.25, False)


BONE_SPECS = tuple(_bone_specs())
FOOT_POINTS = ((-0.03, -0.185), (0.11, -0.185), (0.11, -0.16), (-0.03, -0.14))


class Bone:
    def __init__(self, spec, body, joint):
        self.spec = spec
        self.body = body
        self.joint = joint

    @property
    def friction_scale(self):
        return self.spec.friction_scale


class Human:
    def __init__(self, world, position, scale, friction_torque, hertz, damping_ratio, group_index):
        position = b2d.Vec2(position)
        s = scale
        self.original_scale = scale
        self.scale = scale
        self.friction_torque = friction_torque

        shape_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.2),
            filter=b2d.make_filter(group_index=-group_index, category_bits=2, mask_bits=1 | 2),
        )
        # feet don't collide with ragdolls
        foot_shape_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.05),
            filter=b2d.make_filter(group_index=-group_index, category_bits=2, mask_bits=1),
        )
        foot = b2d.polygon([(s * x, s * y) for x, y in FOOT_POINTS], radius=0.015 * s)

        self.bones = []
        by_name = {}
        for spec in BONE_SPECS:
            body = world.create_dynamic_body(
                position=position + (0.0, spec.height * s),
                linear_damping=spec.linear_damping,
                sleep_threshold=0.1,
                name=spec.name,
            )
            y1, y2, radius = spec.capsule
            body.create_shape(shape_def, b2d.capsule((0.0, y1 * s), (0.0, y2 * s), radius * s))
            if spec.foot:
                body.create_shape(foot_shape_def, foot)

            joint = None
            if spec.parent is not None:
                parent = by_name[spec.parent].body
                lower, upper = spec.limits
                joint = world.create_revolute_joint(
                    **pinned(parent, body, position + (0.0, spec.pivot * s), q_a=spec.frame_angle * math.pi),
                    enable_limit=True,
                    lower_angle=lower * math.pi,
                    upper_angle=upper * math.pi,
                    enable_motor=True,
                    max_motor_torque=spec.friction_scale * friction_torque * s,
                    enable_spring=hertz > 0.0,
                    hertz=hertz,
                    damping_ratio=damping_ratio,
                    draw_scale=0.05,
                )
            bone = Bone(spec, body, joint)
            by_name[spec.name] = bone
            self.bones.append(bone)

    @property
    def jointed_bones(self):
        return self.bones[1:]

    def destroy(self):
        for bone in self.bones:
            bone.body.destroy()
        self.bones = []

    def apply_random_angular_impulse(self, magnitude):
        self.bones[1].body.apply_angular_impulse(random.uniform(-magnitude, magnitude), True)

    def set_joint_friction_torque(self, torque):
        for bone in self.jointed_bones:
            bone.joint.motor_enabled = torque != 0.0
            if torque != 0.0:
                bone.joint.max_motor_torque = self.scale * bone.friction_scale * torque

    def set_joint_spring_hertz(self, hertz):
        for bone in self.jointed_bones:
            bone.joint.spring_enabled = hertz != 0.0
            if hertz != 0.0:
                bone.joint.spring_hertz = hertz

    def set_joint_damping_ratio(self, damping_ratio):
        for bone in self.jointed_bones:
            bone.joint.spring_damping_ratio = damping_ratio

    def set_scale(self, scale):
        assert 0.01 < scale < 100.0
        ratio = scale / self.scale

        # torque scales by pow(length, 4) due to mass and length change, gravity is also a factor so use pow(length, 3)
        friction_torque = (scale / self.original_scale) ** 3 * self.friction_torque

        origin = self.bones[0].body.position
        for bone in self.bones:
            body = bone.body
            if bone.joint is not None:
                transform = body.transform
                body.set_transform(origin + (transform.p - origin) * ratio, transform.q)

                for attr in ("local_frame_a", "local_frame_b"):
                    frame = getattr(bone.joint, attr)
                    frame.p = b2d.Vec2(frame.p) * ratio
                    setattr(bone.joint, attr, frame)

                bone.joint.max_motor_torque = bone.friction_scale * friction_torque

            for shape in body.shapes:
                if isinstance(shape, b2d.CapsuleShape):
                    capsule = shape.capsule
                    shape.capsule = b2d.capsule(
                        b2d.Vec2(capsule.center1) * ratio, b2d.Vec2(capsule.center2) * ratio, capsule.radius * ratio
                    )
                elif isinstance(shape, b2d.PolygonShape):
                    # TODO(binding): Polygon.vertices / centroid are read-only, so the polygon is rebuilt
                    # from a hull, which fails for tiny feet (points closer than the linear slop are welded).
                    # box2d scales polygon.vertices in place instead.
                    polygon = shape.polygon
                    hull = b2d.compute_hull(polygon.vertices * ratio)
                    if hull.count > 0:
                        shape.polygon = b2d.make_polygon(hull, polygon.radius * ratio)

            body.update_mass_from_shapes()

        self.scale = scale
