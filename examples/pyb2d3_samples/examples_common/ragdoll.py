# This python version of the Box2D Ragdoll example is based on the original C code
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

import math
from enum import Enum
from dataclasses import dataclass
import pyb2d3 as b2d


class RagdollBoneId(Enum):
    hip = 0
    torso = 1
    head = 2
    upper_left_leg = 3
    lower_left_leg = 4
    upper_right_leg = 5
    lower_right_leg = 6
    upper_left_arm = 7
    lower_left_arm = 8
    upper_right_arm = 9
    lower_right_arm = 10
    bone_count = 11


@dataclass
class RagdollBone:
    body: b2d.Body = None
    joint: b2d.Joint = None
    friction_scale: float = 1.0
    max_motor_torque: float = 1000.0
    parent_index: int = -1


class Ragdoll(object):
    Bone = RagdollBone
    BoneId = RagdollBoneId

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
    ):
        self._is_spawned = True
        position = b2d.Vec2(position)

        self.bones = [RagdollBone() for _ in range(RagdollBoneId.bone_count.value)]
        self.friction_torque = friction_torque
        self.orginal_scale = scale
        self.scale = scale
        self.hertz = hertz

        body_def = b2d.body_def()
        body_def.type = b2d.BodyType.DYNAMIC
        body_def.user_data = user_data
        body_def.sleep_threshold = 0.1

        shape_def = b2d.shape_def()
        shape_def.material.friction = 0.2
        shape_def.filter.group_index = -group_index
        shape_def.filter.category_bits = 2
        shape_def.filter.mask_bits = 1 | 2

        foot_shape_def = shape_def.copy()
        foot_shape_def.material.friction = 0.05

        # feet dont collide with ragdolls
        foot_shape_def.filter.category_bits = 2
        foot_shape_def.filter.mask_bits = 1

        if colorize:
            foot_shape_def.material.custom_color = b2d.HexColor.SaddleBrown.value

        s = scale
        max_motor_torque = friction_torque * s
        enable_motor = False
        enable_limit = True
        draw_size = 0.05

        shirt_color = b2d.HexColor.MediumTurquoise.value
        pant_color = b2d.HexColor.DodgerBlue.value

        skin_colors = [
            b2d.HexColor.NavajoWhite.value,
            b2d.HexColor.LightYellow.value,
            b2d.HexColor.Peru.value,
            b2d.HexColor.SandyBrown.value,
        ]
        skin_color = skin_colors[group_index % 4]

        # hip
        bone = self.bones[RagdollBoneId.hip.value]
        bone.parent_index = -1

        body_def.position = position + (0.0, 0.95 * s)
        body_def.linear_damping = 0.0
        body_def.name = "hip"
        bone.body = world.create_body(body_def)
        if colorize:
            shape_def.material.custom_color = pant_color

        capsule = b2d.capsule((0.0, -0.02 * s), (0.0, 0.02 * s), 0.095 * s)
        bone.body.create_shape(shape_def, capsule)

        # torso
        bone = self.bones[RagdollBoneId.torso.value]
        bone.parent_index = RagdollBoneId.hip.value
        body_def.position = position + (0.0, 1.2 * s)
        body_def.linear_damping = 0.0
        body_def.name = "torso"

        bone.body = world.create_body(body_def)
        bone.friction_scale = 0.5
        body_def.type = b2d.BodyType.DYNAMIC

        if colorize:
            shape_def.material.custom_color = shirt_color

        capsule = b2d.capsule((0.0, -0.135 * s), (0.0, 0.135 * s), 0.09 * s)
        bone.body.create_shape(shape_def, capsule)

        pivot = position + (0.0, 1.0 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.25 * math.pi
        joint_def.upper_angle = 0.0
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

        # head
        bone = self.bones[RagdollBoneId.head.value]
        bone.parent_index = RagdollBoneId.torso.value
        body_def.position = position + (0.0, 1.475 * s)
        body_def.linear_damping = 0.1
        body_def.name = "head"
        bone.body = world.create_body(body_def)
        bone.friction_scale = 0.25
        if colorize:
            shape_def.material.custom_color = skin_color
        capsule = b2d.capsule((0.0, -0.038 * s), (0.0, 0.039 * s), 0.075 * s)
        bone.body.create_shape(shape_def, capsule)

        # neck
        pivot = position + (0.0, 1.4 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.3 * math.pi
        joint_def.upper_angle = 0.1 * math.pi
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

        # upper left leg
        bone = self.bones[RagdollBoneId.upper_left_leg.value]
        bone.parent_index = RagdollBoneId.hip.value
        body_def.position = position + (0.0, 0.775 * s)
        body_def.linear_damping = 0.0
        body_def.name = "upper_left_leg"

        bone.body = world.create_body(body_def)
        bone.friction_scale = 1.0

        if colorize:
            shape_def.material.custom_color = pant_color

        capsule = b2d.capsule((0.0, -0.125 * s), (0.0, 0.125 * s), 0.06 * s)
        bone.body.create_shape(shape_def, capsule)

        pivot = position + (0.0, 0.9 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.05 * math.pi
        joint_def.upper_angle = 0.4 * math.pi
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

        points = [
            (-0.03 * s, -0.185 * s),
            (0.11 * s, -0.185 * s),
            (0.11 * s, -0.16 * s),
            (-0.03 * s, -0.14 * s),
        ]
        foot_polygon = b2d.polygon(points, radius=0.015 * s)

        # lower left leg
        bone = self.bones[RagdollBoneId.lower_left_leg.value]
        bone.parent_index = RagdollBoneId.upper_left_leg.value

        body_def.position = position + (0.0, 0.475 * s)
        body_def.linear_damping = 0.0
        body_def.name = "lower_left_leg"

        bone.body = world.create_body(body_def)
        bone.friction_scale = 0.5

        if colorize:
            shape_def.material.custom_color = pant_color

        capsule = b2d.capsule((0.0, -0.155 * s), (0.0, 0.125 * s), 0.045 * s)
        bone.body.create_shape(shape_def, capsule)

        bone.body.create_shape(foot_shape_def, foot_polygon)

        pivot = position + (0.0, 0.625 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.5 * math.pi
        joint_def.upper_angle = -0.02 * math.pi
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

        # upper right leg
        bone = self.bones[RagdollBoneId.upper_right_leg.value]
        bone.parent_index = RagdollBoneId.hip.value
        body_def.position = position + (0.0, 0.775 * s)
        body_def.linear_damping = 0.0
        body_def.name = "upper_right_leg"

        bone.body = world.create_body(body_def)
        bone.friction_scale = 1.0

        if colorize:
            shape_def.material.custom_color = pant_color

        capsule = b2d.capsule((0.0, -0.125 * s), (0.0, 0.125 * s), 0.06 * s)
        bone.body.create_shape(shape_def, capsule)

        pivot = position + (0.0, 0.9 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.05 * math.pi
        joint_def.upper_angle = 0.4 * math.pi
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

        # lower right leg
        bone = self.bones[RagdollBoneId.lower_right_leg.value]
        bone.parent_index = RagdollBoneId.upper_right_leg.value
        body_def.position = position + (0.0, 0.475 * s)
        body_def.linear_damping = 0.0
        body_def.name = "lower_right_leg"
        bone.body = world.create_body(body_def)
        bone.friction_scale = 0.5
        if colorize:
            shape_def.material.custom_color = pant_color
        capsule = b2d.capsule((0.0, -0.155 * s), (0.0, 0.125 * s), 0.045 * s)
        bone.body.create_shape(shape_def, capsule)
        bone.body.create_shape(foot_shape_def, foot_polygon)
        pivot = position + (0.0, 0.625 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.5 * math.pi
        joint_def.upper_angle = -0.02 * math.pi
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

        # upper left arm
        bone = self.bones[RagdollBoneId.upper_left_arm.value]
        bone.parent_index = RagdollBoneId.torso.value
        body_def.position = position + (0.0, 1.225 * s)
        body_def.linear_damping = 0.0
        body_def.name = "upper_left_arm"
        bone.body = world.create_body(body_def)
        bone.friction_scale = 0.5
        if colorize:
            shape_def.material.custom_color = shirt_color
        capsule = b2d.capsule((0.0, -0.125 * s), (0.0, 0.125 * s), 0.035 * s)
        bone.body.create_shape(shape_def, capsule)
        pivot = position + (0.0, 1.35 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.1 * math.pi
        joint_def.upper_angle = 0.8 * math.pi
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

        # lower left arm
        bone = self.bones[RagdollBoneId.lower_left_arm.value]
        bone.parent_index = RagdollBoneId.upper_left_arm.value
        body_def.position = position + (0.0, 0.975 * s)
        body_def.linear_damping = 0.1
        body_def.name = "lower_left_arm"
        bone.body = world.create_body(body_def)
        bone.friction_scale = 0.1
        if colorize:
            shape_def.material.custom_color = skin_color
        capsule = b2d.capsule((0.0, -0.125 * s), (0.0, 0.125 * s), 0.03 * s)
        bone.body.create_shape(shape_def, capsule)
        pivot = position + (0.0, 1.1 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.reference_angle = 0.25 * math.pi
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.2 * math.pi
        joint_def.upper_angle = 0.3 * math.pi
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

        # upper right arm
        bone = self.bones[RagdollBoneId.upper_right_arm.value]
        bone.parent_index = RagdollBoneId.torso.value
        body_def.position = position + (0.0, 1.225 * s)
        body_def.linear_damping = 0.0
        body_def.name = "upper_right_arm"
        bone.body = world.create_body(body_def)
        bone.friction_scale = 0.5
        if colorize:
            shape_def.material.custom_color = shirt_color
        capsule = b2d.capsule((0.0, -0.125 * s), (0.0, 0.125 * s), 0.035 * s)
        bone.body.create_shape(shape_def, capsule)
        pivot = position + (0.0, 1.35 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.1 * math.pi
        joint_def.upper_angle = 0.8 * math.pi
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

        # lower right arm
        bone = self.bones[RagdollBoneId.lower_right_arm.value]
        bone.parent_index = RagdollBoneId.upper_right_arm.value
        body_def.position = position + (0.0, 0.975 * s)
        body_def.linear_damping = 0.1
        body_def.name = "lower_right_arm"
        bone.body = world.create_body(body_def)
        bone.friction_scale = 0.1
        if colorize:
            shape_def.material.custom_color = skin_color
        capsule = b2d.capsule((0.0, -0.125 * s), (0.0, 0.125 * s), 0.03 * s)
        bone.body.create_shape(shape_def, capsule)
        pivot = position + (0.0, 1.1 * s)
        joint_def = b2d.revolute_joint_def()
        joint_def.body_a = self.bones[bone.parent_index].body
        joint_def.body_b = bone.body
        joint_def.local_anchor_a = joint_def.body_a.local_point(pivot)
        joint_def.local_anchor_b = joint_def.body_b.local_point(pivot)
        joint_def.reference_angle = 0.25 * math.pi
        joint_def.enable_limit = enable_limit
        joint_def.lower_angle = -0.2 * math.pi
        joint_def.upper_angle = 0.3 * math.pi
        joint_def.enable_motor = enable_motor
        joint_def.max_motor_torque = bone.friction_scale * max_motor_torque
        joint_def.enable_spring = hertz > 0.0
        joint_def.hertz = hertz
        joint_def.damping_ratio = damping_ratio
        joint_def.draw_size = draw_size
        bone.joint = world.create_joint(joint_def)

    def destroy(self):
        if not self._is_spawned:
            return

        for bone in self.bones:
            if bone.joint is not None:
                bone.joint.destroy()
                bone.joint = None

            if bone.body is not None:
                bone.body.destroy()
                bone.body = None

        self._is_spawned = False

    def set_velocity(self, velocity):
        assert self._is_spawned, "Ragdoll not be destroyed before setting velocity."
        for bone in self.bones:
            if bone.body is not None:
                bone.body.set_linear_velocity(b2d.Vec2(velocity))
