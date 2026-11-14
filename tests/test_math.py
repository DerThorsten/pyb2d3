import math

import numpy as np
import pytest
from pytest import approx

import pyb2d3 as b2d


def test_vec2():
    v = b2d.Vec2(3, 4)
    assert (v.x, v.y) == (3, 4)
    assert len(v) == 2 and v[0] == 3 and v[-1] == 4
    v[1] = 5
    assert v.y == 5
    with pytest.raises(IndexError):
        v[2]
    assert b2d.Vec2((1, 2)) == b2d.Vec2(1, 2)
    assert b2d.Vec2(np.array([1, 2], dtype=np.float64)) == (1, 2)
    assert b2d.Vec2(3, 4).length() == approx(5)
    assert b2d.Vec2(3, 4).length_squared() == approx(25)
    assert b2d.Vec2(3, 4).normalize() == approx((0.6, 0.8))
    assert tuple(b2d.Vec2(1, 2) + b2d.Vec2(3, 4)) == (4, 6)
    assert tuple(b2d.Vec2(1, 2) - b2d.Vec2(3, 4)) == (-2, -2)
    assert tuple(-b2d.Vec2(1, 2)) == (-1, -2)
    assert tuple(b2d.Vec2(1, 2) * 2) == (2, 4)
    assert tuple(2 * b2d.Vec2(1, 2)) == (2, 4)
    assert tuple(b2d.Vec2(2, 4) / 2) == (1, 2)
    assert tuple(b2d.Vec2(3, 5) // 2) == (1, 2)
    assert tuple(math.floor(b2d.Vec2(1.5, 2.5))) == (1, 2)
    assert tuple(math.ceil(b2d.Vec2(1.5, 2.5))) == (2, 3)
    w = b2d.Vec2(1, 1)
    w += (1, 2)
    w -= 1
    w *= 2
    w /= 2
    assert tuple(w) == (1, 2)
    assert "Vec2" in repr(w)


def test_rot_and_transform():
    q = b2d.Rot(math.pi / 2)
    assert q.angle == approx(math.pi / 2, abs=2e-3)
    assert q.x_axis == approx((0, 1), abs=2e-3)
    assert q.y_axis == approx((-1, 0), abs=2e-3)
    assert q.inverse().angle == approx(-q.angle)

    t = b2d.Transform((1, 2), 0.0)
    assert t.transform_point((1, 0)) == approx((2, 2))
    assert t.inv_transform_point((2, 2)) == approx((1, 0))
    assert b2d.transform(p=(1, 0)).p == approx((1, 0))
    assert "Transform" in repr(t)

    m = b2d.Mat22((2, 0), (0, 4))
    assert b2d.mul_mv(m, (1, 1)) == approx((2, 4))
    assert b2d.solve22(m, (2, 4)) == approx((1, 1))
    assert b2d.get_inverse22(m).cx == approx((0.5, 0))


def test_aabb():
    a = b2d.aabb((0, 0), (2, 2))
    b = b2d.aabb((1, 1), (3, 3))
    assert a.center() == approx((1, 1))
    assert a.extents() == approx((1, 1))
    assert a.overlaps(b)
    assert not a.contains(b)
    assert a.union(b).upper_bound == approx((3, 3))
    assert a.is_valid()
    assert b2d.aabb_arround_point((1, 1), 1).upper_bound == approx((2, 2))
    assert b2d.make_aabb(np.array([(0, 0), (2, 3)], dtype=np.float32)).upper_bound == approx((2, 3))


@pytest.mark.parametrize(
    "expr, expected",
    [
        (lambda: b2d.dot((1, 2), (3, 4)), 11),
        (lambda: b2d.cross((1, 0), (0, 1)), 1),
        (lambda: b2d.cross_vs((1, 0), 1), (0, -1)),
        (lambda: b2d.cross_sv(1, (1, 0)), (0, 1)),
        (lambda: b2d.left_perp((1, 0)), (0, 1)),
        (lambda: b2d.right_perp((1, 0)), (0, -1)),
        (lambda: b2d.add((1, 2), (3, 4)), (4, 6)),
        (lambda: b2d.sub((1, 2), (3, 4)), (-2, -2)),
        (lambda: b2d.neg((1, 2)), (-1, -2)),
        (lambda: b2d.lerp((0, 0), (2, 2), 0.5), (1, 1)),
        (lambda: b2d.mul((1, 2), (3, 4)), (3, 8)),
        (lambda: b2d.mul_sv(2, (1, 2)), (2, 4)),
        (lambda: b2d.mul_add((1, 1), 2, (1, 2)), (3, 5)),
        (lambda: b2d.mul_sub((1, 1), 2, (1, 2)), (-1, -3)),
        (lambda: b2d.abs((-1, 2)), (1, 2)),
        (lambda: b2d.min((1, 4), (3, 2)), (1, 2)),
        (lambda: b2d.max((1, 4), (3, 2)), (3, 4)),
        (lambda: b2d.clamp((5, -5), (0, 0), (1, 1)), (1, 0)),
        (lambda: b2d.length((3, 4)), 5),
        (lambda: b2d.length_squared((3, 4)), 25),
        (lambda: b2d.distance((0, 0), (3, 4)), 5),
        (lambda: b2d.distance_squared((0, 0), (3, 4)), 25),
        (lambda: b2d.normalize((0, 2)), (0, 1)),
        (lambda: b2d.mid_point((0, 0), (2, 4)), (1, 2)),
        (lambda: b2d.rotate_vector(b2d.Rot(0), (1, 0)), (1, 0)),
        (lambda: b2d.inv_rotate_vector(b2d.Rot(0), (1, 0)), (1, 0)),
        (lambda: b2d.transform_point(b2d.transform(p=(1, 1)), (1, 0)), (2, 1)),
        (lambda: b2d.inv_transform_point(b2d.transform(p=(1, 1)), (2, 1)), (1, 0)),
        (lambda: b2d.atan2(1, 1), math.pi / 4),
        (lambda: b2d.unwind_angle(3 * math.pi), math.pi),
        (lambda: b2d.plane_separation(_plane((0, 1), 1), (0, 3)), 2),
    ],
)
def test_functions(expr, expected):
    result = expr()
    if isinstance(expected, tuple):
        assert tuple(result) == approx(expected, abs=1e-4)
    else:
        assert result == approx(expected, abs=1e-4)


def _plane(normal, offset):
    p = b2d.Plane()
    p.normal = normal
    p.offset = offset
    return p


def test_rotation_functions():
    q = b2d.make_rot(0.5)
    assert b2d.rot_get_angle(q) == approx(0.5, abs=2e-3)
    assert b2d.is_normalized_rot(q)
    assert b2d.normalize_rot(q).c == approx(q.c)
    assert b2d.invert_rot(q).s == approx(-q.s)
    assert b2d.mul_rot(q, b2d.invert_rot(q)).angle == approx(0, abs=1e-5)
    assert b2d.inv_mul_rot(q, q).angle == approx(0, abs=1e-5)
    # angle of the second rotation relative to the first
    assert b2d.relative_angle(b2d.Rot(0), q) == approx(0.5, abs=2e-3)
    assert b2d.nlerp(b2d.Rot(0), q, 1.0).angle == approx(q.angle, abs=1e-5)
    assert b2d.integrate_rotation(b2d.Rot(0), 0.1).angle == approx(0.1, abs=1e-2)
    # small angle approximation: sin(delta) * inv_h (exact rotation, make_rot itself approximates cos/sin)
    small = b2d.Rot()
    small.c, small.s = math.cos(0.01), math.sin(0.01)
    assert b2d.compute_angular_velocity(b2d.Rot(0), small, 60) == approx(0.6, rel=1e-3)
    assert b2d.make_rot_from_unit_vector((0, 1)).angle == approx(math.pi / 2)
    assert b2d.compute_rotation_between_unit_vectors((1, 0), (0, 1)).angle == approx(math.pi / 2, abs=1e-4)
    cs = b2d.compute_cos_sin(0.0)
    assert (cs.cosine, cs.sine) == approx((1, 0))
    length, n = b2d.get_length_and_normalize((0, 3))
    assert length == approx(3) and n == approx((0, 1))
    assert b2d.is_normalized((1, 0))
    t = b2d.mul_transforms(b2d.transform(p=(1, 0)), b2d.transform(p=(1, 0)))
    assert t.p == approx((2, 0))
    assert b2d.inv_mul_transforms(t, t).p == approx((0, 0))
    assert b2d.spring_damper(5, 1, 1.0, 0.0, 1 / 60) < 0


def test_validation():
    assert b2d.is_valid_float(1.0)
    assert not b2d.is_valid_float(float("nan"))
    assert b2d.is_valid_vec2((1, 2))
    assert b2d.is_valid_rot(b2d.Rot(0))
    assert b2d.is_valid_transform(b2d.Transform())
    assert b2d.is_valid_aabb(b2d.aabb((0, 0), (1, 1)))
    assert b2d.is_valid_plane(_plane((0, 1), 0))


def test_base():
    version = b2d.get_version()
    assert (version.major, version.minor) >= (3, 2)
    assert repr(version).startswith(f"{version.major}.{version.minor}")
    assert b2d.is_double_precision() is False
    assert isinstance(b2d.is_avx2_available(), bool)
    assert b2d.get_byte_count() >= 0
    ticks = b2d.get_ticks()
    assert b2d.get_milliseconds(ticks) >= 0
    b2d.yield_thread()
    assert b2d.get_graph_color(0) != b2d.get_graph_color(1)
    assert b2d.MAX_POLYGON_VERTICES == 8
    assert b2d.DEFAULT_MASK_BITS == 2**64 - 1


def test_length_units():
    old = b2d.get_length_units_per_meter()
    try:
        b2d.set_length_units_per_meter(100.0)
        assert b2d.get_length_units_per_meter() == approx(100)
    finally:
        b2d.set_length_units_per_meter(old)


def test_log_callback():
    b2d.set_log_callback(lambda message: None)
    b2d.set_log_callback(None)
