from .debug_draw import DebugDraw
from .._pyb2d3 import transform_point
import pygame
import math


def rounded_polygon(surface, vertices, radius, color):
    """Draw a filled polygon with rounded corners directly on the surface."""
    n = len(vertices)

    for i in range(n):
        p1 = vertices[i]
        p2 = vertices[(i + 1) % n]

        # Vector from p1 to p2
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)

        # Unit perpendicular vector
        ux = dx / length
        uy = dy / length
        perp_x = -uy
        perp_y = ux

        # Offset corners by radius along perpendicular
        corner1 = (float(p1[0] + perp_x * radius), float(p1[1] + perp_y * radius))
        corner2 = (float(p2[0] + perp_x * radius), float(p2[1] + perp_y * radius))
        corner3 = (float(p2[0] - perp_x * radius), float(p2[1] - perp_y * radius))
        corner4 = (float(p1[0] - perp_x * radius), float(p1[1] - perp_y * radius))

        # Draw rectangle as polygon
        pygame.draw.polygon(surface, color, [corner1, corner2, corner3, corner4])

    # Draw circles at corners
    for p in vertices:
        pygame.draw.circle(surface, color, (float(p[0]), float(p[1])), radius)

    # draw the inner part of the polygon
    if isinstance(vertices, list):
        pygame.draw.polygon(surface, color, vertices, 0)
    else:
        pygame.draw.polygon(surface, color, vertices.astype("int"), 0)


class PygameDebugDraw(DebugDraw):
    def __init__(self, transform, screen):
        self.screen = screen
        self.transform = transform
        super().__init__()

    def convert_hex_color(self, hex_color):
        # we have a hexadecimal color **as integer**
        r = (hex_color >> 16) & 0xFF
        g = (hex_color >> 8) & 0xFF
        b = hex_color & 0xFF
        return (r, g, b)

    def world_to_canvas(self, world_point):
        return self.transform.world_to_canvas(world_point)

    # def draw_rect(self, center, shape, line_width, color, width_in_pixels):
    #     if not width_in_pixels:
    #         line_width = self.transform.scale_world_to_canvas(line_width)

    #     canvas_width  = self.transform.scale_world_to_canvas(shape[0])
    #     canvas_height = self.transform.scale_world_to_canvas(shape[1])
    #     canvas_center = self.world_to_canvas(center)

    #     pygame.draw.rect(
    #         self.screen,
    #         color,
    #         pygame.Rect(
    #             canvas_center[0] - canvas_width / 2,
    #             canvas_center[1] - canvas_height / 2,
    #             canvas_width,
    #             canvas_height
    #         ),
    #         round(line_width)
    #     )

    def draw_polygon(self, vertices, color, line_width, width_in_pixels=False):
        if not width_in_pixels:
            line_width = self.transform.scale_world_to_canvas(line_width)
        pygame.draw.polygon(
            self.screen,
            color,
            [self.world_to_canvas(v) for v in vertices],
            round(line_width),
        )

    def draw_solid_polygon(self, vertices, color):
        pygame.draw.polygon(
            self.screen, color, [self.world_to_canvas(v) for v in vertices], 0
        )

    def draw_circle(self, center, radius, line_width, color, width_in_pixels=False):

        if not width_in_pixels:
            line_width = self.transform.scale_world_to_canvas(line_width)

        pygame.draw.circle(
            self.screen,
            color,
            self.world_to_canvas(center),
            self.transform.scale_world_to_canvas(radius),
            round(line_width),
        )

    def draw_solid_circle(self, center, radius, color):
        pygame.draw.circle(
            self.screen,
            color,
            self.world_to_canvas(center),
            self.transform.scale_world_to_canvas(radius),
            0,
        )

    def draw_line(self, p1, p2, line_width, color, width_in_pixels=False):
        if not width_in_pixels:
            line_width = self.transform.scale_world_to_canvas(line_width)

        pygame.draw.line(
            self.screen,
            color,
            self.world_to_canvas(p1),
            self.world_to_canvas(p2),
            round(line_width),
        )
