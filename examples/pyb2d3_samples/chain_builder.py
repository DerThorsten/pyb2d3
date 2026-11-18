"""Static chain shapes drawn with b2d.PathBuilder: lines, arcs and a billiard table."""

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

VIEW = 50  # half size of the shown region (m)
SEGMENTS = 20  # line segments per arc


@register_sample("Demos", "Chain Builder")
class ChainBuilder(SampleBase):
    """Static chain shapes drawn with b2d.PathBuilder: lines plus arcs (clockwise or not,
    minor or major arc), and a billiard table outline with pockets.

    There are no dynamic bodies; zoom with the mouse wheel to look at the outlines.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.create_arc_examples()
        self.create_billiard_table(top_left=(0, 20), width=8, pocket_radius=0.5)

    def create_arc_examples(self):
        """5 x 5 squares, one above the other, with different arcs as their sides"""
        # left side: an arc bulging out (counter clockwise) ...
        path = b2d.PathBuilder((0, 0))
        path.line_to(right=5)
        path.line_to(up=5)
        path.line_to(left=5)
        path.arc_to(down=5, radius=2.5, clockwise=False, segments=SEGMENTS)
        self.anchor_body.create_chain(path.chain_def(is_loop=True))

        # ... or bulging in (clockwise)
        path = b2d.PathBuilder((0, -10))
        path.line_to(right=5)
        path.line_to(up=5)
        path.line_to(left=5)
        path.arc_to(down=5, radius=2.5, clockwise=True, segments=SEGMENTS)
        self.anchor_body.create_chain(path.chain_def(is_loop=True))

        # both sides arcs: half circles
        path = b2d.PathBuilder((0, -20))
        path.line_to(right=5)
        path.arc_to(up=5, radius=2.5, clockwise=False, segments=SEGMENTS)
        path.line_to(left=5)
        path.arc_to(down=5, radius=2.5, clockwise=True, segments=SEGMENTS)
        self.anchor_body.create_chain(path.chain_def(is_loop=True))

        # a radius larger than half the distance: flatter arcs
        path = b2d.PathBuilder((0, -30))
        path.line_to(right=5)
        path.arc_to(up=5, radius=3, clockwise=False, segments=SEGMENTS)
        path.line_to(left=5)
        path.arc_to(down=5, radius=3, clockwise=True, segments=SEGMENTS)
        self.anchor_body.create_chain(path.chain_def(is_loop=True))

        # the same circle, but the long way round (major arc) on the left
        path = b2d.PathBuilder((0, -40))
        path.line_to(right=5)
        path.arc_to(up=5, radius=3, clockwise=False, segments=SEGMENTS, major_arc=False)
        path.line_to(left=5)
        path.arc_to(down=5, radius=3, clockwise=False, segments=SEGMENTS, major_arc=True)
        self.anchor_body.create_chain(path.chain_def(is_loop=True))

    def create_billiard_table(self, top_left, width, pocket_radius):
        """the cushions of a 2:1 table, counter clockwise, with six major arc pockets"""
        r = pocket_radius
        height = width / 2
        pocket = dict(radius=r, clockwise=False, segments=SEGMENTS, major_arc=True)

        path = b2d.PathBuilder(top_left)
        path.arc_to(delta=(-r, -r), **pocket)  # top left
        path.line_to(down=height)
        path.arc_to(delta=(r, -r), **pocket)  # bottom left
        path.line_to(right=width / 2)
        path.arc_to(delta=(2 * r, 0), **pocket)  # bottom middle
        path.line_to(right=width / 2)
        path.arc_to(delta=(r, r), **pocket)  # bottom right
        path.line_to(up=height)
        path.arc_to(delta=(-r, r), **pocket)  # top right
        path.line_to(left=width / 2)
        path.arc_to(delta=(-2 * r, 0), **pocket)  # top middle
        path.line_to(left=width / 2)
        self.anchor_body.create_chain(path.chain_def(is_loop=True))

    def aabb(self):
        return b2d.aabb(lower_bound=(-VIEW, -VIEW), upper_bound=(VIEW, VIEW))
