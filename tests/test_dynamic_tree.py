import pytest
from pytest import approx

import pyb2d3 as b2d


@pytest.fixture
def tree():
    tree = b2d.DynamicTree()
    for i in range(10):
        tree.create_proxy(b2d.aabb((i, 0), (i + 0.5, 0.5)), category_bits=1 << (i % 2), user_data=100 + i)
    return tree


def test_proxies(tree):
    assert tree.proxy_count == 10
    assert tree.height >= 1
    assert tree.area_ratio > 0
    assert tree.byte_count > 0
    root = tree.root_bounds
    assert root.lower_bound[0] <= 0 and root.upper_bound[0] >= 9.5
    tree.validate()


def test_overlap(tree):
    found = []
    tree.overlap_aabb(b2d.aabb((-1, -1), (2.1, 1)), lambda proxy_id, user_data: found.append(user_data))
    assert sorted(found) == [100, 101, 102]

    found = []
    tree.overlap_aabb(b2d.aabb((-1, -1), (2.1, 1)), lambda pid, ud: found.append(ud), mask_bits=2)
    assert found == [101]

    found = []
    tree.overlap_aabb_all(b2d.aabb((-1, -1), (2.1, 1)), lambda pid, ud: found.append(ud))
    assert sorted(found) == [100, 101, 102]


def test_cast_ray_and_box(tree):
    hits = []

    def on_ray(ray_input, proxy_id, user_data):
        hits.append(user_data)
        return ray_input.max_fraction

    tree.cast_ray(b2d.ray_cast_input(origin=(-1, 0.25), translation=(20, 0)), on_ray)
    assert sorted(hits) == list(range(100, 110))

    box_hits = []
    inp = b2d.BoxCastInput()
    inp.box = b2d.aabb((-1.2, 0), (-1, 0.2))
    inp.translation = (5, 0)
    inp.max_fraction = 1.0
    tree.cast_box(inp, lambda box_input, pid, ud: box_hits.append(ud))
    assert 100 in box_hits


def test_move_and_destroy(tree):
    proxy = tree.create_proxy(b2d.aabb((50, 50), (51, 51)), category_bits=1, user_data=7)
    assert tree.get_user_data(proxy) == 7
    assert tree.get_category_bits(proxy) == 1
    tree.set_category_bits(proxy, 4)
    assert tree.get_category_bits(proxy) == 4

    tree.move_proxy(proxy, b2d.aabb((60, 60), (61, 61)))
    bounds = tree.get_proxy_bounds(proxy)
    assert bounds.lower_bound == approx((60, 60), abs=0.5)

    tree.destroy_proxy(proxy)
    assert tree.proxy_count == 10
