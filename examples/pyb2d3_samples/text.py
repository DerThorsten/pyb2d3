# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase

# from PIL import Image, ImageDraw, ImageFont


try:
    import examples_common  # noqa: F401, E402
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import examples_common  # noqa: F401, E402


class Text(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.box_radius = 15

        # attach the chain shape to a static body
        self.box_body = self.world.create_static_body(position=(0, 0))
        chain_def = b2d.chain_box(center=(0, 0), hx=self.box_radius, hy=self.box_radius)
        chain_def.filter = b2d.make_filter(category_bits=0x0001, mask_bits=0x0001)
        self.box_body.create_chain(
            b2d.chain_box(center=(0, 0), hx=self.box_radius, hy=self.box_radius)
        )

        examples_common.create_boxes_from_text(
            world=self.world, text="pyb2d3", height=3, position=(-3, 0)
        )

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.box_radius, -self.box_radius),
            upper_bound=(self.box_radius, self.box_radius),
        )


if __name__ == "__main__":
    Text.run()
