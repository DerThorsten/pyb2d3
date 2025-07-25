import pyb2d3 as b2d
from pyb2d3.samples import SampleBase


import math


class PathBuilder(object):
    def __init__(self, start):
        self.points = [start]

    def chain_def(self, is_loop=False, material=None):
        return b2d.chain_def(self.points, is_loop=is_loop, material=material)

    def _point(self, **point_args):
        assert len(point_args) == 1, (
            "Only one of point, delta, left, right, up, down must be given"
        )
        last_point = self.points[-1]
        if "point" in point_args:
            return point_args["point"]
        elif "delta" in point_args:
            return (
                last_point[0] + point_args["delta"][0],
                last_point[1] + point_args["delta"][1],
            )
        elif "left" in point_args:
            return (last_point[0] - point_args["left"], last_point[1])
        elif "right" in point_args:
            return (last_point[0] + point_args["right"], last_point[1])
        elif "up" in point_args:
            return (last_point[0], last_point[1] + point_args["up"])
        elif "down" in point_args:
            return (last_point[0], last_point[1] - point_args["down"])
        else:
            raise ValueError("No valid point or delta provided")

    def line_to(self, **point_args):
        self.points.append(self._point(**point_args))
        return self

    def arc_to(
        self, /, radius, clockwise=True, segments=10, major_arc=False, **point_args
    ):
        from_point = self.points[-1]
        to_point = self._point(**point_args)

        dx = to_point[0] - from_point[0]
        dy = to_point[1] - from_point[1]
        chord_length = math.hypot(dx, dy)

        if radius < chord_length / 2:
            raise ValueError("Radius too small to form an arc between the points")

        # Midpoint of the chord
        mx = (from_point[0] + to_point[0]) / 2
        my = (from_point[1] + to_point[1]) / 2

        # Distance from midpoint to circle center (h)
        h = math.sqrt(radius**2 - (chord_length / 2) ** 2)

        # Perpendicular unit vector to the chord
        perp_dx = -dy / chord_length
        perp_dy = dx / chord_length

        # Compute both possible centers
        center1 = (mx + h * perp_dx, my + h * perp_dy)
        center2 = (mx - h * perp_dx, my - h * perp_dy)

        # Compute angles from centers to points
        def arc_angle(center):
            a1 = math.atan2(from_point[1] - center[1], from_point[0] - center[0])
            a2 = math.atan2(to_point[1] - center[1], to_point[0] - center[0])
            delta = (a2 - a1) % (2 * math.pi)
            return delta if clockwise else (2 * math.pi - delta)

        # Select center that gives the minor arc in the desired direction
        angle1 = arc_angle(center1)
        # angle2 = arc_angle(center2)

        if (angle1 <= math.pi) == major_arc:
            center = center1
            start_angle = math.atan2(
                from_point[1] - center[1], from_point[0] - center[0]
            )
            end_angle = math.atan2(to_point[1] - center[1], to_point[0] - center[0])
        else:
            center = center2
            start_angle = math.atan2(
                from_point[1] - center[1], from_point[0] - center[0]
            )
            end_angle = math.atan2(to_point[1] - center[1], to_point[0] - center[0])

        # Normalize angle span to always go minor arc direction
        if clockwise:
            if end_angle > start_angle:
                end_angle -= 2 * math.pi
        else:
            if end_angle < start_angle:
                end_angle += 2 * math.pi

        # Generate arc points
        for i in range(1, segments + 1):
            t = i / segments
            angle = start_angle + (end_angle - start_angle) * t
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            self.points.append((x, y))


class ChainBuilderExample(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.box_radius = 30

        # create a chain shape
        builder = PathBuilder((0, 0))
        builder.line_to(right=5).line_to(up=5).line_to(left=5)
        builder.arc_to(down=5, radius=5 / 2, clockwise=False, segments=20)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

        # create a chain shape
        builder = PathBuilder((0, -10))
        builder.line_to(right=5).line_to(up=5).line_to(left=5)
        builder.arc_to(down=5, radius=5 / 2, clockwise=True, segments=20)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

        # create a chain shape
        builder = PathBuilder((0, -20))
        builder.line_to(right=5)
        builder.arc_to(up=5, radius=5 / 2, clockwise=False, segments=20)
        builder.line_to(left=5)
        builder.arc_to(down=5, radius=5 / 2, clockwise=True, segments=20)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

        # create a chain shape
        builder = PathBuilder((0, -30))
        builder.line_to(right=5)
        builder.arc_to(up=5, radius=3, clockwise=False, segments=20)
        builder.line_to(left=5)
        builder.arc_to(down=5, radius=3, clockwise=True, segments=20)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

        # create a chain shape
        builder = PathBuilder((0, -40))
        builder.line_to(right=5)
        builder.arc_to(up=5, radius=3, clockwise=False, segments=20, major_arc=False)
        builder.line_to(left=5)
        builder.arc_to(down=5, radius=3, clockwise=False, segments=20, major_arc=True)
        self.anchor_body.create_chain(builder.chain_def(is_loop=True))

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.box_radius, -self.box_radius),
            upper_bound=(self.box_radius, self.box_radius),
        )


if __name__ == "__main__":
    ChainBuilderExample.run()
