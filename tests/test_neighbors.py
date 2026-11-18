"""b2d.extensions.neighbor_pairs: all pairs closer than a radius (pyb2d3 extension)."""

import numpy as np
import pytest

import pyb2d3 as b2d
from pyb2d3 import extensions as ext


def brute_force(positions, radius):
    pairs = set()
    for a in range(len(positions)):
        for b in range(a + 1, len(positions)):
            if np.linalg.norm(positions[b] - positions[a]) < radius:
                pairs.add((a, b))
    return pairs


@pytest.mark.parametrize("radius", [0.3, 1.0, 2.5])
def test_same_pairs_as_brute_force(radius):
    rng = np.random.default_rng(1)
    positions = rng.uniform(-5.0, 5.0, size=(300, 2))
    positions[:20] = np.round(positions[:20] / radius) * radius  # points on cell borders
    i, j, delta, distance = ext.neighbor_pairs(positions, radius)
    assert set(zip(i.tolist(), j.tolist())) == brute_force(positions, radius)
    assert len(set(zip(i.tolist(), j.tolist()))) == len(i)  # each pair once
    assert np.all(i < j)
    np.testing.assert_allclose(delta, positions[j] - positions[i])
    np.testing.assert_allclose(distance, np.linalg.norm(delta, axis=1))


def test_shapes_and_edge_cases():
    i, j, delta, distance = ext.neighbor_pairs(np.zeros((0, 2)), 1.0)
    assert len(i) == len(j) == len(distance) == 0
    assert delta.shape == (0, 2)
    i, j, _, distance = ext.neighbor_pairs([(0.0, 0.0), (0.5, 0.0), (3.0, 0.0)], 1.0)
    assert (i.tolist(), j.tolist(), distance.tolist()) == ([0], [1], [0.5])
    with pytest.raises(ValueError):
        ext.neighbor_pairs([(0.0, 0.0)], 0.0)


def test_bodies_neighbor_pairs():
    world = b2d.World(gravity=(0, 0))
    bodies = b2d.Bodies()
    for x in (0.0, 0.5, 3.0, 3.4):
        body = world.create_dynamic_body(position=(x, 1.0))
        body.create_shape(b2d.shape_def(), b2d.circle(radius=0.1))
        bodies.append(body)
    i, j, _, _ = bodies.neighbor_pairs(1.0)
    assert sorted(zip(i.tolist(), j.tolist())) == [(0, 1), (2, 3)]
