# This python version of the Box2D ragdoll ("human") is based on the original C code
# from Erin Catto's Box2D library.
# The original C code is available at:
#
# https://github.com/erincatto/box2d/blob/main/shared/human.c /
# https://github.com/erincatto/box2d/blob/main/shared/human.h
#
# The original C code is licensed under the MIT License.
#
# MIT License
#
# Copyright (c) 2022 Erin Catto
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""The one ragdoll of the samples: box2d's human (shared/human.c).

`Ragdoll` is used by the hand-written samples, `Human` (joint motors as joint
friction, box2d's argument order) by the ports of box2d's samples.
"""

import math
import random
from collections import namedtuple

import pyb2d3 as b2d

# heights / pivots in units of the scale, capsule (y1, y2, radius) too,
# limits and the frame A angle in units of pi; color: "shirt" / "pant" / "skin"
BoneSpec = namedtuple(
    "BoneSpec",
    "name parent height linear_damping friction_scale capsule pivot limits frame_angle foot color",
)


def _bone_specs():
    """The 11 bones of the human, parents before children."""
    yield BoneSpec("hip", None, 0.95, 0.0, 1.0, (-0.02, 0.02, 0.095), None, None, 0.0, False, "pant")
    yield BoneSpec("torso", "hip", 1.2, 0.0, 0.5, (-0.135, 0.135, 0.09), 1.0, (-0.25, 0.0), 0.0, False, "shirt")
    yield BoneSpec("head", "torso", 1.475, 0.1, 0.25, (-0.038, 0.039, 0.075), 1.4, (-0.3, 0.1), 0.0, False, "skin")
    for side in ("left", "right"):
        upper, lower = f"upper_{side}_leg", f"lower_{side}_leg"
        yield BoneSpec(upper, "hip", 0.775, 0.0, 1.0, (-0.125, 0.125, 0.06), 0.9, (-0.05, 0.4), 0.0, False, "pant")
        yield BoneSpec(lower, upper, 0.475, 0.0, 0.5, (-0.155, 0.125, 0.045), 0.625, (-0.5, -0.02), 0.0, True, "pant")
    for side in ("left", "right"):
        upper, lower = f"upper_{side}_arm", f"lower_{side}_arm"
        yield BoneSpec(upper, "torso", 1.225, 0.0, 0.5, (-0.125, 0.125, 0.035), 1.35, (-0.1, 0.8), 0.0, False, "shirt")
        # box2d >= 3.2: the reference angle is the rotation of the local frame A
        yield BoneSpec(lower, upper, 0.975, 0.1, 0.1, (-0.125, 0.125, 0.03), 1.1, (-0.2, 0.3), 0.25, False, "skin")


BONE_SPECS = tuple(_bone_specs())
FOOT_POINTS = ((-0.03, -0.185), (0.11, -0.185), (0.11, -0.16), (-0.03, -0.14))
SKIN_COLORS = (b2d.HexColor.NavajoWhite, b2d.HexColor.LightYellow, b2d.HexColor.Peru, b2d.HexColor.Tan)
CLOTH_COLORS = {"shirt": b2d.HexColor.MediumTurquoise, "pant": b2d.HexColor.DodgerBlue}


class Bone:
    """One bone: its body and the joint to its parent (None for the hip)."""

    def __init__(self, spec, body, joint):
        self.spec = spec
        self.body = body
        self.joint = joint

    @property
    def name(self):
        return self.spec.name

    @property
    def friction_scale(self):
        return self.spec.friction_scale


class Ragdoll:
    """box2d's human: 11 capsule bones connected by revolute joints with limits
    and springs; with `joint_friction` the joint motors act as joint friction."""

    def __init__(
        self,
        world,
        position=(0, 0),
        scale=1.0,
        friction_torque=0.1,
        hertz=10.0,
        damping_ratio=0.5,
        group_index=0,
        user_data=0,
        colorize=False,
        joint_friction=False,
    ):
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
        if colorize:
            foot_shape_def.material.custom_color = b2d.HexColor.SaddleBrown.value
        foot = b2d.polygon([(s * x, s * y) for x, y in FOOT_POINTS], radius=0.015 * s)
        colors = {**CLOTH_COLORS, "skin": SKIN_COLORS[group_index % len(SKIN_COLORS)]}

        self.bones = []
        by_name = {}
        for spec in BONE_SPECS:
            body = world.create_dynamic_body(
                position=position + (0.0, spec.height * s),
                linear_damping=spec.linear_damping,
                sleep_threshold=0.1,
                name=spec.name,
                user_data=user_data,
            )
            if colorize:
                shape_def.material.custom_color = colors[spec.color].value
            y1, y2, radius = spec.capsule
            body.create_shape(shape_def, b2d.capsule((0.0, y1 * s), (0.0, y2 * s), radius * s))
            if spec.foot:
                body.create_shape(foot_shape_def, foot)

            joint = None
            if spec.parent is not None:
                parent = by_name[spec.parent].body
                pivot = position + (0.0, spec.pivot * s)
                lower, upper = spec.limits
                joint = world.create_revolute_joint(
                    body_a=parent,
                    body_b=body,
                    local_frame_a=b2d.transform(p=parent.local_point(pivot), q=b2d.make_rot(spec.frame_angle * math.pi)),
                    local_anchor_b=body.local_point(pivot),
                    enable_limit=True,
                    lower_angle=lower * math.pi,
                    upper_angle=upper * math.pi,
                    enable_motor=joint_friction,
                    max_motor_torque=spec.friction_scale * friction_torque * s,
                    enable_spring=hertz > 0.0,
                    hertz=hertz,
                    damping_ratio=damping_ratio,
                    draw_scale=0.05,
                )
            bone = Bone(spec, body, joint)
            by_name[spec.name] = bone
            self.bones.append(bone)
        self._by_name = by_name

    # ---- access -------------------------------------------------------------------------

    def bone(self, name):
        """the bone named `name` ("hip", "torso", "head", "upper_left_leg", ...)"""
        return self._by_name[name]

    @property
    def bodies(self):
        return [bone.body for bone in self.bones]

    @property
    def joints(self):
        return [bone.joint for bone in self.bones if bone.joint is not None]

    @property
    def jointed_bones(self):
        return self.bones[1:]

    # ---- changes ------------------------------------------------------------------------

    def destroy(self):
        """destroy joints first, then bodies (destroying a body also destroys its joints)"""
        for bone in self.bones:
            if bone.joint is not None and bone.joint.is_valid:
                bone.joint.destroy()
        for bone in self.bones:
            if bone.body.is_valid:
                bone.body.destroy()
        self.bones = []
        self._by_name = {}

    def set_velocity(self, velocity):
        """same linear velocity for every bone"""
        for bone in self.bones:
            bone.body.linear_velocity = velocity

    def apply_random_angular_impulse(self, magnitude):
        """a random spin on the torso"""
        self.bone("torso").body.apply_angular_impulse(random.uniform(-magnitude, magnitude), True)

    def enable_sensor_events(self, flag=True):
        for body in self.bodies:
            for shape in body.shapes:
                shape.sensor_events_enabled = flag

    def set_joint_friction_torque(self, torque):
        """joint friction via the joint motors, 0 switches them off"""
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
        """rescale the whole ragdoll in place around the hip"""
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
                    # like box2d: scale in place (the normals stay valid under uniform scaling)
                    polygon = shape.polygon
                    polygon.vertices = polygon.vertices * ratio
                    polygon.centroid = b2d.Vec2(polygon.centroid) * ratio
                    polygon.radius *= ratio
                    shape.polygon = polygon

            body.update_mass_from_shapes()

        self.scale = scale


class Human(Ragdoll):
    """box2d's CreateHuman (argument order of human.c): joint motors on, as joint friction."""

    def __init__(
        self, world, position, scale, friction_torque, hertz, damping_ratio, group_index=1, user_data=0, colorize=False
    ):
        super().__init__(
            world,
            position=position,
            scale=scale,
            friction_torque=friction_torque,
            hertz=hertz,
            damping_ratio=damping_ratio,
            group_index=group_index,
            user_data=user_data,
            colorize=colorize,
            joint_friction=True,
        )
