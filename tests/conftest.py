import pytest

import pyb2d3 as b2d


def make_box_body(world, position=(0, 0), hx=0.5, hy=0.5, density=1.0, body_type=b2d.BodyType.DYNAMIC, **kwargs):
    """A body with a single box shape."""
    body = world.create_body(type=body_type, position=position, **kwargs)
    body.create_polygon_shape(b2d.shape_def(density=density), b2d.box(hx, hy))
    return body


def make_circle_body(world, position=(0, 0), radius=0.5, density=1.0, body_type=b2d.BodyType.DYNAMIC, **kwargs):
    body = world.create_body(type=body_type, position=position, **kwargs)
    body.create_circle_shape(b2d.shape_def(density=density), b2d.circle(radius=radius))
    return body


def step(world, n=60, dt=1 / 60, sub_steps=4):
    for _ in range(n):
        world.step(dt, sub_steps)


@pytest.fixture
def world():
    return b2d.World(gravity=(0, -10))


@pytest.fixture
def ground(world):
    """A wide static box with its top surface at y=0."""
    return make_box_body(world, position=(0, -1), hx=50, hy=1, body_type=b2d.BodyType.STATIC)


@pytest.fixture
def box_body(world):
    return make_box_body(world, position=(0, 5))


@pytest.fixture
def two_bodies(world):
    a = make_box_body(world, position=(-1, 5))
    b = make_box_body(world, position=(1, 5))
    return a, b
