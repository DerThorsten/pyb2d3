"""Helpers shared by the stacking and events samples (ports of donut.cpp, human.c, utils.c)."""

import math
import random

import pyb2d3 as b2d

from ..examples_common.ragdoll import Ragdoll

ROUNDED_BOX = b2d.box(0.45, 0.45, radius=0.05)


def random_polygon(extent):
    """A random convex polygon with 3 to 8 vertices inside [-extent, extent]^2."""
    points = [(random.uniform(-extent, extent), random.uniform(-extent, extent)) for _ in range(random.randint(3, 8))]
    hull = b2d.compute_hull(points)
    if hull.count > 0:
        return b2d.make_polygon(hull)
    return b2d.make_square(extent)


def create_column(world, x, count, shape_def, geometry, offset=0.0):
    """A column of `count` unit spaced bodies, alternately shifted by -offset / +offset."""
    bodies = []
    for i in range(count):
        shift = -offset if i % 2 == 0 else offset
        body = world.create_dynamic_body(position=(x + shift, 0.5 + 1.0 * i))
        body.create_shape(shape_def, geometry)
        bodies.append(body)
    return bodies


def launch_body(world, position, is_bullet=True):
    """A dynamic body shot to the right at 200 to 300 m/s."""
    return world.create_dynamic_body(
        position=position, linear_velocity=(random.uniform(200.0, 300.0), 0.0), is_bullet=is_bullet
    )


class Donut:
    """A ring of capsules welded together."""

    sides = 7

    def __init__(self, world, position, scale=1.0, group_index=0, enable_sensor_events=False, user_data=0):
        radius = 1.0 * scale
        delta_angle = 2.0 * math.pi / self.sides
        length = 2.0 * math.pi * radius / self.sides
        capsule = b2d.capsule((0.0, -0.5 * length), (0.0, 0.5 * length), 0.25 * scale)

        shape_def = b2d.shape_def(
            enable_sensor_events=enable_sensor_events,
            filter=b2d.make_filter(group_index=-group_index),
            material=b2d.surface_material(friction=0.3),
        )

        cx, cy = position
        self.bodies = []
        for i in range(self.sides):
            angle = i * delta_angle
            body = world.create_dynamic_body(
                position=(radius * math.cos(angle) + cx, radius * math.sin(angle) + cy),
                rotation=angle,
                user_data=user_data,
            )
            body.create_shape(shape_def, capsule)
            self.bodies.append(body)

        self.joints = []
        prev = self.bodies[-1]
        for body in self.bodies:
            q = b2d.inv_mul_rot(prev.rotation, body.rotation)
            self.joints.append(
                world.create_weld_joint(
                    body_a=prev,
                    body_b=body,
                    local_frame_a=b2d.transform(p=(0.0, 0.5 * length), q=q),
                    local_frame_b=b2d.transform(p=(0.0, -0.5 * length)),
                    angular_hertz=5.0,
                    angular_damping_ratio=0.0,
                    draw_scale=0.5 * scale,
                )
            )
            prev = body

    def destroy(self):
        for body in self.bodies:
            body.destroy()
        self.bodies, self.joints = [], []


class Human:
    """box2d's Human (shared/human.c): a ragdoll whose joint motors act as joint friction."""

    def __init__(self, world, position, scale, friction_torque, hertz, damping_ratio, group_index, user_data, colorize):
        ragdoll = Ragdoll(
            world,
            position=position,
            scale=scale,
            friction_torque=friction_torque,
            hertz=hertz,
            damping_ratio=damping_ratio,
            group_index=group_index,
            user_data=user_data,
            colorize=colorize,
        )
        self.bodies = [bone.body for bone in ragdoll.bones]
        self.joints = [bone.joint for bone in ragdoll.bones if bone.joint is not None]
        for joint in self.joints:
            joint.motor_enabled = True

    def enable_sensor_events(self, flag=True):
        for body in self.bodies:
            for shape in body.shapes:
                shape.sensor_events_enabled = flag

    def destroy(self):
        # joints first: destroying a body also destroys its joints and a second destroy would crash
        # (Ragdoll.destroy interleaves them)
        for joint in self.joints:
            joint.destroy()
        for body in self.bodies:
            body.destroy()
        self.bodies, self.joints = [], []
