import math

import pytest
from pytest import approx

import pyb2d3 as b2d

from .conftest import make_box_body, make_circle_body, step

JOINT_NAMES = ["distance", "filter", "motor", "mover", "pogo", "prismatic", "revolute", "weld", "wheel"]


def joint_class(name):
    return getattr(b2d, f"{name.capitalize()}Joint")


@pytest.mark.parametrize("name", JOINT_NAMES)
def test_create_joint(world, two_bodies, name):
    a, b = two_bodies
    joint = getattr(world, f"create_{name}_joint")(a, b)
    assert isinstance(joint, joint_class(name))
    assert joint.is_valid
    assert joint.type == getattr(b2d.JointType, name.upper())
    assert joint.body_a == a
    assert joint.body_b == b
    assert joint.world == world
    assert isinstance(b2d.Joint(joint.id).cast(), joint_class(name))
    step(world, 5)
    joint.destroy()
    assert not joint.is_valid


@pytest.mark.parametrize("name", JOINT_NAMES)
def test_create_from_def(world, two_bodies, name):
    a, b = two_bodies
    joint_def = getattr(b2d, f"{name}_joint_def")(body_a=a, body_b=b, user_data=3)
    assert isinstance(joint_def, getattr(b2d, f"{name.capitalize()}JointDef"))
    joint = world.create_joint(joint_def)
    assert isinstance(joint, joint_class(name))
    assert joint.user_data == 3


def test_joint_def_base_fields(two_bodies):
    a, b = two_bodies
    d = b2d.revolute_joint_def(body_a=a, body_b=b)
    d.local_anchor_a = (1, 2)
    d.local_frame_b = b2d.transform(p=(3, 4), q=0.5)
    d.collide_connected = True
    d.force_threshold = 10
    d.torque_threshold = 20
    d.constraint_hertz = 30
    d.constraint_damping_ratio = 2
    d.draw_scale = 0.5
    assert d.body_a == a and d.body_b == b
    assert d.local_frame_a.p == approx((1, 2))
    assert d.local_anchor_b == approx((3, 4))
    assert d.base.collide_connected
    assert d.base.force_threshold == approx(10)
    assert d.base.torque_threshold == approx(20)
    assert d.base.constraint_hertz == approx(30)
    assert d.base.constraint_damping_ratio == approx(2)
    assert d.base.draw_scale == approx(0.5)
    assert isinstance(d.base, b2d.JointDef)


def test_create_joint_variants(world, two_bodies):
    a, b = two_bodies
    j1 = world.create_revolute_joint(a, b, enable_motor=True)
    j2 = world.create_revolute_joint(body_a=a, body_b=b)
    j3 = world.create_revolute_joint(b2d.revolute_joint_def(body_a=a, body_b=b))
    assert all(isinstance(j, b2d.RevoluteJoint) for j in (j1, j2, j3))
    assert j1.motor_enabled
    with pytest.raises(ValueError):
        world.create_revolute_joint(b2d.revolute_joint_def(), enable_motor=True)
    with pytest.raises(ValueError):
        world.create_joint("not a def")


def test_base_joint_api(world, two_bodies):
    a, b = two_bodies
    joint = world.create_weld_joint(a, b, local_anchor_a=(1, 0), local_anchor_b=(-1, 0))
    assert joint.local_frame_a.p == approx((1, 0))
    joint.local_frame_b = b2d.transform(p=(-0.5, 0))
    assert joint.local_frame_b.p == approx((-0.5, 0))

    joint.collide_connected = True
    assert joint.collide_connected
    joint.user_data = 99
    assert joint.user_data == 99

    joint.set_constraint_tuning(hertz=40, damping_ratio=3)
    assert joint.constraint_tuning == approx((40, 3))
    joint.force_threshold = 5
    joint.torque_threshold = 6
    assert joint.force_threshold == approx(5)
    assert joint.torque_threshold == approx(6)

    joint.wake_bodies()
    step(world, 10)
    assert len(joint.constraint_force) == 2
    assert isinstance(joint.constraint_torque, float)
    assert joint.linear_separation >= 0
    assert joint.angular_separation >= 0
    assert joint in a.joints


ROUNDTRIP = {
    "distance": dict(
        rest_length=2.0,
        spring_enabled=True,
        spring_hertz=3.0,
        spring_damping_ratio=0.5,
        limit_enabled=True,
        motor_enabled=True,
        target_motor_speed=1.5,
        max_motor_force=10.0,
    ),
    "motor": dict(
        linear_velocity=(1.0, 2.0),
        angular_velocity=0.5,
        max_velocity_force=10.0,
        max_velocity_torque=5.0,
        linear_hertz=4.0,
        linear_damping_ratio=0.7,
        angular_hertz=4.0,
        angular_damping_ratio=0.7,
        max_spring_force=10.0,
        max_spring_torque=5.0,
    ),
    "mover": dict(linear_velocity=(1.0, 0.0), max_velocity_force=(10.0, 10.0)),
    "pogo": dict(rest_length=1.0, spring_hertz=3.0, spring_damping_ratio=0.5),
    "prismatic": dict(
        spring_enabled=True,
        spring_hertz=3.0,
        spring_damping_ratio=0.5,
        target_translation=0.5,
        limit_enabled=True,
        motor_enabled=True,
        target_motor_speed=1.5,
        max_motor_force=10.0,
    ),
    "revolute": dict(
        spring_enabled=True,
        spring_hertz=3.0,
        spring_damping_ratio=0.5,
        target_angle=0.3,
        limit_enabled=True,
        motor_enabled=True,
        target_motor_speed=1.5,
        max_motor_torque=10.0,
    ),
    "weld": dict(linear_hertz=3.0, linear_damping_ratio=0.5, angular_hertz=4.0, angular_damping_ratio=0.25),
    "wheel": dict(
        spring_enabled=True,
        spring_hertz=3.0,
        spring_damping_ratio=0.5,
        limit_enabled=True,
        motor_enabled=True,
        target_motor_speed=1.5,
        max_motor_torque=10.0,
    ),
}

READ_ONLY = {
    "distance": ["current_length", "spring_force", "current_motor_force", "lower_limit", "upper_limit"],
    "pogo": ["current_length", "current_speed", "impulse"],
    "prismatic": ["current_translation", "current_speed", "current_motor_force", "lower_limit", "upper_limit"],
    "revolute": ["current_angle", "current_speed", "current_motor_torque", "lower_limit", "upper_limit"],
    "wheel": ["current_motor_torque", "lower_limit", "upper_limit"],
}


@pytest.mark.parametrize("name", sorted(ROUNDTRIP))
def test_property_roundtrip(world, two_bodies, name):
    a, b = two_bodies
    joint = getattr(world, f"create_{name}_joint")(a, b)
    for prop, value in ROUNDTRIP[name].items():
        setattr(joint, prop, value)
        got = getattr(joint, prop)
        assert got == approx(value), prop
    step(world, 5)
    for prop in READ_ONLY.get(name, []):
        assert isinstance(getattr(joint, prop), float), prop


@pytest.mark.parametrize("name", ["distance", "prismatic", "revolute", "wheel"])
def test_set_limits(world, two_bodies, name):
    a, b = two_bodies
    joint = getattr(world, f"create_{name}_joint")(a, b)
    joint.set_limits(0.25, 1.5)
    assert joint.lower_limit == approx(0.25)
    assert joint.upper_limit == approx(1.5)


def test_distance_spring_force_range(world, two_bodies):
    joint = world.create_distance_joint(*two_bodies)
    joint.set_spring_force_range(lower_force=-5, upper_force=7)
    assert joint.spring_force_range == approx((-5, 7))


def test_revolute_motor_reaches_speed(world):
    world.gravity = (0, 0)
    ground = world.create_static_body()
    # damping is a load the motor has to work against (without it the reported
    # torque of the last sub-step is 0 once the target speed is reached)
    wheel = make_circle_body(world, angular_damping=1.0)
    joint = world.create_revolute_joint(ground, wheel, enable_motor=True, motor_speed=2.0, max_motor_torque=1000)
    step(world, 60)
    assert joint.current_speed == approx(2.0, rel=1e-2)
    assert wheel.angular_velocity == approx(2.0, rel=1e-2)
    assert joint.current_motor_torque > 0


def test_revolute_limit_holds(world):
    ground = world.create_static_body()
    arm = make_box_body(world, position=(1, 0), hx=1, hy=0.1)
    joint = world.create_revolute_joint(
        ground,
        arm,
        local_anchor_b=(-1, 0),
        enable_limit=True,
        lower_angle=-0.25 * math.pi,
        upper_angle=0.25 * math.pi,
    )
    step(world, 120)
    assert joint.current_angle == approx(-0.25 * math.pi, abs=0.05)


def test_distance_joint_keeps_length(world):
    ground = world.create_static_body(position=(0, 10))
    ball = make_circle_body(world, position=(3, 10))
    joint = world.create_distance_joint(ground, ball, length=3.0)
    step(world, 120)
    assert joint.current_length == approx(3.0, abs=0.05)
    assert joint.rest_length == approx(3.0)


def test_joint_force_threshold_events(world):
    ground = world.create_static_body(position=(0, 10))
    ball = make_circle_body(world, position=(0, 8))
    joint = world.create_revolute_joint(ground, ball, local_anchor_b=(0, 2))
    joint.force_threshold = 0.0
    joint.user_data = 11
    step(world, 1)
    events = world.get_joint_events()
    assert events.count >= 1
    hits = [e for e in events.events() if e.joint == joint]
    assert hits and hits[0].user_data == 11


def test_mouse_drag(world, ground):
    body = make_box_body(world, position=(0, 0.5))
    drag = b2d.MouseDrag(world)
    assert drag.begin((0, 0.5)) == body
    assert drag.active
    drag.update((3, 3))
    for _ in range(180):
        drag.step(1 / 60)
        world.step(1 / 60, 4)
    assert body.position == approx((3, 3), abs=0.25)
    drag.end()
    assert not drag.active
    assert world.counters.joint_count == 0
    assert world.counters.body_count == 2

    # nothing under the cursor
    assert drag.begin((40, 40)) is None
