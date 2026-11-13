"""Ports of box2d's samples/sample_geometry.cpp."""

import math

import numpy as np
import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample

from ._collision_helpers import colors
from ._common import Box2dSample


@register_sample("Geometry", "Convex Hull")
class ConvexHull(Box2dSample):
    """Stress test of b2ComputeHull. Keys: generate (g), auto (a), bulk defect hunting (b)."""

    camera_center = (0.5, 0.0)
    camera_zoom = 25.0 * 0.3

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.rng = np.random.default_rng()
        self.generation = 0
        self.auto = False
        self.bulk = False
        self.generate()
        self.hull = b2d.compute_hull(self.points)
        self.valid = self.hull.validate()

    def generate(self):
        angle = math.pi * self.rng.uniform(-1.0, 1.0)
        c, s = math.cos(angle), math.sin(angle)
        # clamp onto a square to help create collinearities, this stresses the hull algorithm
        v = np.clip(10.0 * self.rng.uniform(-1.0, 1.0, (b2d.MAX_POLYGON_VERTICES, 2)), -4.0, 4.0)
        self.points = (v @ np.array([[c, s], [-s, c]])).astype(np.float32)
        self.generation += 1

    def on_key_down(self, event):
        if event.key == "a":
            self.auto = not self.auto
        elif event.key == "b":
            self.bulk = not self.bulk
        elif event.key == "g":
            self.generate()

    def post_update(self, dt):
        self.valid = False
        if self.bulk:
            # defect hunting
            for _ in range(10000):
                self.generate()
                self.hull = b2d.compute_hull(self.points)
                if self.hull.count == 0:
                    continue
                self.valid = self.hull.validate()
                if not self.valid:
                    self.bulk = False
                    break
        else:
            if self.auto:
                self.generate()
            self.hull = b2d.compute_hull(self.points)
            if self.hull.count > 0:
                self.valid = self.hull.validate()
                if not self.valid:
                    self.auto = False

    def post_debug_draw(self):
        dd = self.debug_draw
        hull_points = self.hull.points
        if len(hull_points) > 0:
            dd.draw_polygon(hull_points, colors.Gray)

        for i, p in enumerate(self.points):
            dd.draw_point(p, 5.0, colors.Blue)
            dd.draw_string(p + 0.1, str(i), colors.White)

        for p in hull_points:
            dd.draw_point(p, 6.0, colors.Green)
