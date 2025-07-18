from .._pyb2d3 import DebugDrawBase


class DebugDraw(DebugDrawBase):
    def __init__(self):
        super().__init__(self)

    def _draw_polygon(self, vertices, color):
        pass

    def _draw_solid_polygon(self, transform, vertices, radius, color):
        pass

    def _draw_circle(self, center, radius, color):
        pass

    def _draw_solid_circle(self, transform, radius, color):
        pass

    def _draw_solid_capsule(self, p1, p2, radius, color):
        pass

    def _draw_segment(self, p1, p2, color):
        pass

    def _draw_transform(self, transform):
        pass

    def _draw_point(self, p, size, color):
        pass

    def _draw_string(self, x, y, string):
        pass

    def _draw_aabb(self, aabb, color):
        pass
