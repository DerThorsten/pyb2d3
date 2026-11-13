import gc

import pytest
from pytest import approx

import pyb2d3 as b2d


def test_body_def():
    d = b2d.body_def(
        type=b2d.BodyType.DYNAMIC,
        position=(1, 2),
        rotation=0.5,
        linear_velocity=(3, 4),
        angular_velocity=1.0,
        linear_damping=0.1,
        angular_damping=0.2,
        gravity_scale=0.5,
        sleep_threshold=0.01,
        safety_factor=0.25,
        enable_sleep=False,
        is_awake=False,
        is_bullet=True,
        is_enabled=False,
        allow_fast_rotation=True,
        enable_contact_recycling=False,
        user_data=17,
    )
    assert d.type == b2d.BodyType.DYNAMIC
    assert d.position == approx((1, 2))
    assert d.rotation.angle == approx(0.5, abs=2e-3)
    assert d.linear_velocity == approx((3, 4))
    for name, value in [
        ("angular_velocity", 1.0),
        ("linear_damping", 0.1),
        ("angular_damping", 0.2),
        ("gravity_scale", 0.5),
        ("sleep_threshold", 0.01),
        ("safety_factor", 0.25),
    ]:
        assert getattr(d, name) == approx(value), name
    assert not d.enable_sleep and not d.is_awake and d.is_bullet and not d.is_enabled
    assert d.allow_fast_rotation and not d.enable_contact_recycling
    assert d.user_data == 17


def test_body_def_name_outlives_python_string(world):
    d = b2d.BodyDef()
    d.name = "".join(["dyn", "amic_", "name"])  # a temporary string
    gc.collect()
    body = world.create_body(d)
    assert d.name == "dynamic_name"
    # box2d stores at most NAME_LENGTH characters
    assert b2d.NAME_LENGTH == 10
    assert body.name == "dynamic_name"[: b2d.NAME_LENGTH]


def test_motion_locks_and_fixed_rotation():
    d = b2d.body_def(fixed_rotation=True)
    assert d.motion_locks.angular_z
    d.motion_locks = b2d.MotionLocks(linear_x=True)
    assert d.motion_locks.linear_x
    assert not d.fixed_rotation


def test_shape_def():
    material = b2d.surface_material(friction=0.2, restitution=0.3)
    d = b2d.shape_def(
        material=material,
        density=2,
        filter=b2d.make_filter(category_bits=4),
        enable_custom_filtering=True,
        is_sensor=True,
        enable_sensor_events=True,
        enable_contact_events=False,
        enable_hit_events=True,
        enable_pre_solve_events=True,
        invoke_contact_creation=True,
        update_body_mass=False,
        user_data=5,
    )
    assert d.material.friction == approx(0.2)
    assert d.density == approx(2)
    assert d.filter.category_bits == 4
    assert d.enable_custom_filtering and d.is_sensor and d.enable_sensor_events
    assert not d.enable_contact_events and d.enable_hit_events and d.enable_pre_solve_events
    assert d.invoke_contact_creation and not d.update_body_mass
    assert d.user_data == 5


def test_defaults_match_box2d():
    assert b2d.Filter().category_bits == 1
    assert b2d.Filter().mask_bits == 2**64 - 1
    assert b2d.QueryFilter().mask_bits == 2**64 - 1
    assert b2d.SurfaceMaterial().friction == approx(0.6)
    assert b2d.ShapeDef().density == approx(1)
    assert b2d.WorldDef().gravity == approx((0, -10))


def test_explosion_def():
    d = b2d.explosion_def(mask_bits=3, position=(1, 1), radius=2, falloff=0.5, impulse_per_length=4)
    assert d.mask_bits == 3
    assert d.position == approx((1, 1))
    assert (d.radius, d.falloff, d.impulse_per_length) == approx((2, 0.5, 4))


def test_world_def_capacity():
    d = b2d.WorldDef()
    cap = b2d.Capacity()
    cap.dynamic_body_count = 100
    d.capacity = cap
    assert d.capacity.dynamic_body_count == 100
    d.worker_count = 2
    assert d.worker_count == 2


@pytest.mark.parametrize(
    "cls",
    [b2d.WorldDef, b2d.BodyDef, b2d.ShapeDef, b2d.SurfaceMaterial, b2d.Filter, b2d.QueryFilter, b2d.ExplosionDef],
)
def test_copy_is_independent(cls):
    import copy

    a = cls()
    b = a.copy()
    c = copy.copy(a)
    assert type(b) is cls and type(c) is cls
    assert b is not a


def test_update():
    d = b2d.BodyDef()
    assert d.update(gravity_scale=3) is d
    assert d.gravity_scale == approx(3)
    j = b2d.RevoluteJointDef()
    j.update(enable_motor=True)
    assert j.enable_motor
