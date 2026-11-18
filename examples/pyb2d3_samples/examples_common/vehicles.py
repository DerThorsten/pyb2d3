"""Simple vehicles: a body on motor driven wheels, from light (car) to heavy (tank)."""

from collections import namedtuple

import pyb2d3 as b2d

# boxes: the parts of the body, (half width, half height, center) each
# wheels: x positions of the wheel axles relative to the body
Vehicle = namedtuple("Vehicle", "boxes density wheels wheel_radius motor_torque color")

VEHICLES = {
    "car": Vehicle(
        boxes=[(1.2, 0.3, (0.0, 0.0))],
        density=6.0,
        wheels=(-0.8, 0.8),
        wheel_radius=0.4,
        motor_torque=60.0,
        color=b2d.HexColor.Crimson,
    ),
    "truck": Vehicle(
        boxes=[(2.0, 0.35, (0.0, 0.0)), (0.6, 0.5, (1.4, 0.85))],  # bed and cab
        density=7.5,
        wheels=(-1.4, 0.0, 1.4),
        wheel_radius=0.45,
        motor_torque=200.0,
        color=b2d.HexColor.Orange,
    ),
    "tank": Vehicle(
        boxes=[(2.2, 0.4, (0.0, 0.0)), (1.0, 0.35, (-0.3, 0.75)), (1.1, 0.08, (1.6, 0.8))],
        density=13.0,
        wheels=(-1.8, -0.9, 0.0, 0.9, 1.8),
        wheel_radius=0.35,
        motor_torque=400.0,
        color=b2d.HexColor.DarkOliveGreen,
    ),
}


def create_vehicle(world, name, x, ground, shape_filter=b2d.make_filter(), speed=2.0, weight=1.0):
    """The vehicle `name` standing on `ground` (its height) at `x`, driving to the right
    with `speed` (m/s). `weight` scales its mass and its motors (so it still climbs).
    Returns its bodies, the body first, then the wheels."""
    v = VEHICLES[name]
    r = v.wheel_radius
    clearance = v.boxes[0][1] + 0.1  # the wheel axles are a bit below the body

    body = world.create_dynamic_body(position=(x, ground + r + clearance))
    body_def = b2d.shape_def(
        density=weight * v.density,
        filter=shape_filter,
        material=b2d.surface_material(custom_color=v.color),
    )
    for hx, hy, center in v.boxes:
        body.create_shape(body_def, b2d.box(hx, hy, center=center))

    wheel_def = b2d.shape_def(
        density=2.0 * weight,
        filter=shape_filter,
        material=b2d.surface_material(friction=0.9, custom_color=b2d.HexColor.DimGray),
    )
    bodies = [body]
    for dx in v.wheels:
        wheel = world.create_dynamic_body(position=(x + dx, ground + r))
        wheel.create_shape(wheel_def, b2d.circle(radius=r))
        # the axle at the wheel center (the origin of the wheel body)
        world.create_revolute_joint(
            body_a=body,
            body_b=wheel,
            local_anchor_a=body.local_point(wheel.position),
            enable_motor=True,
            motor_speed=-speed / r,  # clockwise: to the right
            max_motor_torque=weight * v.motor_torque,
        )
        bodies.append(wheel)
    return bodies
