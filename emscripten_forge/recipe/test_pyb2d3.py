import pytest
from pytest import approx

import pyb2d3 as b2d


joint_names = ["distance", "filter", "motor", "mouse", "prismatic", "revolute", "wheel"]


def test_world_cls():
    world = b2d.World(gravity=(0, -10), user_data=42)
    assert world.gravity.x == approx(0)
    assert world.gravity.y == approx(-10)
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
    a = body.angle
    assert body.user_data == 100

    material = b2d.surface_material(friction=0.5, restitution=0.3)
    shape_def = b2d.shape_def(density=1, material=material, user_data=400)

    shapes = [b2d.box(1, 1), b2d.circle(radius=0.5)]

    for i in range(10):
        body = world.create_body(body_def)
        for shape in shapes:
            shape_id = body.create_shape(shape_def, shape)
            assert shape_id.user_data == 400


@pytest.mark.parametrize("joint_name", joint_names)
def test_joints(joint_name):
    print(f"Testing joint: {joint_name}")
    cls_name = f"{joint_name.capitalize()}Joint"
    joint_cls = getattr(b2d, cls_name, None)
    world_func = getattr(b2d.World, f"create_{joint_name}_joint", None)

    world = b2d.World(gravity=(0, -10))
    factory = world.body_factory()
    factory.dynamic().shape(density=1).add_box(1, 1)
    body_a = factory.position((0, 0)).create()
    body_b = factory.position((2, 0)).create()

    joint = world_func(world, body_a, body_b)

    assert isinstance(joint, joint_cls)
    assert joint.body_a == body_a
    assert joint.body_b == body_b
