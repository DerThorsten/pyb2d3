import pytest

import bb2d as b2d


def test_world():
    world_def = b2d.WorldDef()
    world_def.gravity = (0, -10)
    world = b2d.create_world(world_def)

    assert world is not None


def test_hello_world():

    world_def = b2d.WorldDef()
    world_def.gravity = (0, -10)
    world = b2d.create_world(world_def)

    # create ground body
    ground = b2d.BodyDef()
    ground.position = (0, -10)
    ground.type = b2d.BodyType.STATIC
    groud_body = b2d.create_body(world, ground)

    box =b2d.make_box(1, 1)
    shape_def = b2d.ShapeDef()
    shape_def.density = 1
    shape_def.friction = 0.3
    shape_id = b2d.create_polygon_shape(groud_body, shape_def, box)

    # create dynamic body
    body = b2d.BodyDef()
    body.position = (0, 4)
    body.type = b2d.BodyType.DYNAMIC
    body.angular_damping = 0.1
    body.linear_damping = 0.1
    body.fixed_rotation = False

    body_id = b2d.create_body(world, body)

    # create circle shape
    circle = b2d.Circle()
    circle.radius = 0.5
    shape = b2d.ShapeDef()
    shape.density = 1
    shape.friction = 0.3
    shape.restitution = 0.5
    shape_id = b2d.create_circle_shape(body_id, shape, circle)


    # simulate
    pos_inital = b2d.body_get_position(body_id)
    for i in range(60):
        b2d.world_step(world, 1 / 60, 6)
        pos = b2d.body_get_position(body_id)

    assert pos[1] < pos_inital[1]

