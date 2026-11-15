"""Helpers shared by the shapes and restitution sample ports (box2d's samples/utils + sample.cpp)."""

import random

import pyb2d3 as b2d

WHITE = b2d.HexColor.White.value
LINEAR_SLOP = 0.005  # B2_LINEAR_SLOP


def random_vec2(lo, hi):
    return (random.uniform(lo, hi), random.uniform(lo, hi))


def random_polygon(extent):
    """A random convex polygon with 3 to 8 vertices (box2d's RandomPolygon)."""
    points = [random_vec2(-extent, extent) for _ in range(random.randint(3, 8))]
    hull = b2d.compute_hull(points)
    if hull.count > 0:
        return b2d.make_polygon(hull, 0.0)
    return b2d.make_square(extent)


def parse_svg_path(path, offset, scale, capacity=20):
    """Points of a simple svg path (M/L/H/V and relative m/l/h/v), y flipped (box2d's Sample::ParsePath)."""
    points = []
    x = y = 0.0
    command = None
    for token in path.split():
        if token[0].isalpha():
            command = token
            if command == "z":
                break
            continue
        values = [float(v) for v in token.split(",")]
        if command in ("M", "L"):
            x, y = values
        elif command == "H":
            x = values[0]
        elif command == "V":
            y = values[0]
        elif command in ("m", "l"):
            x, y = x + values[0], y + values[1]
        elif command == "h":
            x += values[0]
        elif command == "v":
            y += values[0]
        else:
            raise ValueError(f"unsupported svg path command {command!r}")
        points.append((scale * (x + offset[0]), -scale * (y + offset[1])))
        if len(points) == capacity:
            break

    # remove the loop point for chain shapes
    if len(points) > 2:
        (x0, y0), (x1, y1) = points[0], points[-1]
        if (x1 - x0) ** 2 + (y1 - y0) ** 2 <= LINEAR_SLOP**2:
            points.pop()
    return points


def compute_energy(world, bodies):
    """(linear kinetic, angular kinetic, potential) energy of the bodies."""
    gx, gy = world.gravity
    linear = angular = potential = 0.0
    for body in bodies:
        mass_data = body.mass_data
        vx, vy = body.linear_velocity
        w = body.angular_velocity
        cx, cy = body.world_center
        linear += 0.5 * mass_data.mass * (vx * vx + vy * vy)
        angular += 0.5 * mass_data.rotational_inertia * w * w
        potential -= mass_data.mass * (gx * cx + gy * cy)
    return linear, angular, potential


class EnergyMeter:
    """Tracks the total energy of some bodies relative to the start and the peak."""

    def __init__(self, world, bodies):
        self.world = world
        self.bodies = list(bodies)
        self.start = sum(compute_energy(world, self.bodies))
        self.peak = self.start
        self.linear = self.angular = self.potential = 0.0
        self.update()

    @property
    def total(self):
        return self.linear + self.angular + self.potential

    def update(self):
        self.linear, self.angular, self.potential = compute_energy(self.world, self.bodies)
        self.peak = max(self.peak, self.total)

    def lines(self):
        scale = 100.0 / self.start if self.start != 0.0 else 0.0
        return [
            f"kinetic   = {self.linear:.3f} J linear + {self.angular:.3f} J angular",
            f"potential = {self.potential:.3f} J",
            f"total     = {self.total:.3f} J ({scale * self.total:.2f}% of start, peak {scale * self.peak:.2f}%)",
        ]


def draw_text_lines(sample, lines, color=WHITE):
    """Status text at the top of the sample's initial view (box2d's DrawScreenTextLine)."""
    cx, cy = sample.camera_center
    zoom = sample.camera_zoom
    for i, line in enumerate(lines):
        sample.debug_draw.draw_string((cx, cy + zoom * (0.9 - 0.08 * i)), line, color)
