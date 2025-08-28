import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pyb2d3 as b2d


def create_boxes_from_text(world, text, position, height, font_size=20):
    # Create a  big blank white image
    W, H = 1000, 1000
    image = Image.new("L", (W, H), color=255)  # "L" = grayscale, 255 = white

    # Draw text
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=20)  # or ImageFont.truetype("arial.ttf", 24)
    draw.text((20, 40), text, font=font, fill=0)  # 0 = black text
    arr = np.array(image)

    where_black = np.argwhere(arr <= 255 / 2)

    # crop st. we only keep the black pixels
    arr = arr[
        where_black[:, 0].min() : where_black[:, 0].max() + 1,
        where_black[:, 1].min() : where_black[:, 1].max() + 1,
    ]

    # # show arr with matplotlib
    # import matplotlib.pyplot as plt
    # plt.imshow(arr, cmap='gray')
    # plt.show()

    # # flip ud
    arr = np.flipud(arr)

    pixel_height = arr.shape[0]
    scaling = height / pixel_height

    def pixel_to_world(x, y):
        x = (x) * scaling + 0.5 * scaling
        y = (y) * scaling + 0.5 * scaling
        return position[0] + x, position[1] + y

    pixel_width = scaling
    pixel_height = scaling

    slack_factor = 0.9
    where_black = np.argwhere(arr <= 100)
    for y, x in where_black:
        val = (255 - arr[y, x]) / 255  # how black in [0,1]
        val *= slack_factor

        world_pos = pixel_to_world(x, y)
        pixel_body = world.create_dynamic_body(position=world_pos)
        box = b2d.box(hx=val * pixel_width / 2, hy=val * pixel_height / 2)
        pixel_body.create_shape(b2d.shape_def(density=1.0), box)
