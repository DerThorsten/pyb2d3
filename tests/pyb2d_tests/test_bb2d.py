import pytest
from pytest import approx

import numpy as np
import pyb2d as b2d

from .test_utils import DebugDrawTest

from .conftest import *  # noqa


def test_world_cls():
    world = b2d.World(gravity=(0, -10), user_data=42)
    assert world.gravity == approx((0, -10))
    assert world.user_data == 42

    body = world.create_dynamic_body(position=(0, 0), user_data=100)
    assert body.user_data == 100
    body = world.create_static_body(position=(0, -10), user_data=200)
    assert body.user_data == 200
    body = world.create_kinematic_body(position=(0, 10), user_data=300)
    assert body.user_data == 300

    body_def = b2d.body_def(position=(0, 0))
    body_def.user_data = 100

    body = world.create_body(body_def)
    assert body.user_data == 100

    material = b2d.surface_material(friction=0.5, restitution=0.3)
    shape_def = b2d.shape_def(density=1, material=material, user_data=400)

    shapes = [b2d.make_box(1, 1), b2d.make_circle(radius=0.5)]

    for i in range(10):
        body = world.create_body(body_def)
        for shape in shapes:
            shape_id = body.create_shape(shape_def, shape)
            # assert shape_id.user_data == 400

    hl_shapes = body.create_shapes(shape_def, shapes)


def test_body_builder():
    world = b2d.World(gravity=(0, -10))

    factory = world.body_factory()
    factory.dynamic().shape(density=1).surface_material(restitution=1)
    factory.add_circle(radius=1).add_box(1, 1).is_bullet(True)
    for i in range(10):
        body = factory.position((i, 0)).user_data(i)()
        assert body.user_data == i
        assert body.position == approx((i, 0))
        assert body.shape_count == 2
        shapes = body.shapes

        for shape in shapes:
            if isinstance(shape, b2d.CircleShape):
                circle = shape.circle
                assert circle.radius == approx(1)
            elif isinstance(shape, b2d.PolygonShape):
                polygon = shape.polygon


def test_threadpool():
    pool = b2d.ThreadPool()
    world = b2d.World(gravity=(0, -10), thread_pool=pool)

    factory = world.body_factory()
    factory.dynamic().shape(density=1).surface_material(restitution=1)
    factory.add_circle(radius=1).add_box(1, 1)
    for i in range(1000):
        rx = i % 10
        ry = i + 1 % 10
        body = factory.position((rx, ry))()

    world.step(1 / 60, 4)
