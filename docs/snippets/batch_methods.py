import numpy as np

import pyb2d3 as b2d

world = b2d.World(gravity=(0, 0))
n = 200
bodies = b2d.Bodies()
for i in range(n):
    body = world.create_dynamic_body(position=(i % 20, i // 20))
    body.create_shape(b2d.shape_def(density=1.0), b2d.circle(radius=0.4))
    bodies.append(body)
masses = bodies.mass

# a single argument is broadcast: the same impulse for every body
bodies.apply_linear_impulse_to_center((1.0, 0.0))

# one argument per body: impulses proportional to the mass -> the same velocity change
bodies.apply_linear_impulse_to_center(np.stack([np.zeros(n), masses], axis=1))
velocities = bodies.linear_velocity
assert np.allclose(velocities[:, 1], 1.0)

# arguments can be mixed: per-body forces at one shared point (in world coordinates) ...
forces = np.random.default_rng(0).normal(size=(n, 2)).astype(np.float32)
bodies.apply_force(forces, (10.0, 5.0))

# ... or per-body points, and a broadcast keyword argument
bodies.apply_force(forces, bodies.world_center, wake=False)
bodies.apply_torque(np.linspace(-1, 1, n))

# methods with a result return an array, e.g. the velocity of a point on every body
tips = bodies.world_point((0.4, 0.0))  # (n, 2)
tip_velocities = bodies.world_point_velocity(tips)  # (n, 2)
print(tip_velocities.shape)

world.step(1 / 60, 4)
bodies.clear_forces()  # no arguments: called on every body
