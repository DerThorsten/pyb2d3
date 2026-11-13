from pytest import approx

import numpy as np
import pyb2d3 as b2d

from .conftest import make_circle_body, step


POINTS = np.array([(-10, 0), (10, 0), (10, 10), (-10, 10)], dtype=np.float32)


def test_chain_def():
    material = b2d.surface_material(friction=0.3)
    d = b2d.chain_def(points=POINTS, material=material, is_loop=True, filter=b2d.make_filter(category_bits=2))
    assert d.points.shape == (4, 2)
    assert d.points == approx(POINTS)
    assert d.is_loop
    assert d.filter.category_bits == 2
    assert len(d.materials) == 1
    assert d.materials[0].friction == approx(0.3)
    d.enable_sensor_events = True
    d.user_data = 5
    assert d.enable_sensor_events and d.user_data == 5

    # copies own their points
    c = d.copy()
    d.points = POINTS[:3]
    assert c.points.shape == (4, 2)


def test_create_chain(world):
    ground = world.create_static_body()
    chain = ground.create_chain(b2d.chain_def(points=POINTS, is_loop=True))
    assert chain.is_valid
    assert chain.world == world
    assert chain.segment_count == 4
    segments = chain.segments
    assert len(segments) == 4
    assert all(isinstance(s, b2d.ChainSegmentShape) for s in segments)
    assert all(s.parent_chain == chain for s in segments)
    assert b2d.Chain(chain.id) == chain


def test_surface_materials(world):
    ground = world.create_static_body()
    chain = ground.create_chain(b2d.chain_def(points=POINTS, is_loop=True))

    chain.set_all_surface_materials(b2d.surface_material(friction=0.1))
    assert all(chain.get_surface_material(i).friction == approx(0.1) for i in range(4))

    chain.set_surface_material(b2d.surface_material(restitution=0.9), 2)
    assert chain.get_surface_material(2).restitution == approx(0.9)
    assert chain.get_surface_material(1).restitution == approx(0.0)


def test_per_segment_materials(world):
    materials = [b2d.surface_material(friction=0.1 * (i + 1)) for i in range(4)]
    ground = world.create_static_body()
    chain = ground.create_chain(b2d.chain_def(points=POINTS, materials=materials, is_loop=True))
    for i in range(4):
        assert chain.get_surface_material(i).friction == approx(0.1 * (i + 1))


def test_chain_collides(world):
    ground = world.create_static_body()
    ground.create_chain(b2d.chain_def(points=POINTS[[1, 0]], is_loop=False))
    ball = make_circle_body(world, position=(0, 2))
    step(world, 120)
    assert ball.position[1] == approx(0.5, abs=0.05)


def test_destroy(world):
    ground = world.create_static_body()
    chain = ground.create_chain(b2d.chain_def(points=POINTS, is_loop=True))
    segment = chain.segments[0]
    chain.destroy()
    assert not chain.is_valid
    assert not segment.is_valid


def test_destroy_with_body(world):
    ground = world.create_static_body()
    chain = ground.create_chain(b2d.chain_def(points=POINTS, is_loop=True))
    ground.destroy()
    assert not chain.is_valid
    chain.destroy()  # stale: no-op
