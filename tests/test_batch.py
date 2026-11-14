import numpy as np
import pytest
from pytest import approx

import pyb2d3 as b2d

from .conftest import make_box_body, step

pytestmark = pytest.mark.skipif(not b2d.WITH_BATCH_API, reason="batch api disabled in this build")

N = 10


@pytest.fixture
def body_list(world):
    world.gravity = (0, 0)
    return [make_box_body(world, position=(i, -i)) for i in range(N)]


@pytest.fixture
def bodies(body_list):
    return b2d.Bodies(body_list)


def test_construction(body_list, bodies):
    assert len(bodies) == N
    assert bodies.ids.dtype == np.uint64
    assert list(bodies.ids) == [b.id for b in body_list]
    assert len(b2d.Bodies(bodies.ids)) == N  # from an id array

    appended = b2d.Bodies()
    for b in body_list:
        appended.append(b)
    assert list(appended.ids) == list(bodies.ids)


def test_indexing(body_list, bodies):
    assert bodies[3] == body_list[3]
    assert isinstance(bodies[2:5], b2d.Bodies)
    assert list(bodies[2:5]) == body_list[2:5]
    mask = bodies.position[:, 0] > 4
    assert list(bodies[mask]) == body_list[5:]
    assert list(bodies) == body_list


def test_property_getters(body_list, bodies):
    pos = bodies.position
    assert pos.shape == (N, 2) and pos.dtype == np.float32
    for i, b in enumerate(body_list):
        assert pos[i] == approx(tuple(b.position))
    assert bodies.mass.shape == (N,)
    assert bodies.angle.shape == (N,)
    assert bodies.transform.shape == (N, 4)
    assert bodies.rotation.shape == (N, 2)
    assert bodies.is_valid.all()
    assert (bodies.type == b2d.BodyType.DYNAMIC.value).all()


def test_property_setters(body_list, bodies):
    velocities = np.arange(2 * N, dtype=np.float32).reshape(N, 2)
    bodies.linear_velocity = velocities
    for i, b in enumerate(body_list):
        assert b.linear_velocity == approx(tuple(velocities[i]))

    bodies.angular_velocity = 1.5  # broadcast a scalar
    assert all(b.angular_velocity == approx(1.5) for b in body_list)

    bodies.linear_velocity = (1, 2)  # broadcast a vector
    assert all(b.linear_velocity == approx((1, 2)) for b in body_list)

    bodies.user_data = np.arange(N, dtype=np.uint64)
    assert [b.user_data for b in body_list] == list(range(N))

    bodies.bullet = True
    assert all(b.bullet for b in body_list)

    with pytest.raises(ValueError):
        bodies.angular_velocity = np.ones(N + 1)


def test_methods(world, body_list, bodies):
    # per-body points -> per-body results
    local = np.tile(np.array([[0.5, 0.0]], dtype=np.float32), (N, 1))
    world_points = bodies.world_point(local)
    assert world_points.shape == (N, 2)
    for i, b in enumerate(body_list):
        assert world_points[i] == approx(tuple(b.world_point((0.5, 0))))

    # broadcast a single point
    back = bodies.local_point((1, 2))
    assert back.shape == (N, 2)
    assert back[0] == approx(tuple(body_list[0].local_point((1, 2))))

    # void methods: forces / impulses
    masses = bodies.mass
    bodies.apply_linear_impulse_to_center(np.stack([masses, np.zeros(N)], axis=1))
    assert bodies.linear_velocity[:, 0] == approx(np.ones(N))

    bodies.apply_force_to_center((0, 600))
    step(world, 1)
    assert (bodies.linear_velocity[:, 1] > 0).all()

    bodies.apply_force(np.zeros((N, 2)), bodies.world_center, wake=False)


def test_shapes_and_joints_batches(world, body_list):
    shapes = b2d.Shapes([b.shapes[0] for b in body_list])
    shapes.friction = np.linspace(0, 1, N)
    assert shapes.friction == approx(np.linspace(0, 1, N))
    assert shapes.density == approx(np.ones(N))
    assert isinstance(shapes[0], b2d.PolygonShape)

    joints = b2d.Joints([world.create_revolute_joint(body_list[i], body_list[i + 1]) for i in range(N - 1)])
    step(world, 2)
    assert joints.constraint_force.shape == (N - 1, 2)
    joints.collide_connected = True
    assert joints.collide_connected.all()
    assert isinstance(joints[0], b2d.RevoluteJoint)
