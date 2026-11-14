import math

import pytest
from pytest import approx

import pyb2d3 as b2d

from .conftest import make_box_body, make_circle_body, step


def test_identity(world, box_body):
    assert box_body.is_valid
    same = b2d.Body(box_body.id)
    assert same == box_body
    assert hash(same) == hash(box_body)
    assert box_body.world == world
    assert "Body(id=" in repr(box_body)


def test_destroy(world, box_body):
    shape = box_body.shapes[0]
    box_body.destroy()
    assert not box_body.is_valid
    assert not shape.is_valid


def test_equality_with_other_types(world, two_bodies):
    a, b = two_bodies
    assert a == b2d.Body(a.id) and a != b
    assert a != None  # noqa: E711
    assert not (a == "a body")
    assert a in [None, b, a]
    assert len({a, b2d.Body(a.id), b}) == 2


def test_destroy_stale_handles_is_noop(world, two_bodies):
    # handles of objects that died with their body must not crash box2d
    a, b = two_bodies
    joint = world.create_revolute_joint(body_a=a, body_b=b)
    shape = b.shapes[0]
    stale_b = b2d.Body(b.id)
    b.destroy()
    assert not joint.is_valid and not shape.is_valid
    joint.destroy()
    shape.destroy()
    stale_b.destroy()
    b.destroy()
    assert a.is_valid


def test_destroy_keeps_hash():
    # a destroyed body can still be found in (and removed from) a set or dict
    world = b2d.World(gravity=(0, -10))
    body = make_box_body(world)
    lifetimes = {body: 1.0}
    body.destroy()
    assert not body.is_valid
    del lifetimes[body]
    assert body == b2d.Body(body.id)


def test_type_name_user_data(box_body):
    box_body.type = b2d.BodyType.KINEMATIC
    assert box_body.type == b2d.BodyType.KINEMATIC
    box_body.name = "player"
    assert box_body.name == "player"
    box_body.user_data = 1234
    assert box_body.user_data == 1234


def test_pose(box_body):
    # box2d builds rotations with a fast cos/sin approximation (~1e-3 accurate)
    box_body.set_transform((1, 2), 0.5)
    assert box_body.position == approx((1, 2))
    assert box_body.angle == approx(0.5, abs=2e-3)
    assert box_body.rotation.angle == approx(box_body.angle)
    t = box_body.transform
    assert t.p == approx((1, 2))
    assert t.q.angle == approx(box_body.angle)


def test_frames(box_body):
    box_body.set_transform((1, 2), math.pi / 2)
    world_point = box_body.world_point((1, 0))
    assert world_point == approx((1, 3), abs=1e-5)
    assert box_body.local_point(world_point) == approx((1, 0), abs=1e-5)
    assert box_body.world_vector((1, 0)) == approx((0, 1), abs=1e-5)
    assert box_body.local_vector((0, 1)) == approx((1, 0), abs=1e-5)
    assert box_body.distance_to((4, 6)) == approx(5)


def test_velocities(world, box_body):
    world.gravity = (0, 0)
    box_body.linear_velocity = (3, 4)
    box_body.angular_velocity = 2.0
    assert box_body.linear_velocity == approx((3, 4))
    assert box_body.speed == approx(5)
    assert box_body.angular_velocity == approx(2.0)
    # velocity of the point (1, 0) in local coordinates: v + w x r
    assert box_body.local_point_velocity((1, 0)) == approx((3, 6))
    assert box_body.world_point_velocity(box_body.world_point((1, 0))) == approx((3, 6))


def test_forces_and_impulses(world):
    world.gravity = (0, 0)
    body = make_circle_body(world)
    mass = body.mass

    body.apply_linear_impulse_to_center((mass * 2, 0))
    assert body.linear_velocity == approx((2, 0))

    body.apply_linear_impulse((0, mass), body.world_center)
    assert body.linear_velocity == approx((2, 1))

    body.apply_angular_impulse(body.rotational_inertia * 3)
    assert body.angular_velocity == approx(3)

    body.linear_velocity = (0, 0)
    body.angular_velocity = 0
    body.apply_force_to_center((mass * 60, 0))
    body.apply_torque(1.0)
    step(world, 1)
    assert body.linear_velocity[0] == approx(1.0, rel=1e-3)
    assert body.angular_velocity > 0

    body.linear_velocity = (0, 0)
    body.apply_force((0, 10), body.world_center)
    body.clear_forces()
    step(world, 1)
    assert body.linear_velocity == approx((0, 0))


def test_mass(world):
    body = make_box_body(world, position=(2, 3), hx=1, hy=1, density=2)
    assert body.mass == approx(8)
    assert body.rotational_inertia > 0
    assert body.local_center == approx((0, 0))
    assert body.world_center == approx((2, 3))

    md = body.mass_data
    md.mass = 1.0
    body.mass_data = md
    assert body.mass == approx(1.0)
    body.update_mass_from_shapes()
    assert body.mass == approx(8)


@pytest.mark.parametrize(
    "prop, value",
    [
        ("linear_damping", 0.5),
        ("angular_damping", 0.25),
        ("gravity_scale", 2.0),
        ("sleep_threshold", 0.1),
        ("safety_factor", 0.5),
        ("bullet", True),
        ("sleep_enabled", False),
        ("contact_recycling_enabled", False),
        ("fixed_rotation", True),
        ("enabled", False),
        ("awake", False),
    ],
)
def test_property_roundtrip(box_body, prop, value):
    setattr(box_body, prop, value)
    assert getattr(box_body, prop) == approx(value)


def test_motion_locks(world, box_body):
    box_body.motion_locks = b2d.MotionLocks(linear_x=True, angular_z=True)
    locks = box_body.motion_locks
    assert locks.linear_x and not locks.linear_y and locks.angular_z
    assert box_body.fixed_rotation

    world.gravity = (0, 0)
    box_body.linear_velocity = (5, 5)
    step(world, 10)
    assert box_body.position[0] == approx(0)  # x is locked
    assert box_body.position[1] > 5


def test_target_transform_moves_kinematic_body(world):
    body = world.create_kinematic_body(position=(0, 0))
    for _ in range(10):
        body.set_target_transform(b2d.transform(p=(1, 0)), 1 / 60)
        world.step(1 / 60, 4)
    assert body.position == approx((1, 0), abs=1e-3)


def test_sleep_and_wake(world, ground):
    body = make_box_body(world, position=(0, 0.5))
    step(world, 300)
    assert not body.awake
    body.wake_touching()
    body.awake = True
    assert body.awake


def test_extents_and_bounds(world):
    body = make_box_body(world, position=(3, 0), hx=1, hy=2)
    assert body.min_extent == approx(1)
    assert body.max_extent == approx(math.sqrt(5))
    assert body.max_extent_from_origin == approx(math.sqrt(5))
    bounds = body.compute_bounds()
    assert bounds.lower_bound == approx((2, -2), abs=0.1)
    assert bounds.upper_bound == approx((4, 2), abs=0.1)


def test_shapes_joints_contacts(world, ground):
    body = make_box_body(world, position=(0, 0.5))
    body.create_circle_shape(b2d.shape_def(), b2d.circle(radius=0.2))
    assert body.shape_count == 2
    assert {type(s) for s in body.shapes} == {b2d.PolygonShape, b2d.CircleShape}

    step(world, 30)
    assert body.contact_capacity >= 1
    data = body.contact_data
    assert len(data) >= 1
    assert {data[0].shape_a.body, data[0].shape_b.body} == {ground, body}

    # (jointed bodies do not collide by default, so joints are tested after contacts)
    joint = world.create_revolute_joint(ground, body)
    assert body.joint_count == 1
    assert body.joints == [joint]


def test_event_toggles(box_body):
    # setter only in box2d: just make sure they are callable
    box_body.enable_contact_events(False)
    box_body.enable_hit_events(True)
