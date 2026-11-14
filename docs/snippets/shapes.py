import numpy as np

import pyb2d3 as b2d

world = b2d.World()
body = world.create_dynamic_body(position=(0, 0))

# --- geometry ------------------------------------------------------------------
circle = b2d.circle(center=(0, 0), radius=0.5)
capsule = b2d.capsule((-0.5, 0), (0.5, 0), radius=0.25)
segment = b2d.segment((-1, 0), (1, 0))
box = b2d.box(1.0, 0.5)  # half width, half height
rotated_box = b2d.box(1.0, 0.5, center=(2, 0), rotation=0.3)
rounded_box = b2d.box(1.0, 0.5, radius=0.1)
hexagon = b2d.polygon(points=[(np.cos(a), np.sin(a)) for a in np.linspace(0, 2 * np.pi, 6, endpoint=False)])

# --- shape definitions -----------------------------------------------------------
material = b2d.surface_material(friction=0.4, restitution=0.2, rolling_resistance=0.05)
shape_def = b2d.shape_def(density=2.0, material=material, enable_contact_events=True)

# create_shape dispatches on the geometry type and returns a typed shape
shape = body.create_shape(shape_def, box)
assert isinstance(shape, b2d.PolygonShape)
shapes = body.create_shapes(shape_def, [circle, capsule])

# --- shape properties ----------------------------------------------------------------
shape.friction = 0.8
shape.filter = b2d.make_filter(category_bits=0x2, mask_bits=0xFFFF)
shape.set_density(3.0)  # updates the body mass
print(shape.bounds, shape.compute_mass_data().mass)
assert shape.test_point(body.world_point((0.5, 0)))

# typed access to the geometry
poly = shape.polygon
print(poly.vertices)  # (n, 2) numpy array

# --- sensors ----------------------------------------------------------------------------
sensor = body.create_shape(b2d.shape_def(is_sensor=True, enable_sensor_events=True), b2d.circle(radius=3))

# --- chains: one-sided polylines, ideal for terrain -----------------------------------------
ground = world.create_static_body()
points = np.array([(-10, 0), (-5, 1), (0, 0), (5, 1), (10, 0)])
chain = ground.create_chain(b2d.chain_def(points=points, material=b2d.surface_material(friction=0.9)))
print(chain.segment_count, chain.segments[0].chain_segment)
chain.set_surface_material(b2d.surface_material(friction=0.1), segment_index=0)
