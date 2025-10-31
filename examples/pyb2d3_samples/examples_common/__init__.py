from .ragdoll import Ragdoll  # noqa: F401
from .text import create_boxes_from_text  # noqa: F401
from .math import truncated_vector_diff, interpolate_color  # noqa: F401

import pyb2d3 as b2d


def stacked_blocks(world, num_blocks_base, box_shape, start):
    start_x = start[0]
    start_y = start[1]
    distance_x = box_shape[1]

    for outer in range(num_blocks_base):
        start_y_inner = start_y + outer * (box_shape[1] + box_shape[0])
        for i in range(num_blocks_base - outer):
            x = start_x + (i + outer / 2) * distance_x
            y = start_y_inner + box_shape[1] / 2
            body = world.create_dynamic_body(position=(x, y))
            body.create_shape(
                b2d.shape_def(density=1, material=b2d.surface_material(restitution=0.5)),
                b2d.box(hx=box_shape[0] / 2, hy=box_shape[1] / 2),
            )

            if i + 1 < num_blocks_base - outer:
                # create a second block on top
                body = world.create_dynamic_body(
                    position=(
                        x + box_shape[1] / 2,
                        start_y_inner + box_shape[1] + box_shape[0] / 2,
                    )
                )
                body.create_shape(
                    b2d.shape_def(density=1, material=b2d.surface_material(restitution=0.5)),
                    b2d.box(hx=box_shape[1] / 2, hy=box_shape[0] / 2),
                )
