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


# ---- BatchDebugDraw: the same primitives as the python callbacks, in flat arrays ----


def rgba8(color):
    """0xRRGGBB -> the packed RGBA8 of BatchDebugDraw (r in the lowest byte, alpha 255)"""
    r, g, b = (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF
    return (255 << 24) | (b << 16) | (g << 8) | r


def colors(array):
    """the color column (last) of a BatchDebugDraw array: uint32 bits"""
    return array[:, -1].copy().view(np.uint32).tolist()


def batch_and_callbacks(world, **flags):
    """draw `world` with the python callbacks and with a BatchDebugDraw (same options)"""
    rec = RecordingDraw()
    rec.drawing_bounds = b2d.aabb((-100, -100), (100, 100))
    for k, v in flags.items():
        setattr(rec, k, v)
    world.draw(rec)
    strings = []
    batch = b2d.BatchDebugDraw(on_string=lambda p, s, c: strings.append((p, s, c)))
    batch.copy_options(rec)
    world._draw(batch)
    return rec, batch, strings


def test_batch_debug_draw_matches_callbacks(world, two_bodies):
    box = make_box_body(world, position=(2, 0))
    make_circle_body(world, position=(-2, 0), radius=0.5)
    capsule = world.create_dynamic_body(position=(0, 3), rotation=b2d.make_rot(0.4))
    capsule.create_capsule_shape(b2d.shape_def(), b2d.capsule((0, 0), (1, 0), 0.2))
    hexagon = world.create_dynamic_body(position=(4, 4))
    hexagon.create_shape(b2d.shape_def(), b2d.polygon(points=[(np.cos(a), np.sin(a)) for a in np.arange(6) * np.pi / 3]))
    rounded = world.create_dynamic_body(position=(-4, 4))
    rounded.create_shape(b2d.shape_def(), b2d.box(0.5, 0.3, radius=0.1))
    world.create_revolute_joint(*two_bodies)

    rec, batch, _ = batch_and_callbacks(world, draw_shapes=True, draw_joints=True, draw_bounds=True,
                                        draw_joint_extras=True)
    calls = {kind: [c for c in rec.calls if c[0] == kind] for kind in rec.kinds()}

    # solid circles: center transform, radius, color
    solid_circles = batch.solid_circles
    assert solid_circles.shape == (len(calls["solid_circle"]), 6) and solid_circles.dtype == np.float32
    for row, (_, t, radius, color) in zip(solid_circles, calls["solid_circle"]):
        assert row[:5] == approx([t.p[0], t.p[1], t.q.c, t.q.s, radius], abs=1e-5)
    assert colors(solid_circles) == [rgba8(c[3]) for c in calls["solid_circle"]]

    # capsules: center, axis, radius, length
    (_, p1, p2, radius, color), = calls["solid_capsule"]
    length = float(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))
    assert batch.capsules[0, :6] == approx(
        [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p2[0] - p1[0]) / length, (p2[1] - p1[1]) / length,
         radius, length], abs=1e-5)
    assert colors(batch.capsules) == [rgba8(color)]

    # polygons: transform, padded local points, count (int32 bits), radius, color
    polygons = batch.polygons
    assert polygons.shape == (len(calls["solid_polygon"]), 23)
    for row, (_, t, points, radius, color) in zip(polygons, calls["solid_polygon"]):
        n = len(points)
        assert row[:4] == approx([t.p[0], t.p[1], t.q.c, t.q.s], abs=1e-5)
        assert row[4:4 + 2 * n] == approx(points.ravel(), abs=1e-6)
        assert not row[4 + 2 * n:20].any()
        assert row[20:21].copy().view(np.int32)[0] == n
        assert row[21] == approx(radius)
    assert colors(polygons) == [rgba8(c[4]) for c in calls["solid_polygon"]]
    assert [box.position[0], box.position[1]] in polygons[:, :2].tolist()

    # lines: segments + polygon outlines + bounds (4 edges) + transforms (2 axes), 2 vertices each
    expected_lines = (len(calls.get("segment", [])) + sum(len(c[1]) for c in calls.get("polygon", []))
                      + 4 * len(calls.get("aabb", [])) + 2 * len(calls.get("transform", [])))
    assert expected_lines > 0
    assert batch.lines.shape == (2 * expected_lines, 3)
    assert batch.points.shape == (len(calls.get("point", [])), 4)
    assert batch.circles.shape == (len(calls.get("circle", [])), 4)


def test_batch_debug_draw_clear_options_strings(world, box_body):
    batch = b2d.BatchDebugDraw()  # no string callback: strings are dropped
    batch.drawing_bounds = b2d.aabb((-100, -100), (100, 100))
    batch.draw_shapes = True
    world._draw(batch)
    assert len(batch.polygons) == 1
    world._draw(batch)
    assert len(batch.polygons) == 2  # collects until cleared
    batch.clear()
    assert batch.polygons.shape == (0, 23)
    batch.draw_shapes = False
    world._draw(batch)
    assert len(batch.polygons) == 0

    # options copied from another debug draw; strings (body names) go to the callback
    box_body.name = "crate"
    rec, batch, strings = batch_and_callbacks(world, draw_shapes=False, draw_body_names=True)
    assert batch.draw_body_names and not batch.draw_shapes
    assert [s for _, s, _ in strings] == [c[2] for c in rec.calls if c[0] == "string"] == ["crate"]
