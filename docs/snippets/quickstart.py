import pyb2d3 as b2d

# a world with gravity pointing down
world = b2d.World(gravity=(0, -10))

# a static ground box (half width 50, half height 1)
ground = world.create_static_body(position=(0, -1))
ground.create_shape(b2d.shape_def(), b2d.box(50, 1))

# a dynamic box falling onto it
body = world.create_dynamic_body(position=(0, 4))
body.create_shape(b2d.shape_def(density=1, material=b2d.surface_material(friction=0.6)), b2d.box(0.5, 0.5))

# simulate one second at 60 Hz with 4 sub-steps
for _ in range(60):
    world.step(1 / 60, 4)

x, y = body.position
print(f"box at ({x:.2f}, {y:.2f}), angle {body.angle:.2f}")
