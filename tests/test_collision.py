import math

import numpy as np
import pytest
from pytest import approx

import pyb2d3 as b2d

SQUARE = np.array([(-1, -1), (1, -1), (1, 1), (-1, 1)], dtype=np.float32)
IDENTITY = b2d.Transform()


def test_geometry_constructors():
    c = b2d.Circle((1, 2), 3)
    assert c.center == approx((1, 2)) and c.radius == approx(3)
    cap = b2d.Capsule((0, 0), (1, 0), 0.5)
    assert cap.center2 == approx((1, 0)) and cap.radius == approx(0.5)
    s = b2d.Segment((0, 0), (1, 1))
    assert s.point2 == approx((1, 1))
    cs = b2d.chain_segment(s, (-1, -1), (2, 2))
    assert cs.ghost2 == approx((2, 2))


def test_hull_and_polygon():
    hull = b2d.compute_hull(SQUARE)
    assert hull.count == 4
    assert hull.validate()
    assert b2d.validate_hull(hull)
    assert hull.points.shape == (4, 2)

    poly = b2d.make_polygon(hull, 0.0)
    assert poly.count == 4
    assert poly.vertices.shape == (4, 2)
    assert poly.normals.shape == (4, 2)
    assert poly.centroid == approx((0, 0))

    rounded = b2d.polygon(points=SQUARE, radius=0.1)
    assert rounded.radius == approx(0.1)
    offset = b2d.polygon(points=SQUARE, position=(5, 0), rotation=0.0)
    assert offset.centroid == approx((5, 0))
    offset_rounded = b2d.make_offset_rounded_polygon(hull, (5, 0), 0.0, 0.2)
    assert offset_rounded.radius == approx(0.2)

    moved = b2d.transform_polygon(b2d.transform(p=(1, 1)), poly)
    assert moved.centroid == approx((1, 1))


SQUARE_POINTS = [(-1, -1), (1, -1), (1, 1), (-1, 1)]


@pytest.mark.parametrize(
    "make",
    [
        pytest.param(lambda: SQUARE, id="float32-array"),
        pytest.param(lambda: SQUARE.astype(np.float64), id="float64-array"),
        pytest.param(lambda: np.repeat(SQUARE, 2, axis=0)[::2], id="non-contiguous-array"),
        pytest.param(lambda: SQUARE_POINTS, id="list-of-tuples"),
        pytest.param(lambda: tuple(SQUARE_POINTS), id="tuple-of-tuples"),
        pytest.param(lambda: [list(p) for p in SQUARE_POINTS], id="list-of-lists"),
        pytest.param(lambda: (p for p in SQUARE_POINTS), id="generator"),
        pytest.param(lambda: [b2d.Vec2(*p) for p in SQUARE_POINTS], id="list-of-vec2"),
        pytest.param(lambda: [np.array(p) for p in SQUARE_POINTS], id="list-of-arrays"),
    ],
)
def test_points_accept_any_iterable(make):
    assert b2d.compute_hull(make()).count == 4
    assert b2d.make_proxy(make()).count == 4
    assert b2d.make_aabb(make()).upper_bound == approx((1, 1))
    assert b2d.polygon(points=make()).count == 4
    assert b2d.chain_def(points=make(), is_loop=True).points.shape == (4, 2)
    hull = b2d.Hull()
    hull.points = make()
    assert hull.count == 4
    np.testing.assert_allclose(hull.points, SQUARE)


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(np.zeros((4, 3), dtype=np.float32), id="wrong-shape"),
        pytest.param([(1, 2, 3)], id="triples"),
        pytest.param("abc", id="string"),
        pytest.param(42, id="not-iterable"),
    ],
)
def test_points_reject_bad_input(bad):
    with pytest.raises(TypeError):
        b2d.compute_hull(bad)


def test_points_empty():
    assert b2d.make_proxy([]).count == 0
    assert b2d.compute_hull(np.zeros((0, 2), dtype=np.float32)).count == 0
    with pytest.raises(ValueError):
        b2d.make_aabb([])
    with pytest.raises(ValueError):
        b2d.polygon(points=[(0, 0), (1, 1)])


def test_polygon_vertices_are_writable_with_same_count():
    poly = b2d.make_polygon(b2d.compute_hull(SQUARE), 0.0)
    poly.vertices = 2.0 * poly.vertices  # scale in place, normals stay valid
    assert poly.vertices.max() == approx(2.0 * np.max(SQUARE))
    with pytest.raises(ValueError):
        poly.vertices = poly.vertices[:3]


def test_hull_points_are_bounds_checked():
    hull = b2d.Hull()
    hull.points = SQUARE
    assert hull.count == 4
    with pytest.raises(ValueError):
        hull.points = np.zeros((b2d.MAX_POLYGON_VERTICES + 1, 2), dtype=np.float32)


def test_box_factories():
    assert b2d.make_square(1).count == 4
    box = b2d.box(1, 2)
    assert box.vertices[:, 0].max() == approx(1)
    assert box.vertices[:, 1].max() == approx(2)
    assert b2d.box(1, 1, radius=0.1).radius == approx(0.1)
    assert b2d.box(1, 1, center=(3, 0)).centroid == approx((3, 0))
    assert b2d.box(1, 1, center=(3, 0), rotation=0.5, radius=0.1).radius == approx(0.1)
    assert b2d.make_rounded_box(1, 1, 0.2).radius == approx(0.2)
    assert b2d.make_offset_box(1, 1, (1, 1), 0.0).centroid == approx((1, 1))
    assert b2d.make_offset_rounded_box(1, 1, (1, 1), 0.0, 0.3).radius == approx(0.3)


def test_mass_and_bounds():
    circle = b2d.circle(radius=1)
    assert b2d.compute_circle_mass(circle, 1).mass == approx(math.pi, rel=1e-5)
    capsule = b2d.capsule((0, 0), (2, 0), 1)
    assert b2d.compute_capsule_mass(capsule, 1).mass == approx(math.pi + 4, rel=1e-5)
    assert b2d.compute_polygon_mass(b2d.box(1, 1), 2).mass == approx(8)

    t = b2d.transform(p=(10, 0))
    assert b2d.compute_circle_bounds(circle, t).lower_bound == approx((9, -1))
    assert b2d.compute_capsule_bounds(capsule, t).upper_bound == approx((13, 1))
    assert b2d.compute_polygon_bounds(b2d.box(1, 1), t).upper_bound == approx((11, 1))
    assert b2d.compute_segment_bounds(b2d.segment((0, 0), (1, 2)), t).upper_bound == approx((11, 2))


def test_point_tests():
    assert b2d.point_in_circle(b2d.circle(radius=1), (0.5, 0))
    assert not b2d.point_in_circle(b2d.circle(radius=1), (2, 0))
    assert b2d.point_in_capsule(b2d.capsule((0, 0), (2, 0), 0.5), (1, 0.4))
    assert b2d.point_in_polygon(b2d.box(1, 1), (0.9, 0.9))


def test_ray_casts():
    ray = b2d.ray_cast_input(origin=(-5, 0), translation=(10, 0))
    assert b2d.is_valid_ray(ray)
    out = b2d.cast_ray_circle(b2d.circle(radius=1), ray)
    assert out.hit and out.point == approx((-1, 0), abs=1e-5) and out.fraction == approx(0.4)
    assert b2d.cast_ray_capsule(b2d.capsule((0, -1), (0, 1), 0.5), ray).hit
    assert b2d.cast_ray_polygon(b2d.box(1, 1), ray).hit
    seg = b2d.segment((0, -1), (0, 1))
    assert b2d.cast_ray_segment(seg, ray).hit
    assert not b2d.cast_ray_circle(b2d.circle(center=(0, 5), radius=1), ray).hit


def test_shape_casts():
    proxy = b2d.make_proxy(np.array([(0, 0)], dtype=np.float32), radius=0.5)
    inp = b2d.ShapeCastInput()
    inp.proxy = b2d.make_offset_proxy(np.array([(0, 0)], dtype=np.float32), 0.5, (-5, 0), 0.0)
    inp.translation = (10, 0)
    inp.max_fraction = 1.0
    assert proxy.count == 1
    for fn, shape in [
        (b2d.cast_shape_circle, b2d.circle(radius=1)),
        (b2d.cast_shape_capsule, b2d.capsule((0, -1), (0, 1), 0.5)),
        (b2d.cast_shape_segment, b2d.segment((0, -1), (0, 1))),
        (b2d.cast_shape_polygon, b2d.box(1, 1)),
    ]:
        out = fn(shape, inp)
        assert out.hit, fn.__name__
        assert 0 < out.fraction < 1


def test_pair_cast_and_distance():
    square = b2d.make_proxy(SQUARE, 0.0)

    pair = b2d.ShapeCastPairInput()
    pair.proxy_a = square
    pair.proxy_b = square
    pair.transform = b2d.transform(p=(5, 0))
    pair.translation_b = (-10, 0)
    pair.max_fraction = 1.0
    out = b2d.cast_shape(pair)
    assert out.hit and out.fraction == approx(0.3, abs=1e-3)

    din = b2d.DistanceInput()
    din.proxy_a = square
    din.proxy_b = square
    din.transform = b2d.transform(p=(5, 0))
    din.use_radii = True
    cache = b2d.SimplexCache()
    result, simplexes = b2d.compute_shape_distance(din, cache, simplex_capacity=4)
    assert result.distance == approx(3)
    assert len(simplexes) == min(result.simplex_count, 4)
    assert cache.count > 0

    seg = b2d.compute_segment_distance((0, 0), (1, 0), (0, 1), (1, 1))
    assert seg.distance_squared == approx(1)


def test_time_of_impact():
    square = b2d.make_proxy(SQUARE * 0.5, 0.0)
    sweep_a = b2d.Sweep()
    sweep_a.c1 = sweep_a.c2 = (0, 0)
    sweep_a.q1 = sweep_a.q2 = b2d.Rot(0)
    sweep_b = b2d.Sweep()
    sweep_b.c1 = (5, 0)
    sweep_b.c2 = (-5, 0)
    sweep_b.q1 = sweep_b.q2 = b2d.Rot(0)
    assert b2d.get_sweep_transform(sweep_b, 0.5).p == approx((0, 0))

    toi = b2d.TOIInput()
    toi.proxy_a = square
    toi.proxy_b = square
    toi.sweep_a = sweep_a
    toi.sweep_b = sweep_b
    toi.max_fraction = 1.0
    out = b2d.compute_time_of_impact(toi)
    assert out.state == b2d.TOIState.HIT
    assert out.fraction == approx(0.4, abs=1e-2)


SEGMENT = b2d.segment((-1, 0), (1, 0))


# shape B sits at (0, offset) relative to shape A; segments have no thickness
@pytest.mark.parametrize(
    "fn, a, b, offset",
    [
        (b2d.collide_circles, b2d.circle(radius=1), b2d.circle(radius=1), 1.5),
        (b2d.collide_capsule_and_circle, b2d.capsule((0, 0), (1, 0), 1), b2d.circle(radius=1), 1.5),
        (b2d.collide_segment_and_circle, SEGMENT, b2d.circle(radius=1), 0.5),
        (b2d.collide_polygon_and_circle, b2d.box(1, 1), b2d.circle(radius=1), 1.5),
        (b2d.collide_capsules, b2d.capsule((0, 0), (1, 0), 1), b2d.capsule((0, 0), (1, 0), 1), 1.5),
        (b2d.collide_segment_and_capsule, SEGMENT, b2d.capsule((0, 0), (1, 0), 1), 0.5),
        (b2d.collide_polygon_and_capsule, b2d.box(1, 1), b2d.capsule((0, 0), (1, 0), 1), 1.5),
        (b2d.collide_polygons, b2d.box(1, 1), b2d.box(1, 1), 1.5),
        (b2d.collide_segment_and_polygon, SEGMENT, b2d.box(1, 1), 0.5),
    ],
)
def test_manifolds(fn, a, b, offset):
    manifold = fn(a, b, b2d.transform(p=(0, offset)))
    assert isinstance(manifold, b2d.LocalManifold)
    assert manifold.point_count >= 1
    assert len(manifold.points) == manifold.point_count
    assert manifold.points[0].separation < 0


def test_chain_segment_manifolds():
    # chain segments are one-sided (they collide on the right side): right to left = normal up
    cs = b2d.chain_segment(b2d.segment((1, 0), (-1, 0)), (2, 0), (-2, 0))
    xf = b2d.transform(p=(0, 0.5))
    assert b2d.collide_chain_segment_and_circle(cs, b2d.circle(radius=1), xf).point_count >= 1
    assert b2d.collide_chain_segment_and_capsule(cs, b2d.capsule((0, 0), (1, 0), 1), xf).point_count >= 1
    assert b2d.collide_chain_segment_and_polygon(cs, b2d.box(1, 1), xf, cache=b2d.SimplexCache()).point_count >= 1
