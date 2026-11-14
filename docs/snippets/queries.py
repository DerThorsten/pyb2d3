import pyb2d3 as b2d

world = b2d.World()
for i in range(5):
    body = world.create_static_body(position=(2 * i, 0))
    body.create_shape(b2d.shape_def(), b2d.box(0.5, 0.5))

# --- overlap queries: the callback returns False to stop, anything else continues ---
found = []
world.overlap_aabb(b2d.aabb((-1, -1), (5, 1)), lambda shape: found.append(shape))

# --- ray casts ------------------------------------------------------------------------
result = world.cast_ray_closest(origin=(-5, 0), translation=(20, 0))
if result.hit:
    print(result.shape.body, result.point, result.normal, result.fraction)


def on_hit(shape, point, normal, fraction):
    print("ray hit", shape, point)
    return fraction  # clip the ray: only closer hits are reported afterwards


world.cast_ray((-5, 0), (20, 0), on_hit)

# --- shape casts and movers ---------------------------------------------------------------
proxy = b2d.make_proxy([(0, 0)], radius=0.25)  # a circle of radius 0.25
world.cast_shape(proxy, translation=(20, 0), callback=lambda *hit: 1.0, origin=(-5, 0))
mover = b2d.capsule((0, 0), (0, 1), 0.25)
fraction = world.cast_mover(mover, translation=(0, -5), origin=(0, 2))

# --- filters --------------------------------------------------------------------------
only_category_2 = b2d.make_query_filter(category_bits=0x1, mask_bits=0x2)
world.overlap_aabb(b2d.aabb((-1, -1), (9, 1)), found.append, query_filter=only_category_2)

# --- convenience -------------------------------------------------------------------------
print(world.body_at_point((4, 0)), world.dynamic_body_at_point((4, 0)))

# exceptions raised in a callback stop the query and propagate
try:
    world.overlap_aabb(b2d.aabb((-1, -1), (9, 1)), lambda shape: 1 / 0)
except ZeroDivisionError:
    pass
