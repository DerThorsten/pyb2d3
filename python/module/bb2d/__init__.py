import numpy as np # type: ignore
from ._bb2d import *

# Factory functions
def world_def(**kwargs):
    world = WorldDef()
    for k, v in kwargs.items():
        setattr(world, k, v)
    return world

def body_def(**kwargs):
    body = BodyDef()
    for k, v in kwargs.items():
        setattr(body, k, v)
    return body

def shape_def(**kwargs):
    shape = ShapeDef()
    for k, v in kwargs.items():
        setattr(shape, k, v)
    return shape


def circle(**kwargs):
    c = Circle()
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c




class DebugDraw(DebugDrawBase):
    def __init__(self):
        super().__init__(self)


    def draw_polygon(self, vertices, color):
        pass

    def draw_solid_polygon(self, transform, vertices, radius,  color):
        pass

    def draw_circle(self, center, radius, color):
        pass

    def draw_solid_circle(self, transform, radius, color):
        pass
    
    def draw_solid_capsule(self, p1, p2, radius, color):
        pass

    def draw_segment(self, p1, p2, color):
        pass

    def draw_transform(self, transform):
        pass

    def draw_point(self, p, size, color):
        pass

    def draw_string(self, x, y, string):
        pass

    def draw_aabb(self, aabb, color):
        pass