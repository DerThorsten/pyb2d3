import pyb2d3 as b2d
from pyb2d3.samples import SampleBase


from dataclasses import dataclass

# some constants to not overcomplicate the example
BALL_RADIUS = 0.1


@dataclass
class CourseLevelData:
    # where are the 2 balls placed?
    start_positions = list[tuple]

    # where is the hole?
    hole_position = tuple

    # the polygons of the course
    course_polygons = list[list[tuple]]


Levels = [
    CourseLevelData(
        start_positions=[(1, 1), (1, 2)],
        hole_position=(5, 1),
        course_polygons=[[(0, 0), (0, 2), (6, 2), (6, 0)]],
    )
]


class CoupledMinigolf(SampleBase):
    @dataclass
    class Settings(SampleBase.Settings):
        current_level: int = 0

    def __init__(self, settings):
        super().__init__(settings.set_gravity((0, -50)))
        self.outer_box_radius = 100

        # attach the chain shape to a static body
        self.box_body = self.world.create_static_body(position=(0, 0))

        self.level = Levels[settings.current_level]

        # create the chains

    def aabb(self):
        eps = 0.01
        r = self.outer_box_radius + eps
        return b2d.aabb(
            lower_bound=(-r, -r),
            upper_bound=(r, r),
        )


if __name__ == "__main__":
    CoupledMinigolf.run()
