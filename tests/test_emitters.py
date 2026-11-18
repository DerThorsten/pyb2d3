import math

import numpy as np
import pytest
from pytest import approx

import pyb2d3 as b2d
from pyb2d3 import extensions as ext

DT = 1 / 60


@pytest.fixture
def world():
    return b2d.World(gravity=(0, 0))


def circle_def(**filter_args):
    shape_def = b2d.shape_def(density=1.0)
    if filter_args:
        shape_def.filter = b2d.make_filter(**filter_args)
    return shape_def


def radial(world, **settings):
    return ext.RadialEmitter(world, circle_def(), b2d.circle(radius=0.05), **settings)


def test_rate_and_fractional_carry(world):
    e = radial(world, rate=30.0, capacity=1000, lifetime=math.inf)
    for _ in range(60):
        e.step(DT)
    assert len(e) == 30  # 0.5 particles per step, carried over
    assert len(e.particles) == len(e.shapes) == len(e.ages) == len(e.lifetimes) == 30


def test_enabled(world):
    e = radial(world, rate=60.0, capacity=1000, lifetime=0.5, enabled=False)
    e.burst(3)  # burst works while paused
    for _ in range(60):
        impulse, _ = e.step(DT)
        assert tuple(impulse) == (0.0, 0.0)
    assert len(e) == 0  # nothing emitted, the burst particles expired
    e.enabled = True
    e.step(DT)
    assert len(e) == 1


@pytest.mark.parametrize("on_capacity_reached", list(ext.OnCapacityReached))
def test_capacity(world, on_capacity_reached):
    e = radial(world, rate=600.0, capacity=20, lifetime=math.inf, on_capacity_reached=on_capacity_reached)
    first = e.burst(5) and e.particles.ids
    for _ in range(30):
        e.step(DT)
        assert len(e) <= 20
    assert len(e) == 20
    alive = set(e.particles.ids)
    if on_capacity_reached == ext.OnCapacityReached.STOP:
        assert set(first) <= alive  # nothing was replaced
    if on_capacity_reached == ext.OnCapacityReached.DESTROY_OLDEST:
        assert not set(first) & alive  # the oldest went first
        assert np.all(np.diff(e.ages) <= 0)  # oldest first


def test_lifetime_and_expiry(world):
    e = radial(world, rate=120.0, capacity=1000, lifetime=ext.uniform(0.1, 2.0), max_lifetime=0.3)
    for _ in range(60):
        e.step(DT)
        assert np.all(e.lifetimes <= 0.3 + 1e-6)
        assert np.all(e.ages < e.lifetimes)
    # a second without new particles: all expired
    e.rate = 0.0
    for _ in range(30):
        e.step(DT)
    assert len(e) == 0


def test_distributions(world):
    e = radial(world, rate=0.0, capacity=1000, speed=ext.uniform(2.0, 3.0), lifetime=math.inf)
    e.burst(200)
    speed = np.linalg.norm(e.particles.linear_velocity, axis=1)
    assert speed.min() >= 2.0 - 1e-4 and speed.max() <= 3.0 + 1e-4
    assert ext.constant(1.5).a == 1.5
    assert repr(ext.normal(1, 2)) == "normal(1.0, 2.0)"
    e.speed = 4  # a number is a constant
    e.burst(1)
    assert np.linalg.norm(e.particles[-1:].linear_velocity) == approx(4.0, abs=1e-4)


def test_radial_geometry(world):
    e = radial(world, rate=0.0, capacity=1000, angle_min=0.2, angle_max=0.6, radius=2.0,
               lifetime=math.inf)
    e.transform = b2d.transform((5.0, 1.0), b2d.make_rot(0.5))
    e.burst(100)
    offsets = e.particles.position - np.array([5.0, 1.0])
    assert np.linalg.norm(offsets, axis=1) == approx(np.full(100, 2.0), abs=1e-4)
    angles = np.arctan2(offsets[:, 1], offsets[:, 0]) - 0.5
    assert angles.min() >= 0.2 - 1e-4 and angles.max() <= 0.6 + 1e-4
    velocity = e.particles.linear_velocity
    assert np.allclose(np.arctan2(velocity[:, 1], velocity[:, 0]) - 0.5, angles, atol=1e-4)


def test_linear_geometry(world):
    e = ext.LinearEmitter(world, circle_def(), b2d.circle(radius=0.05), rate=0.0, capacity=1000,
                          p1=(-2.0, 1.0), p2=(2.0, 1.0), along=ext.uniform(0.75, 1.0),
                          lifetime=math.inf)
    e.burst(100)
    position = e.particles.position
    assert position[:, 1] == approx(np.full(100, 1.0), abs=1e-5)
    assert position[:, 0].min() >= 1.0 - 1e-4 and position[:, 0].max() <= 2.0 + 1e-4
    velocity = e.particles.linear_velocity
    assert velocity[:, 0] == approx(np.zeros(100), abs=1e-5)  # the line's left normal: +y
    assert np.all(velocity[:, 1] > 0)


def test_reaction(world):
    owner = world.create_dynamic_body(position=(1.0, 2.0))
    owner.create_shape(b2d.shape_def(density=1.0), b2d.box(0.5, 0.5))
    e = radial(world, rate=0.0, capacity=1000, angle_min=-0.3, angle_max=0.3, radius=0.8,
               speed=ext.uniform(3.0, 5.0), lifetime=math.inf, body=owner,
               local_frame=b2d.transform((0.0, 0.2), b2d.make_rot(1.0)))
    # the owner at rest: the reaction is minus the momentum (and angular momentum about the
    # owner's center) of the new particles
    impulse, angular_impulse = e.burst(50)
    particles = e.particles
    momenta = particles.mass[:, None] * particles.linear_velocity
    assert tuple(impulse) == approx(tuple(-momenta.sum(axis=0)), abs=1e-4)
    arms = particles.position - np.array(owner.world_center)
    angular = np.sum(arms[:, 0] * momenta[:, 1] - arms[:, 1] * momenta[:, 0])
    assert angular_impulse == approx(-angular, abs=1e-4)

    # applied, it pushes the owner back (against the emission)
    owner.apply_linear_impulse_to_center(impulse)
    assert np.dot(owner.linear_velocity, momenta.sum(axis=0)) < 0


def test_inherits_the_owner_velocity(world):
    owner = world.create_kinematic_body(position=(0.0, 0.0), linear_velocity=(2.0, 0.0))
    e = radial(world, rate=0.0, capacity=10, speed=0.0, lifetime=math.inf, body=owner)
    impulse, _ = e.burst(1)
    assert tuple(e.particles.linear_velocity[0]) == approx((2.0, 0.0), abs=1e-5)
    assert tuple(impulse) == approx((0.0, 0.0), abs=1e-6)  # no speed relative to the owner


def test_no_collision_with_owner(world):
    owner = world.create_dynamic_body(position=(0.0, 0.0))
    owner.create_shape(b2d.shape_def(density=1.0), b2d.box(1.0, 1.0))
    # particles start inside the owner: only the filter joints keep them from colliding
    e = radial(world, rate=0.0, capacity=100, speed=0.0, lifetime=math.inf, body=owner,
               collide_with_owner=False)
    e.burst(10)
    world.step(DT, 4)
    assert owner.contact_capacity == 0
    assert np.linalg.norm(owner.linear_velocity) == approx(0.0, abs=1e-6)

    e2 = radial(world, rate=0.0, capacity=100, speed=0.0, lifetime=math.inf, body=owner)  # default
    e2.burst(1)
    world.step(DT, 4)
    assert owner.contact_capacity > 0


def test_filter_of_the_shape_def(world):
    # particles that do not collide with each other (mask without their own category)
    e = ext.RadialEmitter(world, circle_def(category_bits=0x2, mask_bits=0x1),
                          b2d.circle(radius=0.5), rate=0.0, capacity=10, speed=0.0,
                          lifetime=math.inf)
    e.burst(5)  # all at the same spot
    world.step(DT, 4)
    assert sum(s.contact_capacity for s in e.shapes) == 0


def test_follows_the_owner(world):
    owner = world.create_kinematic_body(position=(3.0, 4.0), rotation=b2d.make_rot(math.pi / 2))
    e = radial(world, rate=0.0, capacity=10, radius=1.0, speed=0.0, lifetime=math.inf, body=owner)
    e.burst(1)
    assert tuple(e.particles.position[0]) == approx((3.0, 5.0), abs=1e-5)  # x axis -> world up


def test_colors_by_age(world):
    e = radial(world, rate=0.0, capacity=10, lifetime=1.0, max_lifetime=1.0,
               colors=[(0.0, 0x000000), (1.0, 0xFF8040)])
    e.burst(1)
    assert e.shapes.custom_color[0] == 0x000000
    for _ in range(30):
        e.step(DT)  # half the life
    r, g, b = (int(e.shapes.custom_color[0]) >> s & 0xFF for s in (16, 8, 0))
    assert (r, g, b) == approx((0x80, 0x40, 0x20), abs=3)


def test_clear_and_external_destruction(world):
    e = radial(world, rate=0.0, capacity=10, lifetime=math.inf)
    e.burst(5)
    e.particles[:2].destroy()  # destroyed by someone else: dropped on the next step
    e.step(DT)
    assert len(e) == 3
    e.clear()
    assert len(e) == 0
    e.burst(3)
    world.destroy()
    assert e.step(DT)[1] == 0.0 and len(e) == 0  # the world is gone: nothing left


def test_unknown_setting(world):
    with pytest.raises(TypeError, match="no setting"):
        radial(world, rat=3)
