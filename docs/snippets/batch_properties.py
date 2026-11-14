import numpy as np

import pyb2d3 as b2d

world = b2d.World(gravity=(0, 0))
n = 500
bodies = b2d.Bodies()
for i in range(n):
    body = world.create_dynamic_body(position=(i % 25, i // 25), rotation=b2d.make_rot(0.01 * i))
    body.create_shape(b2d.shape_def(density=1.0), b2d.box(0.3, 0.2))
    bodies.append(body)

# --- reading: one call, one numpy array ----------------------------------------------
positions = bodies.position  # (n, 2) float32
angles = bodies.angle  # (n,)
rotations = bodies.rotation  # (n, 2) as (cos, sin)
transforms = bodies.transform  # (n, 4) as (x, y, cos, sin)
masses = bodies.mass  # (n,)
print(positions.shape, angles.shape, rotations.shape, transforms.shape, masses.shape)
assert np.allclose(transforms[:, :2], positions)
assert np.allclose(rotations, np.stack([np.cos(angles), np.sin(angles)], axis=1), atol=1e-3)

# --- writing: one value per body ... -------------------------------------------------
phase = np.linspace(0, 2 * np.pi, n, endpoint=False)
bodies.linear_velocity = np.stack([np.cos(phase), np.sin(phase)], axis=1)  # (n, 2)
bodies.angular_velocity = np.linspace(-1, 1, n)  # (n,)

# ... or a single value for all of them (broadcast)
bodies.linear_damping = 0.5
bodies.gravity_scale = 2.0

# booleans and integers work the same way
bodies.bullet = np.arange(n) % 2 == 0
bodies.user_data = np.arange(n, dtype=np.uint64)  # e.g. an index into your own arrays

# teleport: set_transform takes positions (n, 2) and rotations (n, 2) as (cos, sin)
new_angles = np.zeros(n)
bodies.set_transform(positions + (0, 10), np.stack([np.cos(new_angles), np.sin(new_angles)], axis=1))
assert np.allclose(bodies.position[:, 1], positions[:, 1] + 10)

world.step(1 / 60, 4)
print("mean speed:", bodies.speed.mean())
