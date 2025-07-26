import pytest
from pytest import approx

import numpy as np
import pyb2d3 as b2d


from .conftest import *  # noqa

joint_names = ["distance", "filter", "motor", "mouse", "prismatic", "revolute", "wheel"]


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

    shapes = [b2d.box(1, 1), b2d.circle(radius=0.5)]

    for i in range(10):
        body = world.create_body(body_def)
        for shape in shapes:
            shape_id = body.create_shape(shape_def, shape)
            assert shape_id is not None
            # assert shape_id.user_data == 400

    # hl_shapes = body.create_shapes(shape_def, shapes)


def test_body_builder():
    world = b2d.World(gravity=(0, -10))

    factory = world.body_factory()
    factory.dynamic().shape(density=1).surface_material(restitution=1)
    factory.add_circle(radius=1).add_box(1, 1).is_bullet(True)
    for i in range(10):
        body = factory.position((i, 0)).user_data(i).create()
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
                assert polygon is not None


@pytest.mark.skipif(
    not b2d.WITH_THREADING, reason="Threading is not enabled in this build of pyb2d"
)
def test_threadpool():
    pool = b2d.ThreadPool()
    world = b2d.World(gravity=(0, -10), thread_pool=pool)
    factory = world.body_factory()
    factory.dynamic().shape(density=1).surface_material(restitution=1)
    factory.add_circle(radius=1).add_box(1, 1)
    for i in range(100):
        rx = i % 10
        ry = i + 1 % 10
        body = factory.position((rx, ry)).create()
        assert body is not None
    for i in range(20):
        world.step(1 / 60, 4)


@pytest.mark.parametrize("joint_name", joint_names)
def test_joints(joint_name):
    cls_name = f"{joint_name.capitalize()}Joint"
    joint_cls = getattr(b2d, cls_name, None)
    world_func = getattr(b2d.World, f"create_{joint_name}_joint", None)

    world = b2d.World(gravity=(0, -10))
    factory = world.body_factory()
    factory.dynamic().shape(density=1).add_box(1, 1)
    body_a = factory.position((-1, 1)).create()
    body_b = factory.position((2, -2)).create()

    joint = world_func(world, body_a, body_b)

    assert isinstance(joint, joint_cls)
    assert joint.body_a == body_a
    assert joint.body_b == body_b


def test_batch_api():
    world = b2d.World(gravity=(0, -10))
    factory = world.body_factory()
    factory.dynamic().shape(density=1).add_box(1, 1)
    body_list = [factory.position((i, -i)).create() for i in range(10)]
    bodies = b2d.Bodies()
    for body in body_list:
        bodies.append(body)
    n_bodies = len(bodies)
    assert n_bodies == len(body_list)

    world.step(1 / 60, 4)

    # from pre-allocated positions object
    positions = np.zeros((n_bodies, 2), dtype=np.float32)
    pos = bodies.get_positions(positions)

    # ensure positions are filled correctly
    for i in range(n_bodies):
        assert pos[i, 0] == approx(body_list[i].position[0])
        assert pos[i, 1] == approx(body_list[i].position[1])

    # ensure output "pos" is the same as "positions"
    assert pos is positions

    pos2 = bodies.get_positions()
    assert pos2.shape == (n_bodies, 2)
    for i in range(n_bodies):
        assert pos2[i, 0] == approx(body_list[i].position[0])
        assert pos2[i, 1] == approx(body_list[i].position[1])

    # get velocities
    velocities = np.zeros((n_bodies, 2), dtype=np.float32)
    vel = bodies.get_linear_velocities(velocities)
    assert vel is velocities
    vel2 = bodies.get_linear_velocities()

    # ensure velocities are filled correctly
    for i in range(n_bodies):
        assert vel[i, 0] == approx(body_list[i].linear_velocity[0])
        assert vel[i, 1] == approx(body_list[i].linear_velocity[1])
        assert vel2[i, 0] == approx(body_list[i].linear_velocity[0])
        assert vel2[i, 1] == approx(body_list[i].linear_velocity[1])

    # get_angular_velocities
    angular_velocities = np.zeros(n_bodies, dtype=np.float32)
    ang_vel = bodies.get_angular_velocities(angular_velocities)
    assert ang_vel is angular_velocities
    ang_vel2 = bodies.get_angular_velocities()

    # ensure angular velocities are filled correctly
    for i in range(n_bodies):
        assert ang_vel[i] == approx(body_list[i].angular_velocity)
        assert ang_vel2[i] == approx(body_list[i].angular_velocity)

    # set agular velocities
    new_angular_velocities = np.array([i for i in range(n_bodies)], dtype=np.float32)
    bodies.set_angular_velocities(new_angular_velocities)

    # ensure angular velocities are set correctly
    for i in range(n_bodies):
        assert body_list[i].angular_velocity == approx(new_angular_velocities[i])

    # set from scalar
    bodies.set_angular_velocities(1.0)
    for i in range(n_bodies):
        assert body_list[i].angular_velocity == approx(1.0)

    # set from array with 1 value
    bodies.set_angular_velocities(np.array([3.0], dtype=np.float32))
    for i in range(n_bodies):
        assert body_list[i].angular_velocity == approx(3.0)

    # get_linear_velocities_magnitude
    linear_velocities_magnitude = bodies.get_linear_velocities_magnitude()
    assert linear_velocities_magnitude.shape == (n_bodies,)
    for i in range(n_bodies):
        assert linear_velocities_magnitude[i] == approx(
            np.linalg.norm(body_list[i].linear_velocity)
        )

    # get_local_points from world points
    world_points = np.array([(i, i + 1) for i in range(len(bodies))], dtype=np.float32)
    assert world_points.shape == (len(bodies), 2)
    local_points = bodies.get_local_points(world_points)
    assert local_points.shape == world_points.shape

    for i in range(len(world_points)):
        assert local_points[i, 0] == approx(
            body_list[i].local_point(world_points[i])[0]
        )
        assert local_points[i, 1] == approx(
            body_list[i].local_point(world_points[i])[1]
        )

    # get_local_points from **single** world point
    world_point = np.array((1, 2), dtype=np.float32)
    local_points = bodies.get_local_points(world_points=world_point)
    assert local_points.shape == (len(bodies), 2)
    for i in range(len(bodies)):
        assert local_points[i, 0] == approx(body_list[i].local_point(world_point)[0])
        assert local_points[i, 1] == approx(body_list[i].local_point(world_point)[1])


def test_query_callback_with_chains():
    world = b2d.World(gravity=(0, -10))
    w = 100
    ground_points = np.array(
        [
            (-w, 1.0),
            (w, 0.0),
            (-w, 0.0),
            (-w, 0.1),
        ]
    )

    material = b2d.surface_material(restitution=1.0, friction=0.0)

    chain_def = b2d.chain_def(
        points=ground_points,
        materials=[material, material, material, material],
    )

    ground = world.create_static_body(position=(0, 0))
    ground.create_chain(chain_def)

    # create aabb around the point
    world_point = (0, 0)
    aabb = b2d.aabb_arround_point(point=world_point, radius=10)

    def callback(shape):
        # check if the world point is inside the shape
        if shape.body.type != b2d.BodyType.STATIC:
            return b2d.CONTINUE_QUERY
        return b2d.STOP_QUERY

    world.overlap_aabb(aabb, callback)

    # callback = QueryCallback()
    # world.query_aabb(callback, body.aabb)

    # assert callback.hit_count == 1
