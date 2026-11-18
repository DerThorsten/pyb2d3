"""A huge pyramid of blocks and heavy meteors falling into it."""

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

BOUNCY = b2d.surface_material(restitution=0.5)
PYRAMID_LEVELS = 40
METEOR_RADIUS = 5.0


@register_sample("Demos", "Meteor", video=True)
class Meteor(SampleBase):
    """A huge pyramid of blocks waiting for a heavy, fast falling meteor.

    Mouse: double click high above the pyramid to drop a meteor there.
    Keys: m creates a meteor at the origin (the left foot of the pyramid).
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.anchor_body.create_shape(
            b2d.shape_def(material=BOUNCY), b2d.segment((-1000, 0), (1000, 0))
        )
        self.create_pyramid(PYRAMID_LEVELS, thickness=0.5, length=3.0)
        if self.frontend.settings.headless:
            self.create_meteor((-35, 300), velocity=(10, 0))

    def create_pyramid(self, levels, thickness, length):
        """Upright blocks, each pair bridged by a lying block, fewer per level."""
        shape_def = b2d.shape_def(density=1, material=BOUNCY)
        upright = b2d.box(hx=thickness / 2, hy=length / 2)
        lying = b2d.box(hx=length / 2, hy=thickness / 2)
        for level in range(levels):
            y = level * (length + thickness)
            for i in range(levels - level):
                x = (i + level / 2) * length
                body = self.world.create_dynamic_body(position=(x, y + length / 2))
                body.create_shape(shape_def, upright)
                if i + 1 < levels - level:
                    body = self.world.create_dynamic_body(
                        position=(x + length / 2, y + length + thickness / 2)
                    )
                    body.create_shape(shape_def, lying)

    def create_meteor(self, position, velocity=(0, 0)):
        meteor = self.world.create_dynamic_body(
            position=position,
            linear_velocity=velocity,
            gravity_scale=4.0,  # falls faster
        )
        meteor.create_shape(
            b2d.shape_def(density=10, material=BOUNCY), b2d.circle(radius=METEOR_RADIUS)
        )

    def aabb(self):
        return b2d.aabb(lower_bound=(-50, -10), upper_bound=(200, 300))

    def on_key_down(self, event):
        if event.key == "m":
            self.create_meteor((0, 0))

    def on_double_click(self, event):
        self.create_meteor(event.world_position)
