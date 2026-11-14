import numpy as np

import pyb2d3 as b2d

world = b2d.World(gravity=(0, -10))
ground = world.create_static_body(position=(0, -1))
ground.create_shape(b2d.shape_def(), b2d.box(20, 1))

body_list = []
for i in range(100):
    body = world.create_dynamic_body(position=(i % 10 - 4.5, 1 + i // 10))
    body.create_shape(b2d.shape_def(), b2d.box(0.4, 0.4))
    body_list.append(body)

# from a list (or any iterable) of bodies
bodies = b2d.Bodies(body_list)
assert len(bodies) == 100

# from a uint64 id array, e.g. one stored earlier in a numpy array
same = b2d.Bodies(bodies.ids)
assert np.array_equal(same.ids, bodies.ids)

# grow a batch one body at a time
grown = b2d.Bodies()
for body in body_list[:10]:
    grown.append(body)
assert len(grown) == 10

# from a world query: all bodies with a shape in a box
found = []
world.overlap_aabb(b2d.aabb(lower_bound=(-5, 0), upper_bound=(5, 3)), lambda shape: found.append(shape.body))
in_box = b2d.Bodies(b for b in found if b.type == b2d.BodyType.DYNAMIC)
print("bodies in the box:", len(in_box))

# from the body move events: every body that moved during the last step
world.step(1 / 60, 4)
moved = world.get_body_events().bodies  # already a Bodies batch
print("moved:", len(moved), "first:", moved[0])
assert len(moved) == 100
