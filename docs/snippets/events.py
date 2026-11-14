import pyb2d3 as b2d

world = b2d.World(gravity=(0, -10))
ground = world.create_static_body(position=(0, -1))
ground_shape = ground.create_shape(b2d.shape_def(enable_contact_events=True, enable_hit_events=True), b2d.box(20, 1))

sensor_body = world.create_static_body(position=(0, 3))
sensor_body.create_shape(b2d.shape_def(is_sensor=True, enable_sensor_events=True), b2d.box(1, 1))

ball = world.create_dynamic_body(position=(0, 6))
ball.create_shape(
    b2d.shape_def(enable_contact_events=True, enable_hit_events=True, enable_sensor_events=True),
    b2d.circle(radius=0.25),
)

for _ in range(120):
    world.step(1 / 60, 4)

    # events are valid until the next step
    contacts = world.get_contact_events()
    for event in contacts.begin_events():
        print("begin touch", event.shape_a.body, event.shape_b.body)
    for hit in contacts.hit_events():
        print("hit with speed", hit.approach_speed, "at", hit.point)

    sensors = world.get_sensor_events()
    for event in sensors.begin_events():
        print("entered sensor:", event.visitor_shape.body)

    # bodies that moved this step; the arrays are the cheapest way to sync rendering
    moved = world.get_body_events()
    ids, transforms = moved.bodies.ids, moved.transforms  # (n,) uint64, (n, 4) [x, y, cos, sin]

# joints report when their force / torque exceeds a threshold
joint = world.create_weld_joint(ground, ball)
joint.force_threshold = 0.0
world.step(1 / 60, 4)
for event in world.get_joint_events().events():
    print("joint over threshold:", event.joint)

# current contacts of a body / shape
for data in ball.contact_data:
    print(data.shape_a, data.shape_b, data.manifold.point_count)
