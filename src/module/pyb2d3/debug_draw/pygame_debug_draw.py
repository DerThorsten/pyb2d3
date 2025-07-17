from .debug_draw import DebugDraw
from .._pyb2d3 import transform_point
from .debug_draw import TransformDebugDrawHexaColorFormat
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

    def draw_polygon(self, vertices, color):
        pygame.draw.polygon(
            self.screen, color, [self.world_to_canvas(v) for v in vertices], 1
        )

    def draw_solid_polygon(self, transform, vertices, radius, color):
        vertices = [
            self.world_to_canvas(transform_point(transform, v)) for v in vertices
        ]

        if radius == 0:
            pygame.draw.polygon(self.screen, color, vertices, 0)
        else:
            # Draw rounded polygon
            rounded_polygon(
                self.screen,
                vertices,
                self.transform.scale_world_to_canvas(radius),
                color,
            )

    def draw_circle(self, center, radius, color):
        pygame.draw.circle(
            self.screen,
            color,
            self.world_to_canvas(center),
            self.transform.scale_world_to_canvas(radius),
            1,
        )

    def draw_solid_circle(self, transform, radius, color):
        pygame.draw.circle(
            self.screen,
            color,
            self.world_to_canvas(transform.p),
            self.transform.scale_world_to_canvas(radius),
            0,
        )

    def draw_solid_capsule(self, p1, p2, radius, color):
        canvas_radius = self.transform.scale_world_to_canvas(radius)
        canvas_p1 = self.world_to_canvas(p1)
        canvas_p2 = self.world_to_canvas(p2)

        #  width of the line is 2*canvas_radius + 1
        surface = self.screen  # or replace with the surface you want to draw on

        x1, y1 = canvas_p1
        x2, y2 = canvas_p2

        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)

        if length <= 0.01:
            # Degenerate case: just draw a circle
            pygame.draw.circle(surface, color, (x1, y1), canvas_radius)
            return

        # Unit vector along p1->p2
        ux = dx / length
        uy = dy / length

        # Perpendicular vector
        px = -uy
        py = ux

        # Four corners of the rectangle part
        corner1 = (x1 + px * canvas_radius, y1 + py * canvas_radius)
        corner2 = (x2 + px * canvas_radius, y2 + py * canvas_radius)
        corner3 = (x2 - px * canvas_radius, y2 - py * canvas_radius)
        corner4 = (x1 - px * canvas_radius, y1 - py * canvas_radius)

        # Draw central rectangle
        pygame.draw.polygon(surface, color, [corner1, corner2, corner3, corner4])

        # Draw end circles
        pygame.draw.circle(surface, color, (x1, y1), canvas_radius)
        pygame.draw.circle(surface, color, (x2, y2), canvas_radius)

    def draw_segment(self, p1, p2, color):
        pygame.draw.line(
            self.screen, color, self.world_to_canvas(p1), self.world_to_canvas(p2), 1
        )

    def draw_transform(self, transform):
        pass

    def draw_point(self, p, size, color):
        pass

    def draw_string(self, x, y, string):
        font = pygame.font.Font(None, 24)
        text_surface = font.render(string, True, (0, 0, 0))
        self.screen.blit(text_surface, self.world_to_canvas((x, y)))

    def draw_aabb(self, aabb, color):
        lower_bound = self.world_to_canvas(aabb.lower_bound)
        upper_bound = self.world_to_canvas(aabb.upper_bound)
        pygame.draw.rect(
            self.screen,
            color,
            (
                lower_bound[0],
                lower_bound[1],
                upper_bound[0] - lower_bound[0],
                upper_bound[1] - lower_bound[1],
            ),
            1,
        )


# no need to transform color or coordinates, its all done in the base class!!!


class PygameTransformDebugDraw(TransformDebugDrawHexaColorFormat):
    def __init__(self, transform, screen):
        super().__init__(transform=transform)
        self.screen = screen

    def draw_polygon(self, vertices, color):
        pygame.draw.polygon(self.screen, color, vertices, 1)

    def draw_solid_polygon(self, vertices, radius, color):
        if radius == 0:
            pygame.draw.polygon(self.screen, color, vertices.astype("int"), 0)
        else:
            # Draw rounded polygon
            rounded_polygon(self.screen, vertices, radius, color)

    def draw_circle(self, center, radius, color):
        pygame.draw.circle(self.screen, color, center, radius, 1)

    def draw_solid_circle(self, center, radius, color):
        pygame.draw.circle(self.screen, color, center, radius, 0)

    def draw_solid_capsule(self, p1, p2, radius, color):

        #  width of the line is 2*canvas_radius + 1
        surface = self.screen  # or replace with the surface you want to draw on

        x1, y1 = p1
        x2, y2 = p2

        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)

        if length <= 0.01:
            # Degenerate case: just draw a circle
            pygame.draw.circle(surface, color, (x1, y1), canvas_radius)
            return

        # Unit vector along p1->p2
        ux = dx / length
        uy = dy / length

        # Perpendicular vector
        px = -uy
        py = ux

        # Four corners of the rectangle part
        corner1 = (x1 + px * radius, y1 + py * radius)
        corner2 = (x2 + px * radius, y2 + py * radius)
        corner3 = (x2 - px * radius, y2 - py * radius)
        corner4 = (x1 - px * radius, y1 - py * radius)

        # Draw central rectangle
        pygame.draw.polygon(surface, color, [corner1, corner2, corner3, corner4])

        # Draw end circles
        pygame.draw.circle(surface, color, (x1, y1), radius)
        pygame.draw.circle(surface, color, (x2, y2), radius)

    def draw_segment(self, p1, p2, color):
        pygame.draw.line(self.screen, color, p1, p2, 1)

    def draw_transform(self, transform):
        pass

    def draw_point(self, p, size, color):
        pass

    def draw_string(self, x, y, string):
        pass

    def draw_aabb(self, aabb, color):
        pass
