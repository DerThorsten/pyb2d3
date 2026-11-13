"""Ports of the box2d sample helpers used by the World samples.

human.c (CreateHuman), donut.cpp (Donut), car.cpp (Car), utils.c (RandomPolygon)
and Sample::ParsePath.
"""

import math
import random

import pyb2d3 as b2d

LINEAR_SLOP = 0.005

# name, parent, body y, linear damping, friction scale, capsule (y1, y2, radius),
# color, pivot y, (lower, upper) angle in units of pi, has foot, frame A angle in units of pi
_HUMAN_BONES = (
    ("hip", None, 0.95, 0.0, 1.0, (-0.02, 0.02, 0.095), "pant", None, None, False, 0.0),
    ("torso", "hip", 1.2, 0.0, 0.5, (-0.135, 0.135, 0.09), "shirt", 1.0, (-0.25, 0.0), False, 0.0),
    ("head", "torso", 1.475, 0.1, 0.25, (-0.038, 0.039, 0.075), "skin", 1.4, (-0.3, 0.1), False, 0.0),
    ("upper_left_leg", "hip", 0.775, 0.0, 1.0, (-0.125, 0.125, 0.06), "pant", 0.9, (-0.05, 0.4), False, 0.0),
    ("lower_left_leg", "upper_left_leg", 0.475, 0.0, 0.5, (-0.155, 0.125, 0.045), "pant", 0.625, (-0.5, -0.02), True, 0.0),
    ("upper_right_leg", "hip", 0.775, 0.0, 1.0, (-0.125, 0.125, 0.06), "pant", 0.9, (-0.05, 0.4), False, 0.0),
    ("lower_right_leg", "upper_right_leg", 0.475, 0.0, 0.5, (-0.155, 0.125, 0.045), "pant", 0.625, (-0.5, -0.02), True, 0.0),
    ("upper_left_arm", "torso", 1.225, 0.0, 0.5, (-0.125, 0.125, 0.035), "shirt", 1.35, (-0.1, 0.8), False, 0.0),
    ("lower_left_arm", "upper_left_arm", 0.975, 0.1, 0.1, (-0.125, 0.125, 0.03), "skin", 1.1, (-0.2, 0.3), False, 0.25),
    ("upper_right_arm", "torso", 1.225, 0.0, 0.5, (-0.125, 0.125, 0.035), "shirt", 1.35, (-0.1, 0.8), False, 0.0),
    ("lower_right_arm", "upper_right_arm", 0.975, 0.1, 0.1, (-0.125, 0.125, 0.03), "skin", 1.1, (-0.2, 0.3), False, 0.25),
)

_SKIN_COLORS = (b2d.HexColor.NavajoWhite, b2d.HexColor.LightYellow, b2d.HexColor.Peru, b2d.HexColor.Tan)


def create_human(
    world, position, scale, friction_torque, hertz, damping_ratio, group_index, colorize=False
):
    """Port of CreateHuman: a ragdoll of capsules and revolute joints. Returns {bone name: (body, joint)}."""
    s = scale
    px, py = position
    max_torque = friction_torque * s
    colors = {
        "shirt": b2d.HexColor.MediumTurquoise.value,
        "pant": b2d.HexColor.DodgerBlue.value,
        "skin": _SKIN_COLORS[group_index % 4].value,
    }

    def make_shape_def(friction, mask_bits):
        return b2d.shape_def(
            material=b2d.surface_material(friction=friction),
            filter=b2d.make_filter(group_index=-group_index, category_bits=2, mask_bits=mask_bits),
        )

    shape_def = make_shape_def(0.2, 1 | 2)
    # feet don't collide with ragdolls
    foot_shape_def = make_shape_def(0.05, 1)
    if colorize:
        foot_shape_def.material.custom_color = b2d.HexColor.SaddleBrown.value
    foot = b2d.polygon(
        [(-0.03 * s, -0.185 * s), (0.11 * s, -0.185 * s), (0.11 * s, -0.16 * s), (-0.03 * s, -0.14 * s)],
        radius=0.015 * s,
    )

    bones = {}
    for name, parent, y, damping, friction_scale, (y1, y2, r), color, pivot_y, limits, has_foot, frame_angle in _HUMAN_BONES:
        body = world.create_dynamic_body(
            position=(px, py + y * s), linear_damping=damping, sleep_threshold=0.1, name=name
        )
        if colorize:
            shape_def.material.custom_color = colors[color]
        body.create_shape(shape_def, b2d.capsule((0, y1 * s), (0, y2 * s), r * s))
        if has_foot:
            body.create_shape(foot_shape_def, foot)

        joint = None
        if parent is not None:
            parent_body = bones[parent][0]
            pivot = (px, py + pivot_y * s)
            joint = world.create_revolute_joint(
                body_a=parent_body,
                body_b=body,
                local_frame_a=b2d.transform(
                    p=parent_body.local_point(pivot), q=b2d.make_rot(frame_angle * math.pi)
                ),
                local_anchor_b=body.local_point(pivot),
                enable_limit=True,
                lower_angle=limits[0] * math.pi,
                upper_angle=limits[1] * math.pi,
                enable_motor=True,
                max_motor_torque=friction_scale * max_torque,
                enable_spring=hertz > 0.0,
                hertz=hertz,
                damping_ratio=damping_ratio,
                draw_scale=0.05,
            )
        bones[name] = (body, joint)
    return bones


def create_donut(world, position, scale, group_index=0, enable_sensor_events=False, sides=7):
    """Port of Donut::Create: a ring of capsules welded together. Returns the bodies."""
    radius = 1.0 * scale
    delta_angle = 2.0 * math.pi / sides
    length = 2.0 * math.pi * radius / sides
    capsule = b2d.capsule((0, -0.5 * length), (0, 0.5 * length), 0.25 * scale)
    shape_def = b2d.shape_def(
        enable_sensor_events=enable_sensor_events,
        filter=b2d.make_filter(group_index=-group_index),
        material=b2d.surface_material(friction=0.3),
    )

    bodies = []
    for i in range(sides):
        angle = i * delta_angle
        body = world.create_dynamic_body(
            position=(radius * math.cos(angle) + position[0], radius * math.sin(angle) + position[1]),
            rotation=b2d.make_rot(angle),
        )
        body.create_shape(shape_def, capsule)
        bodies.append(body)

    for body_a, body_b in zip(bodies[-1:] + bodies[:-1], bodies):
        world.create_weld_joint(
            body_a=body_a,
            body_b=body_b,
            angular_hertz=5.0,
            angular_damping_ratio=0.0,
            local_frame_a=b2d.transform(
                p=(0, 0.5 * length), q=b2d.inv_mul_rot(body_a.rotation, body_b.rotation)
            ),
            local_anchor_b=(0, -0.5 * length),
            draw_scale=0.5 * scale,
        )
    return bodies


class Car:
    """Port of car.cpp: a chassis with two motorized wheel joints."""

    def __init__(self, world, position, scale, hertz, damping_ratio, torque):
        px, py = position
        vertices = [(-1.5, -0.5), (1.5, -0.5), (1.5, 0.0), (0.0, 0.9), (-1.15, 0.9), (-1.5, 0.2)]
        chassis = b2d.polygon([(0.85 * scale * x, 0.85 * scale * y) for x, y in vertices], radius=0.15 * scale)

        self.chassis = world.create_dynamic_body(position=(px, py + 1.0 * scale))
        self.chassis.create_shape(
            b2d.shape_def(density=1.0 / scale, material=b2d.surface_material(friction=0.2)), chassis
        )

        wheel_shape_def = b2d.shape_def(
            density=2.0 / scale, material=b2d.surface_material(friction=1.5, rolling_resistance=0.1)
        )
        circle = b2d.circle(radius=0.4 * scale)
        self.axles = []
        for x, y in ((-1.0, 0.35), (1.0, 0.4)):
            wheel = world.create_dynamic_body(position=(px + x * scale, py + y * scale), allow_fast_rotation=True)
            wheel.create_shape(wheel_shape_def, circle)
            pivot = wheel.position
            self.axles.append(
                world.create_wheel_joint(
                    body_a=self.chassis,
                    body_b=wheel,
                    local_frame_a=b2d.transform(p=self.chassis.local_point(pivot), q=b2d.make_rot(0.5 * math.pi)),
                    local_anchor_b=wheel.local_point(pivot),
                    motor_speed=0.0,
                    max_motor_torque=torque,
                    enable_motor=True,
                    hertz=hertz,
                    damping_ratio=damping_ratio,
                    lower_translation=-0.25 * scale,
                    upper_translation=0.25 * scale,
                    enable_limit=True,
                )
            )

    def set_speed(self, speed):
        for axle in self.axles:
            axle.target_motor_speed = speed
        self.axles[0].wake_bodies()


def random_polygon(extent, radius=0.0):
    """Port of RandomPolygon: the hull of 3 to 8 random points, a square if that fails."""
    points = [(random.uniform(-extent, extent), random.uniform(-extent, extent)) for _ in range(random.randint(3, 8))]
    hull = b2d.compute_hull(points)
    if hull.count > 0:
        return b2d.make_polygon(hull, radius)
    return b2d.box(extent, extent, radius=radius)


def parse_path(svg_path, offset, scale):
    """Port of Sample::ParsePath: points of an SVG path made of straight lines (y flipped)."""
    points = []
    x = y = 0.0
    command = None
    for token in svg_path.split():
        if token[0].isalpha():
            command = token
            if command == "z":
                break
            continue
        values = [float(v) for v in token.split(",")]
        if command in ("M", "L"):
            x, y = values
        elif command in ("m", "l"):
            x, y = x + values[0], y + values[1]
        elif command == "H":
            x = values[0]
        elif command == "h":
            x += values[0]
        elif command == "V":
            y = values[0]
        elif command == "v":
            y += values[0]
        else:
            raise ValueError(f"unsupported path command {command!r}")
        points.append((scale * (x + offset[0]), -scale * (y + offset[1])))

    # remove the loop point for chain shapes
    if len(points) > 2 and math.dist(points[0], points[-1]) <= LINEAR_SLOP:
        points.pop()
    return points
