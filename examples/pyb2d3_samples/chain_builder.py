# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


class ChainBuilder(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.box_radius = 50

        # create a chain shape
        builder = b2d.PathBuilder((0, 0))
        builder.line_to(right=5)
        builder.line_to(up=5)
        builder.line_to(left=5)
        builder.arc_to(down=5, radius=5 / 2, clockwise=False, segments=20)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

        # create a chain shape
        builder = b2d.PathBuilder((0, -10))
        builder.line_to(right=5)
        builder.line_to(up=5)
        builder.line_to(left=5)
        builder.arc_to(down=5, radius=5 / 2, clockwise=True, segments=20)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

        # create a chain shape
        builder = b2d.PathBuilder((0, -20))
        builder.line_to(right=5)
        builder.arc_to(up=5, radius=5 / 2, clockwise=False, segments=20)
        builder.line_to(left=5)
        builder.arc_to(down=5, radius=5 / 2, clockwise=True, segments=20)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

        # create a chain shape
        builder = b2d.PathBuilder((0, -30))
        builder.line_to(right=5)
        builder.arc_to(up=5, radius=3, clockwise=False, segments=20)
        builder.line_to(left=5)
        builder.arc_to(down=5, radius=3, clockwise=True, segments=20)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

        # create a chain shape
        builder = b2d.PathBuilder((0, -40))
        builder.line_to(right=5)
        builder.arc_to(up=5, radius=3, clockwise=False, segments=20, major_arc=False)
        builder.line_to(left=5)
        builder.arc_to(down=5, radius=3, clockwise=False, segments=20, major_arc=True)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

        # billiard table
        w = 8
        h = w / 2

        # top_left_corner
        top_left_corner = (0, 20)

        # pocket radius
        r = 0.5

        md = r * 2
        cd = r

        # start with left pocket arc
        start = (top_left_corner[0], top_left_corner[1])
        builder = b2d.PathBuilder(start)
        builder.arc_to(delta=(-cd, -cd), radius=r, clockwise=False, segments=20, major_arc=True)

        # move down by height
        builder.line_to(down=h)

        # add bottom left corner pocket
        builder.arc_to(delta=(cd, -cd), radius=r, clockwise=False, segments=20, major_arc=True)

        # move right by width /2
        builder.line_to(right=w / 2)
        # add bottom middle pocket
        builder.arc_to(delta=(md, 0), radius=r, clockwise=False, segments=20, major_arc=True)

        # move right by width /2
        builder.line_to(right=w / 2)
        # add bottom right corner pocket
        builder.arc_to(delta=(cd, cd), radius=r, clockwise=False, segments=20, major_arc=True)

        # move up by height
        builder.line_to(up=h)
        # add top right corner pocket
        builder.arc_to(delta=(-cd, cd), radius=r, clockwise=False, segments=20, major_arc=True)

        # move left by width/2
        builder.line_to(left=w / 2)
        # add top middle pocket
        builder.arc_to(delta=(-md, 0), radius=r, clockwise=False, segments=20, major_arc=True)
        # move left by width/2
        builder.line_to(left=w / 2)

        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.box_radius, -self.box_radius),
            upper_bound=(self.box_radius, self.box_radius),
        )


if __name__ == "__main__":
    ChainBuilder.run()
