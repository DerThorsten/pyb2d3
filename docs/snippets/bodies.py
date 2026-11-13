import pyb2d3 as b2d

world = b2d.World(gravity=(0, 0))

# --- creating bodies ---------------------------------------------------------
# keyword arguments are the fields of b2d.BodyDef
body = world.create_dynamic_body(position=(1, 2), rotation=0.5, linear_damping=0.1, user_data=42)

# or build the def first (handy to create many similar bodies)
body_def = b2d.dynamic_body_def(position=(0, 0), fixed_rotation=True)
other = world.create_body(body_def, position=(3, 0))  # kwargs override the def

body.create_shape(b2d.shape_def(density=1), b2d.circle(radius=0.5))

# --- reading and writing state (plain properties) ----------------------------
print(body.position, body.angle, body.mass)
body.linear_velocity = (1, 0)
body.angular_velocity = 2.0
body.gravity_scale = 0.5
body.name = "player"  # box2d keeps at most b2d.NAME_LENGTH characters

# --- forces and impulses ------------------------------------------------------
body.apply_force_to_center((0, 10))
body.apply_linear_impulse((1, 0), point=body.world_point((0, 0.5)))
body.apply_torque(1.0)

# --- frames -------------------------------------------------------------------
local = body.local_point((2, 2))  # world -> body frame
assert b2d.distance(body.world_point(local), (2, 2)) < 1e-5

# --- kinematic bodies follow a target transform -------------------------------
platform = world.create_kinematic_body(position=(0, 0))
platform.set_target_transform(b2d.transform(p=(1, 0)), time_step=1 / 60)

# --- motion locks (fixed_rotation is a shorthand for angular_z) ----------------
other.motion_locks = b2d.MotionLocks(linear_x=False, linear_y=True, angular_z=True)

# --- identity -------------------------------------------------------------------
same = b2d.Body(body.id)  # wrappers are cheap views on a box2d id
assert same == body and hash(same) == hash(body)

body.destroy()
assert not body.is_valid
