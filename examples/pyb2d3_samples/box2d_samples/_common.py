"""Shared helpers for the ports of the box2d samples."""

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


class Box2dSample(SampleBase):
    """Base class of the ported box2d samples.

    box2d positions its camera with a center and a zoom (the half height of the
    view in meters); the sandbox frames the sample by its `aabb()`.
    """

    camera_center = (0.0, 0.0)
    camera_zoom = 25.0 * 0.5
    aspect = 1.6

    def aabb(self):
        cx, cy = self.camera_center
        hy = self.camera_zoom
        hx = hy * self.aspect
        return b2d.aabb(lower_bound=(cx - hx, cy - hy), upper_bound=(cx + hx, cy + hy))

    def create_ground_segment(self, x0=-20.0, x1=20.0, y=0.0, name="ground"):
        """The flat ground most samples start with."""
        ground = self.world.create_static_body(name=name)
        ground.create_shape(b2d.shape_def(), b2d.segment((x0, y), (x1, y)))
        return ground
