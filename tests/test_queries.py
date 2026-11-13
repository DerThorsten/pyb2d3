import sys

import numpy as np
import pytest
from pytest import approx

import pyb2d3 as b2d

from .conftest import make_box_body, make_circle_body, step


@pytest.fixture
def row(world):
    """five static boxes along the x axis at x = 0, 2, 4, 6, 8"""
    return [make_box_body(world, position=(2 * i, 0), body_type=b2d.BodyType.STATIC) for i in range(5)]


def test_overlap_aabb(world, row):
    found = []
    world.overlap_aabb(b2d.aabb((-1, -1), (5, 1)), lambda shape: found.append(shape.body))
    assert set(found) == set(row[:3])

    # returning False stops the query
    found = []

    def stop_after_first(shape):
        found.append(shape)
        return b2d.STOP_QUERY

    world.overlap_aabb(b2d.aabb((-1, -1), (9, 1)), stop_after_first)
    assert len(found) == 1

    # the query filter is honored
    found = []
    world.overlap_aabb(b2d.aabb((-1, -1), (9, 1)), found.append, query_filter=b2d.make_query_filter(mask_bits=0))
    assert found == []


def test_overlap_aabb_with_origin(world, row):
    found = []
    # the box is relative to the origin
    world.overlap_aabb(b2d.aabb((-0.5, -0.5), (0.5, 0.5)), found.append, origin=(8, 0))
    assert [s.body for s in found] == [row[4]]


def test_callback_exception_propagates(world, row):
    def boom(shape):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        world.overlap_aabb(b2d.aabb((-1, -1), (9, 1)), boom)
    with pytest.raises(RuntimeError, match="boom"):
        world.cast_ray((-5, 0), (20, 0), lambda *args: boom(None))


def test_cast_ray(world, row):
    hits = []

    def callback(shape, point, normal, fraction):
        hits.append((shape.body, tuple(point), tuple(normal), fraction))
        return fraction  # clip: keep the closest

    world.cast_ray((-5, 0), (20, 0), callback)
    assert hits
    closest = min(hits, key=lambda h: h[3])
    assert closest[0] == row[0]
    assert closest[1] == approx((-0.5, 0), abs=1e-4)
    assert closest[2] == approx((-1, 0), abs=1e-4)

    result = world.cast_ray_closest((-5, 0), (20, 0))
    assert isinstance(result, b2d.RayResult)
    assert result.hit
    assert result.shape.body == row[0]
    assert result.point == approx((-0.5, 0), abs=1e-4)
    assert result.fraction == approx(4.5 / 20, abs=1e-4)

    miss = world.cast_ray_closest((-5, 10), (20, 0))
    assert not miss.hit


def test_overlap_and_cast_shape(world, row):
    proxy = b2d.make_proxy(np.array([(-0.25, -0.25), (0.25, -0.25), (0.25, 0.25), (-0.25, 0.25)]), radius=0.0)
    found = []
    world.overlap_shape(proxy, found.append, origin=(4, 0))
    assert [s.body for s in found] == [row[2]]

    hits = []
    world.cast_shape(proxy, (20, 0), lambda shape, p, n, f: hits.append(shape) or f, origin=(-5, 0))
    assert hits


def test_movers(world, row):
    mover = b2d.capsule((0, 0), (0, 1), 0.25)
    fraction = world.cast_mover(mover, (0, -5), origin=(0, 2))
    assert 0 < fraction < 1

    # shallow overlap with the top of the box at x=0 (box2d ignores deep overlaps)
    planes = []
    world.collide_mover(mover, lambda shape, plane: planes.append(plane), origin=(0, 0.7))
    assert planes and all(isinstance(p, b2d.PlaneResult) for p in planes)
    assert planes[0].plane.normal == approx((0, 1), abs=1e-3)

    collision_planes = [b2d.CollisionPlane(p.plane) for p in planes]
    result, updated = b2d.solve_planes((0, -1), collision_planes)
    assert isinstance(result, b2d.PlaneSolverResult)
    assert len(updated) == len(collision_planes)
    # only planes with a push (as computed by solve_planes) clip
    assert b2d.clip_vector((0, -1), updated)[1] == approx(0, abs=1e-5)


def test_shape_and_body_at_point(world, row):
    dynamic = make_circle_body(world, position=(0, 0))
    shape = world.shape_at_point((4, 0))
    assert shape.body == row[2]
    assert world.body_at_point((4, 0)) == row[2]
    assert world.body_at_point((100, 100)) is None
    assert world.body_at_point((0, 0), dynamic_only=True) == dynamic
    assert world.dynamic_body_at_point((0, 0)) == dynamic
    assert world.dynamic_body_at_point((4, 0)) is None


def test_query_with_chains(world):
    ground = world.create_static_body()
    ground.create_chain(b2d.chain_def(points=np.array([(-100, 1.0), (100, 0.0), (-100, 0.0), (-100, 0.1)]), is_loop=True))
    found = []
    world.overlap_aabb(b2d.aabb_arround_point((0, 0), 10), found.append)
    assert all(isinstance(s, b2d.ChainSegmentShape) for s in found)
    assert found


def test_custom_filter_callback(world, ground):
    seen = []

    def no_collisions_with_ground(shape_a, shape_b):
        seen.append((shape_a, shape_b))
        return ground not in (shape_a.body, shape_b.body)

    world.set_custom_filter_callback(no_collisions_with_ground)
    body = world.create_dynamic_body(position=(0, 2))
    body.create_polygon_shape(b2d.shape_def(enable_custom_filtering=True), b2d.box(0.5, 0.5))
    step(world, 60)
    assert seen
    assert body.position[1] < -1  # fell through the ground

    world.set_custom_filter_callback(None)


def test_pre_solve_callback(world, ground):
    calls = []

    def pre_solve(shape_a, shape_b, manifold):
        calls.append(manifold.point_count)

    world.set_pre_solve_callback(pre_solve=pre_solve)
    body = world.create_dynamic_body(position=(0, 1))
    body.create_polygon_shape(b2d.shape_def(enable_pre_solve_events=True), b2d.box(0.5, 0.5))
    step(world, 60)
    assert calls
    world.set_pre_solve_callback()


def test_friction_and_restitution_callbacks(world, ground):
    calls = []

    def friction(fa, ma, fb, mb):
        calls.append((ma, mb))
        return 0.0

    world.set_friction_callback(friction)
    world.set_restitution_callback(lambda ra, ma, rb, mb: 0.0)
    body = make_box_body(world, position=(0, 0.5))
    body.linear_velocity = (5, 0)
    step(world, 30)
    assert calls
    assert body.linear_velocity[0] == approx(5, abs=0.1)  # frictionless
    world.set_friction_callback(None)
    world.set_restitution_callback(None)


def test_mixing_callbacks_cleared_by_other_world(world, ground):
    # the python callback slot is global but box2d installs the callback per world
    world.set_friction_callback(lambda fa, ma, fb, mb: 0.0)
    world.set_restitution_callback(lambda ra, ma, rb, mb: 0.0)
    other = b2d.World(gravity=(0, -10))
    other.set_friction_callback(None)
    other.set_restitution_callback(None)

    make_box_body(world, position=(0, 0.5))
    step(world, 10)  # must fall back to the default mixing, not crash
    world.set_friction_callback(None)
    world.set_restitution_callback(None)


def test_callback_exception_in_step_is_reported(world, ground, monkeypatch):
    def broken(shape_a, shape_b):
        raise ValueError("broken")

    # the exception is reported as "unraisable" (box2d cannot propagate it) and stepping continues
    # only keep the exception type: keeping the exception would keep its traceback
    # (and the shapes in its frames) alive in a cycle until interpreter shutdown
    reported = []
    monkeypatch.setattr(sys, "unraisablehook", lambda args: reported.append(type(args.exc_value)))

    world.set_custom_filter_callback(broken)
    body = world.create_dynamic_body(position=(0, 0.5))
    body.create_polygon_shape(b2d.shape_def(enable_custom_filtering=True), b2d.box(0.5, 0.5))
    step(world, 5)
    world.set_custom_filter_callback(None)

    assert reported
    assert reported[0] is ValueError
