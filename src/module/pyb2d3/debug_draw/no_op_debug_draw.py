from .debug_draw import DebugDraw


class NoopDebugDraw(DebugDraw):
    def __init__(self):
        super().__init__()

    def draw_polygon(self, vertices, color, line_width, width_in_pixels=False):
        pass

    def draw_solid_polygon(self, points, color):
        pass

    def draw_circle(self, center, radius, line_width, color, width_in_pixels=False):
        pass

    def draw_solid_circle(self, center, radius, color):
        pass

    def draw_line(self, p1, p2, line_width, color, width_in_pixels=False):
        pass
