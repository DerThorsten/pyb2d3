import numpy as np

import pyb2d3 as b2d

world = b2d.World(gravity=(0, -10))
anchor = world.create_static_body(position=(0, 10))

# a hanging chain of 20 links
links = []
previous = anchor
for i in range(20):
    link = world.create_dynamic_body(position=(0.5 + i, 10))
    link.create_shape(b2d.shape_def(density=1.0), b2d.capsule((-0.5, 0), (0.5, 0), 0.1))
    anchor_a = (0, 0) if previous is anchor else (0.5, 0)
    world.create_revolute_joint(previous, link, local_anchor_a=anchor_a, local_anchor_b=(-0.5, 0))
    links.append(link)
    previous = link

# --- Shapes: material properties of many shapes at once ------------------------------
shapes = b2d.Shapes(shape for link in links for shape in link.shapes)
shapes.friction = np.linspace(0.2, 1.0, len(shapes))
shapes.restitution = 0.1
print("densities:", shapes.density)

# shapes come back as their concrete type
assert isinstance(shapes[0], b2d.CapsuleShape)

# per-shape queries: which shapes contain a point?
inside = shapes.test_point((0.5, 10.0))
assert inside[0] and not inside[-1]

# --- Joints: read the constraint forces of all joints after a step -------------------
joints = b2d.Joints(joint for link in links for joint in link.joints)
joints = b2d.Joints(np.unique(joints.ids))  # every joint is attached to two links
for _ in range(30):
    world.step(1 / 60, 4)
forces = np.linalg.norm(joints.constraint_force, axis=1)  # (n,)
print("joint forces:", np.round(forces, 1))
assert isinstance(joints[0], b2d.RevoluteJoint)

# e.g. find the most loaded joint; joints near the anchor carry the most weight
print("most loaded joint:", joints[np.argmax(forces)])
