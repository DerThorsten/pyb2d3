import pytest
from pytest import approx

import numpy as np
import pyb2d3 as b2d

from .conftest import make_box_body, make_circle_body, step


def test_create_and_destroy():
    world = b2d.World(gravity=(0, -10), user_data=42)
    assert world.is_valid
    assert world.gravity == approx((0, -10))
    assert world.user_data == 42
    world.destroy()
    assert not world.is_valid
    world.destroy()  # destroying twice is harmless


def test_world_def():
    d = b2d.world_def(gravity=(1, 2), enable_sleep=False, contact_hertz=20)
    assert d.gravity == approx((1, 2))
    assert d.enable_sleep is False
    assert d.contact_hertz == approx(20)
    copy = d.copy()
    copy.contact_hertz = 10
    assert d.contact_hertz == approx(20)
    assert isinstance(d.capacity, b2d.Capacity)


def test_identity_and_hash(world):
    view = b2d.WorldView(world.id)
    assert view == world
    assert hash(view) == hash(world)
    assert {view: 1}[world] == 1


@pytest.mark.parametrize(
    "prop, value",
    [
        ("gravity", (0, -5)),
        ("sleeping_enabled", False),
        ("continuous_enabled", False),
        ("warm_starting_enabled", False),
        ("restitution_threshold", 2.0),
        ("restitution_iterations", 3),
        ("restitution_propagation_enabled", True),
        ("hit_event_threshold", 3.0),
        ("contact_recycle_distance", 0.05),
        ("max_linear_speed", 100.0),
    ],
)
def test_settings_roundtrip(world, prop, value):
    setattr(world, prop, value)
    got = getattr(world, prop)
    if isinstance(value, tuple):
        assert got == approx(value)
    else:
        assert got == approx(value)


def test_contact_tuning(world):
    world.set_contact_tuning(hertz=25, damping_ratio=5, push_speed=2)
    assert world.contact_tuning == approx((25, 5, 2))


def test_step_and_gravity(world):
    body = make_box_body(world, position=(0, 10))
    step(world, 30)
    assert body.position[1] < 10
    assert body.linear_velocity[1] < 0


def test_statistics(world, ground, box_body):
    step(world, 5)
    assert world.awake_body_count >= 1
    counters = world.counters
    assert counters.body_count == 2
    assert counters.shape_count == 2
    assert len(counters.color_counts) == 24
    assert world.profile.step >= 0
    assert isinstance(world.max_capacity, b2d.Capacity)
    assert isinstance(world.state_hash, int)
    bounds = world.bounds
    assert bounds.lower_bound[0] <= -50


def test_deterministic_state_hash():
    def run():
        w = b2d.World(gravity=(0, -10))
        make_box_body(w, position=(0, -1), hx=20, hy=1, body_type=b2d.BodyType.STATIC)
        for i in range(5):
            make_box_body(w, position=(0.1 * i, 2 + i))
        step(w, 60)
        return w.state_hash

    assert run() == run()


def test_explode(world):
    body = make_circle_body(world, position=(1, 0))
    world.gravity = (0, 0)
    world.explode(position=(0, 0), radius=5, impulse_per_length=10)
    step(world, 1)
    assert body.linear_velocity[0] > 0


def test_create_body_variants(world):
    a = world.create_dynamic_body(position=(1, 2), user_data=7)
    b = world.create_static_body(position=(0, 0))
    c = world.create_kinematic_body(position=(0, 0))
    # kwargs override fields of a given def (static bodies ignore velocities, so use kinematic)
    d = world.create_body(b2d.kinematic_body_def(position=(3, 4)), angular_velocity=1.0)
    assert a.type == b2d.BodyType.DYNAMIC
    assert b.type == b2d.BodyType.STATIC
    assert c.type == b2d.BodyType.KINEMATIC
    assert a.user_data == 7
    assert d.position == approx((3, 4))
    assert d.angular_velocity == approx(1.0)


def test_body_factory(world):
    factory = world.body_factory()
    factory.dynamic().shape(density=1).surface_material(restitution=1)
    factory.add_circle(radius=1).add_box(1, 1).is_bullet(True)
    for i in range(5):
        body = factory.position((i, 0)).user_data(i).create()
        assert body.user_data == i
        assert body.position == approx((i, 0))
        assert body.shape_count == 2
        assert body.bullet


@pytest.mark.skipif(not b2d.WITH_THREADING, reason="threading disabled in this build")
def test_thread_pool():
    pool = b2d.ThreadPool(4)
    assert pool.num_threads >= 1
    world = b2d.World(gravity=(0, -10), thread_pool=pool)
    make_box_body(world, position=(0, -1), hx=50, hy=1, body_type=b2d.BodyType.STATIC)
    bodies = [make_box_body(world, position=(i % 10, 1 + i // 10)) for i in range(100)]
    step(world, 30)
    assert all(np.isfinite(b.position).all() for b in bodies)


def test_snapshot_roundtrip(world, ground):
    body = make_box_body(world, position=(0, 5))
    step(world, 10)
    image = world.get_snapshot()
    assert isinstance(image, bytes) and len(image) > 0
    saved = tuple(body.position)

    step(world, 30)
    assert tuple(body.position) != approx(saved)

    assert world.restore_from_snapshot(image)
    assert tuple(body.position) == approx(saved)

    clone = b2d.World.from_snapshot(image)
    assert clone.counters.body_count == world.counters.body_count
