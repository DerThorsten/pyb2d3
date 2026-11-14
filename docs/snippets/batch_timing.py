import timeit

import numpy as np

import pyb2d3 as b2d

n = 2000
target = np.array([25.0, 20.0])


def make_world():
    world = b2d.World(gravity=(0, 0))
    body_list = []
    for i in range(n):
        body = world.create_dynamic_body(position=(i % 50, i // 50))
        body.create_shape(b2d.shape_def(), b2d.circle(radius=0.3))
        body_list.append(body)
    return world, body_list


def pull_loop(body_list):
    # one python iteration and three calls into C++ per body
    for body in body_list:
        p = body.position
        body.apply_force_to_center(((target[0] - p.x) * body.mass, (target[1] - p.y) * body.mass))


def pull_batch(bodies):
    # three calls into C++ in total
    bodies.apply_force_to_center((target - bodies.position) * bodies.mass[:, None])


world, body_list = make_world()
bodies = b2d.Bodies(body_list)
loop_ms = 1000 * min(timeit.repeat(lambda: pull_loop(body_list), number=1, repeat=5))
batch_ms = 1000 * min(timeit.repeat(lambda: pull_batch(bodies), number=1, repeat=5))
print(f"{n} bodies: python loop {loop_ms:.2f} ms, batch {batch_ms:.3f} ms ({loop_ms / batch_ms:.0f}x faster)")

# both apply the same forces
world_a, list_a = make_world()
pull_loop(list_a)
world_a.step(1 / 60, 4)

world_b, list_b = make_world()
pull_batch(b2d.Bodies(list_b))
world_b.step(1 / 60, 4)

assert np.allclose(b2d.Bodies(list_a).linear_velocity, b2d.Bodies(list_b).linear_velocity)
