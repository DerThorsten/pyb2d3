import numpy as np

import pyb2d3 as b2d

world = b2d.World(gravity=(0, -10))
n = 300
half = 0.5
bodies = b2d.Bodies()
for i in range(n):
    body = world.create_dynamic_body(position=(i % 30, i // 30), rotation=b2d.make_rot(0.1 * i))
    body.create_shape(b2d.shape_def(), b2d.box(half, half))
    bodies.append(body)

# the corners of every box in world coordinates: one batch call per corner
corners_local = [(-half, -half), (half, -half), (half, half), (-half, half)]
corners = np.stack([bodies.world_point(c) for c in corners_local], axis=1)  # (n, 4, 2)
print(corners.shape)

# ... which is the same as rotating and translating with the (n, 4) transforms
x, y, c, s = bodies.transform.T
cx, cy = corners_local[2]
assert np.allclose(corners[:, 2, 0], x + c * cx - s * cy, atol=1e-5)
assert np.allclose(corners[:, 2, 1], y + s * cx + c * cy, atol=1e-5)

# to pixels for a renderer (y axis pointing down)
ppm, canvas_height = 20.0, 600
pixels = corners * ppm
pixels[..., 1] = canvas_height - pixels[..., 1]

# the other way round: a world point (e.g. the mouse) in every body's frame
mouse = (12.0, 4.0)
local = bodies.local_point(mouse)  # (n, 2)
under_mouse = bodies[(np.abs(local) <= half).all(axis=1)]
print("bodies under the mouse:", list(under_mouse))
assert len(under_mouse) <= 1

# direction vectors: the local x axis of every body in world coordinates
x_axes = bodies.world_vector((1.0, 0.0))
assert np.allclose(x_axes, bodies.rotation, atol=1e-6)
