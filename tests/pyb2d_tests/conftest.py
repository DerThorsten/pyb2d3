import pytest
import pyb2d as b2d


@pytest.fixture
def world_id():
    world_def = b2d.world_def(gravity=(0, -10))
    world_id = b2d.create_world(world_def)
    yield world_id
    b2d.destroy_world(world_id)
