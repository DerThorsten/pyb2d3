import numpy as np
from pytest import approx

import pyb2d3 as b2d

from .conftest import make_box_body, make_circle_body


class RecordingDraw(b2d.DebugDraw):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.began = self.ended = 0

    def begin_draw(self):
        self.began += 1

    def end_draw(self):
        self.ended += 1

    def draw_polygon(self, points, color):
        self.calls.append(("polygon", points, color))

    def draw_solid_polygon(self, transform, points, radius, color):
        self.calls.append(("solid_polygon", transform, points, radius, color))

    def draw_circle(self, center, radius, color):
        self.calls.append(("circle", center, radius, color))

    def draw_solid_circle(self, transform, radius, color):
        self.calls.append(("solid_circle", transform, radius, color))

    def draw_solid_capsule(self, p1, p2, radius, color):
        self.calls.append(("solid_capsule", p1, p2, radius, color))

    def draw_segment(self, p1, p2, color):
        self.calls.append(("segment", p1, p2, color))

    def draw_transform(self, transform):
        self.calls.append(("transform", transform))

    def draw_point(self, p, size, color):
        self.calls.append(("point", p, size, color))

    def draw_string(self, p, string, color):
        self.calls.append(("string", p, string, color))

    def draw_aabb(self, aabb, color):
        self.calls.append(("aabb", aabb, color))

    def kinds(self):
        return {c[0] for c in self.calls}


def draw(world, **flags):
    dd = RecordingDraw()
    dd.drawing_bounds = b2d.aabb((-100, -100), (100, 100))
    for k, v in flags.items():
        setattr(dd, k, v)
    world.draw(dd)
    return dd


def test_flags():
    dd = RecordingDraw()
    for flag in [
        "draw_shapes",
        "draw_joints",
        "draw_joint_extras",
        "draw_anchor_a",
        "draw_chain_normals",
        "draw_bounds",
        "draw_mass",
        "draw_body_names",
        "draw_contacts",
        "draw_graph_colors",
        "draw_contact_features",
        "draw_contact_normals",
        "draw_contact_forces",
        "draw_friction_forces",
        "draw_islands",
    ]:
        setattr(dd, flag, True)
        assert getattr(dd, flag) is True, flag
    dd.force_scale = 2
    dd.joint_scale = 3
    assert (dd.force_scale, dd.joint_scale) == approx((2, 3))


def test_draw_shapes(world):
    box = make_box_body(world, position=(2, 0))
    make_circle_body(world, position=(-2, 0), radius=0.5)
    capsule_body = world.create_dynamic_body(position=(0, 3))
    capsule_body.create_capsule_shape(b2d.shape_def(), b2d.capsule((0, 0), (1, 0), 0.2))

    dd = draw(world, draw_shapes=True)
    assert dd.began == 1 and dd.ended == 1
    assert {"solid_polygon", "solid_circle", "solid_capsule"} <= dd.kinds()

    _, transform, points, radius, color = next(c for c in dd.calls if c[0] == "solid_polygon")
    assert points.shape == (4, 2) and points.dtype == np.float32
    assert transform.p == approx(tuple(box.position))
    assert isinstance(color, int)

    # solid circles get a transform at the circle center (world coordinates)
    _, transform, radius, _ = next(c for c in dd.calls if c[0] == "solid_circle")
    assert transform.p == approx((-2, 0))
    assert radius == approx(0.5)


def test_draw_bounds_and_joints(world, two_bodies):
    world.create_revolute_joint(*two_bodies)
    dd = draw(world, draw_shapes=False, draw_bounds=True, draw_joints=True)
    assert "aabb" in dd.kinds()
    assert "segment" in dd.kinds() or "point" in dd.kinds()


def test_draw_without_begin_end(world, box_body):
    dd = RecordingDraw()
    dd.drawing_bounds = b2d.aabb((-100, -100), (100, 100))
    world.draw(dd, call_begin_end=False)
    assert dd.began == 0 and dd.calls
