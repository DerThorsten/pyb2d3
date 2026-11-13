import pytest
from pytest import approx

import numpy as np
import pyb2d3 as b2d

from .conftest import make_box_body, make_circle_body, step


@pytest.fixture
def body(world):
    return world.create_dynamic_body(position=(0, 0))


@pytest.mark.parametrize(
    "geometry, creator, cls, prop",
    [
        (b2d.circle(radius=0.5), "create_circle_shape", b2d.CircleShape, "circle"),
        (b2d.capsule((0, 0), (1, 0), 0.25), "create_capsule_shape", b2d.CapsuleShape, "capsule"),
        (b2d.segment((0, 0), (1, 0)), "create_segment_shape", b2d.SegmentShape, "segment"),
        (b2d.box(1, 1), "create_polygon_shape", b2d.PolygonShape, "polygon"),
    ],
)
def test_create_typed_shapes(body, geometry, creator, cls, prop):
    shape = getattr(body, creator)(b2d.shape_def(), geometry)
    assert isinstance(shape, cls)
    assert shape.is_valid
    assert shape.body == body
    assert shape.world == body.world
    assert isinstance(getattr(shape, prop), type(geometry))
    # generic creation goes through the same path
    assert isinstance(body.create_shape(b2d.shape_def(), geometry), cls)
    # untyped handle can be cast to the typed one
    assert isinstance(b2d.Shape(shape.id).cast(), cls)
    assert isinstance(b2d.get_casted_shape(shape.id), cls)


def test_shape_type_enum(body):
    shape = body.create_circle_shape(b2d.shape_def(), b2d.circle())
    assert shape.type == b2d.ShapeType.circle


def test_geometry_setter(body):
    shape = body.create_circle_shape(b2d.shape_def(), b2d.circle(radius=0.5))
    shape.circle = b2d.circle(center=(1, 0), radius=2)
    assert shape.circle.radius == approx(2)
    assert shape.circle.center == approx((1, 0))


def test_material(body):
    shape = body.create_polygon_shape(b2d.shape_def(density=1), b2d.box(1, 1))
    shape.friction = 0.25
    shape.restitution = 0.75
    shape.user_material = 7
    assert shape.friction == approx(0.25)
    assert shape.restitution == approx(0.75)
    assert shape.user_material == 7

    material = b2d.surface_material(friction=0.1, rolling_resistance=0.2, tangent_speed=1.0, custom_color=0xFF0000)
    shape.surface_material = material
    got = shape.surface_material
    assert got.friction == approx(0.1)
    assert got.rolling_resistance == approx(0.2)
    assert got.tangent_speed == approx(1.0)
    assert got.custom_color == 0xFF0000

    mass = body.mass
    shape.set_density(2.0)
    assert shape.density == approx(2.0)
    assert body.mass == approx(2 * mass)


def test_filter_and_flags(body):
    shape = body.create_circle_shape(b2d.shape_def(), b2d.circle())
    shape.filter = b2d.make_filter(category_bits=2, mask_bits=4, group_index=-1)
    f = shape.filter
    assert (f.category_bits, f.mask_bits, f.group_index) == (2, 4, -1)

    for flag in [
        "sensor_events_enabled",
        "contact_events_enabled",
        "pre_solve_events_enabled",
        "hit_events_enabled",
    ]:
        setattr(shape, flag, True)
        assert getattr(shape, flag) is True
        setattr(shape, flag, False)
        assert getattr(shape, flag) is False

    assert not shape.is_sensor
    sensor = body.create_circle_shape(b2d.shape_def(is_sensor=True), b2d.circle())
    assert sensor.is_sensor


def test_geometry_queries(world):
    body = make_box_body(world, position=(2, 0), hx=1, hy=1)
    shape = body.shapes[0]
    assert shape.test_point((2.5, 0.5))
    assert not shape.test_point((5, 5))

    out = shape.cast_ray((-5, 0), (10, 0))
    assert out.hit
    assert out.point == approx((1, 0), abs=1e-4)
    assert out.normal == approx((-1, 0), abs=1e-4)

    assert shape.closest_point((10, 0)) == approx((3, 0), abs=1e-4)

    bounds = shape.bounds
    assert bounds.lower_bound == approx((1, -1), abs=0.1)
    assert bounds.upper_bound == approx((3, 1), abs=0.1)

    md = shape.compute_mass_data()
    assert md.mass == approx(4)

    shape.apply_wind((10, 0), drag=1.0, lift=0.0)


def test_contacts_and_sensors(world, ground):
    sensor_def = b2d.shape_def(is_sensor=True, enable_sensor_events=True)
    sensor = ground.create_polygon_shape(sensor_def, b2d.box(2, 2, center=(0, 3), rotation=0))

    visitor = world.create_dynamic_body(position=(0, 3))
    visitor_shape = visitor.create_circle_shape(b2d.shape_def(enable_sensor_events=True), b2d.circle(radius=0.2))
    world.gravity = (0, 0)
    step(world, 2)
    assert sensor.sensor_capacity >= 1
    assert visitor_shape in sensor.sensor_overlaps

    world.gravity = (0, -10)
    resting = make_box_body(world, position=(5, 0.5))
    step(world, 60)
    shape = resting.shapes[0]
    assert shape.contact_capacity >= 1
    assert len(shape.contact_data) >= 1


def test_destroy_updates_mass(world):
    body = make_box_body(world)
    extra = body.create_circle_shape(b2d.shape_def(density=1), b2d.circle(radius=1))
    mass = body.mass
    extra.destroy()
    assert not extra.is_valid
    assert body.mass < mass
    assert body.shape_count == 1


def test_chain_segment_shape(world):
    ground = world.create_static_body()
    chain = ground.create_chain(b2d.chain_def(points=np.array([(0, 0), (1, 0), (2, 0), (3, 1)]), is_loop=False))
    segment = chain.segments[0]
    assert isinstance(segment, b2d.ChainSegmentShape)
    assert segment.parent_chain == chain
    cs = segment.chain_segment
    assert isinstance(cs, b2d.ChainSegment)
    assert segment.segment.point1 == approx(cs.segment.point1)

    # standalone chain segment shape
    body = world.create_static_body()
    new_cs = b2d.chain_segment(b2d.segment((0, 0), (1, 0)), ghost1=(-1, 0), ghost2=(2, 0))
    shape = body.create_shape(b2d.shape_def(), new_cs)
    assert isinstance(shape, b2d.ChainSegmentShape)
    assert shape.chain_segment.ghost1 == approx((-1, 0))
