import numpy as np

import pyb2d3 as b2d

world = b2d.World(gravity=(0, -10))
body_list = []
for i in range(1000):
    body = world.create_dynamic_body(position=(i % 50, i // 50))
    body.create_shape(b2d.shape_def(), b2d.circle(radius=0.4))
    body_list.append(body)

# a batch is an array of ids
bodies = b2d.Bodies(body_list)
print(len(bodies), bodies.ids.dtype)  # 1000 uint64

# properties read and write numpy arrays (one call into C++ for all bodies)
positions = bodies.position  # (1000, 2) float32
bodies.linear_velocity = np.random.uniform(-1, 1, size=(1000, 2))
bodies.angular_velocity = 0.0  # a single value is broadcast

# methods work the same way: one argument per body, or a single broadcast value
bodies.apply_force_to_center((0, 20))
corners = bodies.world_point((0.4, 0))  # (1000, 2): the same local point on every body

# numpy indexing creates sub batches
high = bodies[bodies.position[:, 1] > 10]
high.awake = False
first = bodies[0]  # a single Body

# shapes and joints have batches as well
shapes = b2d.Shapes([b.shapes[0] for b in body_list])
shapes.friction = np.linspace(0.1, 1.0, len(shapes))
