import numpy as np

import pyb2d3 as b2d

world = b2d.World(gravity=(0, -10))
body_list = []
for i in range(100):
    body = world.create_dynamic_body(position=(i % 10, i // 10))
    body.create_shape(b2d.shape_def(), b2d.circle(radius=0.3))
    body_list.append(body)
bodies = b2d.Bodies(body_list)

# an integer gives a single Body
first = bodies[0]
assert first == body_list[0]
assert isinstance(first, b2d.Body)

# slices, index arrays and boolean masks give a new batch (no copies of the bodies)
every_other = bodies[::2]
picked = bodies[np.array([3, 14, 15])]
assert len(every_other) == 50 and len(picked) == 3

# masks from the batch's own arrays: the classic numpy pattern
positions = bodies.position
left_half = bodies[positions[:, 0] < 5]
top_left = bodies[(positions[:, 0] < 5) & (positions[:, 1] >= 5)]
assert len(left_half) == 50 and len(top_left) == 25

top_left.gravity_scale = -1.0  # sub batches support everything a batch does
top_left.awake = True

# the indices of the selected bodies, e.g. to update your own per-body arrays
colors = np.zeros(len(bodies), dtype=np.uint32)
colors[np.flatnonzero(positions[:, 1] >= 5)] = 0xFF0000

# iterating yields Body objects (one python object per body: fine for small batches)
for body in picked:
    print(body, body.position)
