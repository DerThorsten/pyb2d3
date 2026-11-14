from pytest import approx

import numpy as np
import pyb2d3 as b2d

from .conftest import make_box_body, step


def drop_ball(world, height=5.0, **shape_kwargs):
    ball = world.create_dynamic_body(position=(0, height))
    shape = ball.create_circle_shape(b2d.shape_def(**shape_kwargs), b2d.circle(radius=0.5))
    return ball, shape


def test_contact_begin_end_and_hit_events(world, ground):
    ground_shape = ground.shapes[0]
    ground_shape.contact_events_enabled = True
    ground_shape.hit_events_enabled = True
    ball, shape = drop_ball(world, enable_contact_events=True, enable_hit_events=True)

    begins, hits = [], []
    for _ in range(120):
        world.step(1 / 60, 4)
        events = world.get_contact_events()
        begins += events.begin_events()
        hits += events.hit_events()
        assert events.begin_count == len(events.begin_events())

    assert begins, "no begin touch event"
    event = begins[0]
    assert {event.shape_a, event.shape_b} == {shape, ground_shape}
    assert isinstance(event.contact, b2d.Contact)

    assert hits, "no hit event"
    hit = hits[0]
    assert hit.approach_speed > 1.0
    assert hit.point[1] == approx(0.0, abs=0.1)
    assert len(hit.normal) == 2

    # lift the ball off the ground: end touch event (wake it: sleeping contacts are not updated)
    ball.set_transform((0, 10), 0)
    ball.awake = True
    ends = []
    for _ in range(5):
        world.step(1 / 60, 4)
        ends += world.get_contact_events().end_events()
    assert ends and {ends[0].shape_a, ends[0].shape_b} == {shape, ground_shape}


def test_contact_data(world, ground):
    ball, shape = drop_ball(world, height=0.5)
    step(world, 10)
    data = shape.contact_data[0]
    contact = data.contact
    assert contact.is_valid
    same = contact.data
    assert {same.shape_a, same.shape_b} == {data.shape_a, data.shape_b}
    manifold = data.manifold
    assert manifold.point_count >= 1
    assert len(manifold.points) == manifold.point_count
    point = manifold.points[0]
    assert point.total_normal_impulse >= 0
    assert manifold.normal == approx((0, 1), abs=1e-3) or manifold.normal == approx((0, -1), abs=1e-3)


def test_sensor_events(world):
    world.gravity = (0, -10)
    sensor_body = world.create_static_body(position=(0, 0))
    sensor = sensor_body.create_polygon_shape(b2d.shape_def(is_sensor=True, enable_sensor_events=True), b2d.box(2, 2))
    ball, visitor = drop_ball(world, height=4, enable_sensor_events=True)

    begins, ends = [], []
    for _ in range(120):
        world.step(1 / 60, 4)
        events = world.get_sensor_events()
        begins += events.begin_events()
        ends += events.end_events()

    assert begins and begins[0].sensor_shape == sensor and begins[0].visitor_shape == visitor
    assert ends and ends[0].sensor_shape == sensor


def test_body_move_events(world):
    bodies = [make_box_body(world, position=(2 * i, 5)) for i in range(5)]
    bodies[0].user_data = 77
    world.step(1 / 60, 4)
    events = world.get_body_events()
    assert events.move_count == 5

    moves = events.move_events()
    assert {m.body for m in moves} == set(bodies)
    first = next(m for m in moves if m.body == bodies[0])
    assert first.user_data == 77
    assert not first.fell_asleep
    assert first.transform.p == approx(tuple(bodies[0].position))

    # array form of the same data
    batch = events.bodies
    assert isinstance(batch, b2d.Bodies)
    assert len(batch) == 5
    transforms = events.transforms
    assert transforms.shape == (5, 4)
    assert transforms.dtype == np.float32
    np.testing.assert_allclose(transforms[:, :2], batch.position, rtol=1e-6)
    assert events.fell_asleep.dtype == np.bool_


def test_fell_asleep(world, ground):
    body = make_box_body(world, position=(0, 0.5))
    asleep = False
    for _ in range(600):
        world.step(1 / 60, 4)
        if any(m.fell_asleep and m.body == body for m in world.get_body_events().move_events()):
            asleep = True
            break
    assert asleep
