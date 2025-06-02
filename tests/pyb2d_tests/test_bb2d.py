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


# def test_hello_world(world_id):

#     # create static ground body
#     body_def = b2d.body_def(position=(0, -10), type=b2d.BodyType.STATIC, user_data=10)
#     assert body_def.user_data == 10
#     groud_body_id = b2d.create_body(world_id, body_def)
#     body_user_data = b2d.body_get_user_data(groud_body_id)
#     assert body_user_data == 10
#     box = b2d.make_box(1, 1)

#     # surface material
#     surface_material = b2d.surface_material(
#         friction=0.3, restitution=0.5, rolling_resistance=0.3
#     )

#     # shape definition
#     shape_def = b2d.shape_def(density=0, material=surface_material, user_data=100)
#     shape_id = b2d.create_polygon_shape(groud_body_id, shape_def, box)
#     shape_user_data = b2d.shape_get_user_data(shape_id)
#     assert shape_user_data == 100

#     # create dynamic body
#     body_def = b2d.body_def(
#         position=(0, 4),
#         type=b2d.BodyType.DYNAMIC,
#         angular_damping=0.1,
#         linear_damping=0.1,
#         fixed_rotation=False,
#     )
#     dynamic_body_id = b2d.create_body(world_id, body_def)
#     circle = b2d.circle(radius=0.5)
#     surface_material = b2d.surface_material(friction=0.3, restitution=0.5)
#     shape_def = b2d.shape_def(density=1, material=surface_material, user_data=0)
#     shape_id = b2d.create_circle_shape(dynamic_body_id, shape_def, circle)

#     body_user_data = b2d.body_get_user_data(dynamic_body_id)
#     assert body_user_data == 0

#     # create debug draw
#     debug_draw = DebugDrawTest()
#     debug_draw.draw_shapes = True
#     debug_draw.draw_joints = True
#     debug_draw.draw_joint_extras = True

#     # simulate
#     pos_inital = b2d.body_get_position(dynamic_body_id)
#     for i in range(60):
#         b2d.world_step(world_id, 1 / 60, 6)
#         pos = b2d.body_get_position(dynamic_body_id)
#         b2d.world_draw(world_id, debug_draw)

#     assert pos[1] < pos_inital[1]
