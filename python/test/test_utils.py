import pytest
import numpy as np
import pyb2d as b2d

class DebugDrawTest(b2d.DebugDraw):

    def __init__(self):
        super().__init__()

    def draw_polygon(self, vertices, color):
        color = hex(color)
        assert isinstance(vertices, np.ndarray)

    def draw_solid_polygon(self, transform, vertices, radius, color):
        color = hex(color)
        assert isinstance(vertices, np.ndarray)
        assert radius >= 0
        assert isinstance(transform, b2d.Transform)

    def draw_circle(self, center, radius, color):
        color = hex(color)
        assert isinstance(center, tuple)
        assert radius >= 0

    def draw_solid_capsule(self, p1, p2, radius, color):
        color = hex(color)
        assert isinstance(p1, tuple)
        assert isinstance(p2, tuple)
        assert radius >= 0

    def draw_solid_circle(self, transform, radius, color):
        color = hex(color)
        assert radius >= 0
        assert isinstance(transform, b2d.Transform)
 
    def draw_segment(self, p1, p2, color):
        color = hex(color)
        assert isinstance(p1, tuple)
        assert isinstance(p2, tuple)

    def draw_transform(self, xf):
        assert isinstance(xf, b2d.Transform)

    def draw_point(self, p, size, color):
        assert isinstance(p, tuple)
        assert size >= 0
        color = hex(color)

    def draw_aabb(self, aabb, color):
        assert isinstance(aabb, tuple)
        color = hex(color)