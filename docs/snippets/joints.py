import math

import pyb2d3 as b2d

world = b2d.World(gravity=(0, -10))
ground = world.create_static_body(position=(0, 0))

wheel = world.create_dynamic_body(position=(0, 0))
wheel.create_shape(b2d.shape_def(density=1), b2d.circle(radius=0.5))

# --- creating joints ---------------------------------------------------------------
# create_<type>_joint(body_a, body_b, **def_fields)
motor = world.create_revolute_joint(ground, wheel, enable_motor=True, motor_speed=2.0, max_motor_torque=100)

# or from a def object (works for every joint type via world.create_joint)
arm = world.create_dynamic_body(position=(2, 0))
arm.create_shape(b2d.shape_def(density=1), b2d.box(1, 0.1))
hinge_def = b2d.revolute_joint_def(body_a=ground, body_b=arm)
hinge_def.local_anchor_a = (1, 0)  # shorthand for local_frame_a.p
hinge_def.local_anchor_b = (-1, 0)
hinge_def.enable_limit = True
hinge_def.lower_angle = -0.25 * math.pi
hinge_def.upper_angle = 0.25 * math.pi
hinge = world.create_joint(hinge_def)

# --- local frames (box2d >= 3.2) ----------------------------------------------------
# a joint connects frame A on body A with frame B on body B. The frame origin is the
# anchor; its rotation replaces the old reference angle and joint axis.
slider = world.create_dynamic_body(position=(-3, 0))
slider.create_shape(b2d.shape_def(density=1), b2d.box(0.5, 0.5))
prismatic = world.create_prismatic_joint(
    ground,
    slider,
    local_frame_a=b2d.transform(p=(-3, 0), q=0.25 * math.pi),  # slide along a 45 degree axis
    enable_limit=True,
    lower_translation=-1,
    upper_translation=1,
)

# --- runtime properties ----------------------------------------------------------------
for _ in range(60):
    world.step(1 / 60, 4)

print(motor.current_speed, motor.current_motor_torque)
motor.target_motor_speed = -2.0
hinge.set_limits(-0.5, 0.5)
print(hinge.current_angle, prismatic.current_translation)
print(motor.constraint_force, motor.constraint_torque)

# every joint is typed; the generic base class can be cast
assert isinstance(b2d.Joint(hinge.id).cast(), b2d.RevoluteJoint)

# --- dragging bodies with the mouse ----------------------------------------------------
# box2d >= 3.2 has no mouse joint: MouseDrag uses a kinematic body + motor joint
drag = b2d.MouseDrag(world)
if drag.begin(slider.position):  # mouse down
    drag.update((0, 2))  # mouse move
    for _ in range(30):
        drag.step(1 / 60)  # once per step, before world.step
        world.step(1 / 60, 4)
    drag.end()  # mouse up
