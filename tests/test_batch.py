import numpy as np
import pytest
from pytest import approx

import pyb2d3 as b2d

from .conftest import make_box_body, step

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


def test_create_bodies(world):
    bodies = world.create_dynamic_bodies(N, linear_damping=0.5)
    assert isinstance(bodies, b2d.Bodies) and len(bodies) == N
    assert (bodies.type == b2d.BodyType.DYNAMIC.value).all()
    assert bodies.linear_damping == approx(np.full(N, 0.5))
    assert len(world.create_bodies(3, b2d.body_def(type=b2d.BodyType.STATIC))) == 3


def test_create_shape_on_each(world):
    bodies = world.create_dynamic_bodies(N)
    shape_def = b2d.shape_def(density=2.0)
    circles = bodies.create_shape(shape_def, b2d.circle(radius=0.5))  # one for all
    assert isinstance(circles, b2d.Shapes) and len(circles) == N
    assert all(isinstance(s, b2d.CircleShape) for s in circles)
    assert circles.density == approx(np.full(N, 2.0))
    radii = np.linspace(0.1, 1.0, N)
    sized = bodies.create_shape(shape_def, [b2d.circle(radius=r) for r in radii])  # one per body
    assert [s.circle.radius for s in sized] == approx(radii)
    for geometry, cls in [
        (b2d.box(0.5, 0.5), b2d.PolygonShape),
        (b2d.capsule((0, 0), (1, 0), 0.2), b2d.CapsuleShape),
        (b2d.segment((0, 0), (1, 0)), b2d.SegmentShape),
    ]:
        assert all(isinstance(s, cls) for s in bodies.create_shape(shape_def, geometry))
    assert (bodies.shape_count == 5).all()
    with pytest.raises(ValueError):
        bodies.create_shape(shape_def, [b2d.circle(radius=1.0)] * (N - 1))


def test_custom_color(world, body_list):
    shapes = b2d.Shapes([b.shapes[0] for b in body_list])
    colors = np.arange(N, dtype=np.uint32) * 0x010203
    shapes.custom_color = colors
    assert (shapes.custom_color == colors).all()
    shapes[0].custom_color = 0xFF0000
    assert shapes[0].custom_color == 0xFF0000 == shapes[0].surface_material.custom_color


def test_writable_pose(bodies):
    bodies.angle = 0.25
    positions = np.arange(2 * N, dtype=np.float32).reshape(N, 2)
    bodies.position = positions
    assert bodies.position == approx(positions)
    assert bodies.angle == approx(np.full(N, 0.25), abs=1e-2)  # the rotation is kept
    bodies.rotation = (1.0, 0.0)
    assert bodies.angle == approx(np.zeros(N), abs=1e-6)
    assert bodies.position == approx(positions)  # the position is kept
    bodies[0].position = (-1, -2)
    assert tuple(bodies[0].position) == approx((-1, -2))


def test_destroy(world, body_list, bodies):
    joints = b2d.Joints([world.create_revolute_joint(body_list[i], body_list[i + 1]) for i in range(N - 1)])
    joints[:3].destroy()
    assert not joints[:3].is_valid.any() and joints[3:].is_valid.all()

    shapes = b2d.Shapes([b.shapes[0] for b in body_list[:2]])
    shapes.destroy(update_body_mass=False)
    assert not shapes.is_valid.any()

    bodies[:5].destroy()  # with their remaining shapes and joints
    assert not bodies[:5].is_valid.any() and bodies[5:].is_valid.all()
    assert not joints[3].is_valid  # joint 3 links bodies 3 and 4
    bodies.destroy()  # destroyed ids are skipped
    assert not bodies.is_valid.any()
