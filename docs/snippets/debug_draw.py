import pyb2d3 as b2d


class PrintingDraw(b2d.DebugDraw):
    """Implement the methods you need; all coordinates are in world space, colors are 0xRRGGBB ints."""

    def draw_solid_polygon(self, transform, points, radius, color):
        # points are in the local frame of `transform`
        print("polygon", len(points), "vertices at", transform.p)

    def draw_solid_circle(self, transform, radius, color):
        print("circle at", transform.p, "radius", radius)

    def draw_segment(self, p1, p2, color):
        print("segment", p1, p2)


world = b2d.World()
body = world.create_dynamic_body(position=(1, 2))
body.create_shape(b2d.shape_def(), b2d.box(0.5, 0.5))
body.create_shape(b2d.shape_def(), b2d.circle(center=(1, 0), radius=0.25))

draw = PrintingDraw()
draw.drawing_bounds = b2d.aabb((-100, -100), (100, 100))  # only shapes inside are drawn
draw.draw_shapes = True
draw.draw_joints = True
world.draw(draw)
