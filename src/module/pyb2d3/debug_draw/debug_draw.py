from .._pyb2d3 import DebugDrawBase, transform_point
import math


class DebugDraw(DebugDrawBase):
    def __init__(self):
        super().__init__(self)

    def begin_draw(self):
        pass

    def end_draw(self):
        pass

    def draw_solid_rect(self, center, shape, color):
        # via draw solid_polygon
        hw, hh = shape[0] / 2, shape[1] / 2
        vertices = [
            (center[0] - hw, center[1] - hh),
            (center[0] + hw, center[1] - hh),
            (center[0] + hw, center[1] + hh),
            (center[0] - hw, center[1] + hh),
        ]
        self.draw_solid_polygon(vertices, color)

    def draw_rect(self, center, shape, line_width, color, width_in_pixels=False):
        # via draw solid_polygon
        hw, hh = shape[0] / 2, shape[1] / 2
        vertices = [
            (center[0] - hw, center[1] - hh),
            (center[0] + hw, center[1] - hh),
            (center[0] + hw, center[1] + hh),
            (center[0] - hw, center[1] + hh),
        ]
        self.draw_polygon(
            vertices,
            line_width=line_width,
            color=color,
            width_in_pixels=width_in_pixels,
        )

    def draw_polygon(self, points, line_width, color, width_in_pixels=False):
        raise NotImplementedError("draw_polygon must be implemented in a subclass")

    def draw_solid_polygon(self, points, color):
        raise NotImplementedError(
            "draw_solid_polygon must be implemented in a subclass"
        )

    def draw_circle(self, center, radius, line_width, color, width_in_pixels=False):
        raise NotImplementedError("draw_circle must be implemented in a subclass")

    def draw_solid_circle(self, center, radius, color):
        raise NotImplementedError("draw_solid_circle must be implemented in a subclass")

    def draw_line(self, p1, p2, line_width, color, width_in_pixels=False):
        raise NotImplementedError("draw_line must be implemented in a subclass")

    def draw_solid_rounded_polygon(self, points, radius, color):
        """Draw a filled polygon with rounded corners directly on the surface."""
        n = len(points)

        for i in range(n):
            p1 = points[i]
            p2 = points[(i + 1) % n]

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
            # pygame.draw.polygon(surface, color, [corner1, corner2, corner3, corner4])
            self.draw_solid_polygon(
                points=[corner1, corner2, corner3, corner4], color=color
            )

        # Draw circles at corners
        for p in points:
            # pygame.draw.circle(surface, color, (float(p[0]), float(p[1])), radius)
            self.draw_solid_circle(center=p, radius=radius, color=color)
        # draw the inner part of the polygon
        self.draw_solid_polygon(points=points, color=color)

    def draw_solid_capsule(self, p1, p2, radius, color):

        x1, y1 = p1
        x2, y2 = p2

        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)

        if length <= 0.01:
            # Degenerate case: just draw a circle
            # pygame.draw.circle(surface, color, (x1, y1), radius)
            self.draw_solid_circle(center=(x1, y1), radius=radius, color=color)
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
        # pygame.draw.polygon(surface, color, [corner1, corner2, corner3, corner4])
        self.draw_solid_polygon(
            points=[corner1, corner2, corner3, corner4], color=color
        )

        # Draw end circles
        self.draw_solid_circle(center=(x1, y1), radius=radius, color=color)
        self.draw_solid_circle(center=(x2, y2), radius=radius, color=color)

    def _draw_polygon(self, vertices, color):
        self.draw_polygon(vertices, color, line_width=1, width_in_pixels=True)

    def _draw_solid_polygon(self, transform, vertices, radius, color):
        vertices = [transform_point(transform, v) for v in vertices]
        if radius == 0:
            self.draw_solid_polygon(vertices, color)
        else:
            self.draw_solid_rounded_polygon(vertices, radius=radius, color=color)

    def _draw_circle(self, center, radius, color):
        self.draw_circle(
            center=center,
            radius=radius,
            line_width=1,
            color=color,
            width_in_pixels=True,
        )

    def _draw_solid_circle(self, transform, radius, color):
        self.draw_solid_circle(center=transform.p, radius=radius, color=color)

    def _draw_solid_capsule(self, p1, p2, radius, color):
        self.draw_solid_capsule(p1=p1, p2=p2, radius=radius, color=color)

    def _draw_segment(self, p1, p2, color):
        self.draw_line(p1=p1, p2=p2, line_width=1, color=color, width_in_pixels=True)

    def _draw_transform(self, transform):
        pass

    def _draw_point(self, p, size, color):
        pass

    def _draw_string(self, x, y, string):
        pass

    def _draw_aabb(self, aabb, color):
        pass
