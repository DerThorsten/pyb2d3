import pyb2d3 as b2d
from pyb2d3.samples import SampleBase


from dataclasses import dataclass

# some constants to not overcomplicate the example
BALL_RADIUS = 0.1
HOLE_RADIUS = 0.2
FORCE_VECTOR_DRAW_WIDTH = 0.05
MAX_FORCE_VECTOR_LENGTH = 2
BALL_COLORS = [b2d.hex_color(100, 100, 220), b2d.hex_color(100, 100, 220)]


@dataclass
class LevelData:
    # where are the 2 balls placed?
    start_positions: list[tuple]

    # where is the hole?
    hole_position: tuple

    # the polygons of the course
    course_polygons: list[list[tuple]]


eps = 0.25
Levels = [
    LevelData(
        start_positions=[(1, 1), (1, 1.8)],
        hole_position=(5, 1),
        course_polygons=[[(0, 0), (0, 2), (6, 2), (6, 0)]],
    ),
    LevelData(
        start_positions=[(1, 1), (1, 1.8)],
        hole_position=(5, -1),
        course_polygons=[
            [
                (0, 0),
                (0, 2),
                (6, 2),
                (6, -2),
                (4, -2),
                (4, 0),
            ]
        ],
    ),
    LevelData(
        start_positions=[(1, 1.75), (1, 2.8)],
        hole_position=(1, 5),
        course_polygons=[
            [(0, 0), (0, 2), (2.5, 2), (2.5, 4), (0, 4), (0, 6), (4, 6), (4, 0)],
            [
                (0 + eps, 2 + eps),
                (0 + eps, 4 - eps),
                (2 - eps, 4 - eps),
                (2 - eps, 2 + eps),
            ],
        ],
    ),
]


class Goo(SampleBase):
    @dataclass
    class Settings(SampleBase.Settings):
        current_level: int = 0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.outer_box_radius = 100

        # attach the chain shape to a static body
        self.box_body = self.world.create_static_body(position=(0, 0))
        self.box_body.create_chain(
            b2d.chain_box(hx=self.outer_box_radius, hy=self.outer_box_radius)
        )

        # data for the current level
        self.level = Levels[settings.current_level]

    def post_debug_draw(self):
        # draw hud in screen coordinates
        w = self.canvas_shape[0]
        hud_width = w / 15
        hud_height = self.canvas_shape[1]

        # we need to place n circles below each other
        n = 5

        # we would like to make the radius of the circle the biggest possible
        # so we calculate the radius based on the height of the canvas and the number of circles
        radius = (hud_height / n) / 2
        if radius > hud_width / 2:
            radius = hud_width / 2

        # we need to place the circles in the middle of the hud
        x = hud_width / 2
        for i in range(n):
            y = (hud_height / n) * (i + 0.5)

            # draw the circle
            self.debug_draw.draw_solid_circle(
                center=(x, y),
                radius=radius,
                color=BALL_COLORS[i % len(BALL_COLORS)],
                world_coordinates=False,
            )

    def aabb(self):
        # bouding box from self.levels.course_polygons
        r = self.outer_box_radius + 1
        return b2d.aabb(lower_bound=(-r, -r), upper_bound=(r, r))


if __name__ == "__main__":
    Goo.run()
