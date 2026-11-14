"""Helpers shared by the ports of sample_continuous.cpp and sample_robustness.cpp."""

import pyb2d3 as b2d
from pyb2d3_sandbox import widgets

from ..examples_common.ragdoll import Ragdoll


def attr_slider(sample, label, attr, min_value, max_value, step, on_change=None, cls=widgets.FloatSlider):
    """A slider bound to `sample.<attr>`; `on_change()` runs after every change."""

    def callback(value):
        setattr(sample, attr, value)
        if on_change is not None:
            on_change()

    return cls(
        label=label,
        min_value=min_value,
        max_value=max_value,
        step=step,
        value=getattr(sample, attr),
        callback=callback,
    )


def create_box_walls(body, shape_def, half_extent=10.0):
    """Four segments enclosing the square [-half_extent, half_extent]^2."""
    h = half_extent
    corners = [(-h, -h), (h, -h), (h, h), (-h, h)]
    for p1, p2 in zip(corners, corners[1:] + corners[:1]):
        body.create_shape(shape_def, b2d.segment(p1, p2))


def create_human(world, position, scale, friction_torque, hertz, damping_ratio, group_index=1, colorize=True):
    """box2d's CreateHuman (shared/human.c): a ragdoll whose joints use motors as joint friction."""
    human = Ragdoll(
        world,
        position=position,
        scale=scale,
        friction_torque=friction_torque,
        hertz=hertz,
        damping_ratio=damping_ratio,
        group_index=group_index,
        colorize=colorize,
    )
    for bone in human.bones:
        if bone.joint is not None:
            bone.joint.motor_enabled = True
    return human


def destroy_human(human):
    """box2d's DestroyHuman: joints first, then the bodies."""
    # Ragdoll.destroy() destroys joints whose body is already gone, which crashes
    # (Joint.destroy() on a stale id), so the joints go first here.
    for bone in human.bones:
        if bone.joint is not None and bone.joint.is_valid:
            bone.joint.destroy()
        bone.joint = None
    for bone in human.bones:
        if bone.body is not None and bone.body.is_valid:
            bone.body.destroy()
        bone.body = None
