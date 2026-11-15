"""Ports of box2d's samples/sample_issues.cpp."""

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample

from ._common import Box2dSample


@register_sample("Issues", "Unstable Prismatic Joints")
class UnstablePrismaticJoints(Box2dSample):
    """Stresses the solver with a light mass between two bodies on prismatic joints with stiff springs.

    This can be made stable by increasing the size of the middle circle and/or the number of sub-steps.
    """

    camera_center = (0.0, 1.75)
    camera_zoom = 32.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        self.create_ground_segment(-100.0, 100.0)

        center = world.create_dynamic_body(position=(0, 3))
        # note: this diverges (inf/nan) with a radius of 0.1
        center.create_shape(b2d.shape_def(), b2d.circle(radius=0.5))

        for x, target_translation in ((-3.5, -3.0), (3.5, 3.0)):
            body = world.create_dynamic_body(position=(x, 3))
            body.create_shape(b2d.shape_def(), b2d.circle(radius=2.0))
            world.create_prismatic_joint(
                body_a=center,
                body_b=body,
                enable_spring=True,
                hertz=10.0,
                damping_ratio=2.0,
                target_translation=target_translation,
            )


@register_sample("Issues", "Unstable Windmill")
class UnstableWindmill(Box2dSample):
    """A windmill of boxes welded to a heavy circle, this configuration has stability problems."""

    camera_center = (0.0, 1.75)
    camera_zoom = 32.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        self.create_ground_segment(-100.0, 100.0, y=-10.0)

        shape_def = b2d.shape_def(material=b2d.surface_material(friction=0.1))

        center = world.create_dynamic_body(position=(10, 10), gravity_scale=0.0)
        center.create_shape(shape_def, b2d.circle(radius=5))

        # rotors: position, half extents, anchor on the center, anchor on the rotor
        for position, (hx, hy), anchor_a, anchor_b in (
            ((10, 0), (4, 5), (0, -5), (0, 5)),
            ((20, 10), (5, 4), (5, 0), (-5, 0)),
            ((10, 20), (4, 5), (0, 5), (0, -5)),
            ((0, 10), (5, 4), (-5, 0), (5, 0)),
        ):
            body = world.create_dynamic_body(position=position, gravity_scale=0.0)
            body.create_shape(shape_def, b2d.box(hx, hy))
            # this simulation can be stabilized by using a lower constraint stiffness (constraint_hertz=30)
            world.create_weld_joint(body_a=center, body_b=body, local_anchor_a=anchor_a, local_anchor_b=anchor_b)
