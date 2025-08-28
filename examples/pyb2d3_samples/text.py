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

        # # Create a blank white image
        # W, H = 100, 100
        # image = Image.new("L", (W, H), color=255)  # "L" = grayscale, 255 = white
        # # Draw text
        # draw = ImageDraw.Draw(image)
        # font = ImageFont.load_default()  # or ImageFont.truetype("arial.ttf", 24)
        # draw.text((20, 40), "Notebook", font=font, fill=0)  # 0 = black text
        # arr = np.array(image)
        # # flip ud
        # arr = np.flipud(arr)

        # def pixel_to_world(x,y):
        #     # to [0,1]
        #     x = x / W
        #     y = y / H

        #     # to [-box_radius, box_radius]
        #     x = (x - 0.5) * 2 * self.box_radius
        #     y = (y - 0.5) * 2 * self.box_radius
        #     return x, y

        # # world size of single pixel
        # pixel_size = (2 * self.box_radius / W, 2 * self.box_radius / H)

        # where_black = np.argwhere(arr <= 100)
        # for y, x in where_black:
        #     print(f"Creating box at pixel: ({x}, {y})")
        #     world_pos = pixel_to_world(x,y)
        #     pixel_body = self.world.create_dynamic_body(position=world_pos)
        #     box = b2d.box(hx=pixel_size[0] / 2, hy=pixel_size[1] / 2)
        #     pixel_body.create_shape(b2d.shape_def(density=1.0), box)

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.box_radius, -self.box_radius),
            upper_bound=(self.box_radius, self.box_radius),
        )


if __name__ == "__main__":
    Text.run()
