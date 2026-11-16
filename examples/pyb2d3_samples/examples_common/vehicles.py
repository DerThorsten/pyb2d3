"""Simple vehicles: a body on motor driven wheels, from light (car) to heavy (tank)."""

import pyb2d3 as b2d

from .joints import pinned

# name: (body boxes (half width, half height, center), density, wheel x positions,
#        wheel radius, motor torque, color)
VEHICLES = {
    "car": ([(1.2, 0.3, (0.0, 0.0))], 6.0, (-0.8, 0.8), 0.4, 60.0, b2d.HexColor.Crimson),
    "truck": (
        [(2.0, 0.35, (0.0, 0.0)), (0.6, 0.5, (1.4, 0.85))],
        7.5,
        (-1.4, 0.0, 1.4),
        0.45,
        200.0,
        b2d.HexColor.Orange,
    ),
    "tank": (
        [(2.2, 0.4, (0.0, 0.0)), (1.0, 0.35, (-0.3, 0.75)), (1.1, 0.08, (1.6, 0.8))],
        13.0,
        (-1.8, -0.9, 0.0, 0.9, 1.8),
        0.35,
        400.0,
        b2d.HexColor.DarkOliveGreen,
    ),
}


def create_vehicle(world, name, x, ground, shape_filter=b2d.make_filter(), speed=2.0, weight=1.0):
    """The vehicle `name` standing on `ground` at `x`, driving to the right with `speed`
    (m/s). `weight` scales its mass (and its motors, so it still climbs). Returns its
    bodies, the body first."""
    boxes, density, wheels, radius, torque, color = VEHICLES[name]
    density, torque = weight * density, weight * torque
    clearance = boxes[0][1] + 0.1  # wheel axles below the body
    body = world.create_dynamic_body(position=(x, ground + radius + clearance))
    body_def = b2d.shape_def(
        density=density, filter=shape_filter, material=b2d.surface_material(custom_color=color)
    )
    for hx, hy, center in boxes:
        body.create_shape(body_def, b2d.box(hx, hy, center=center))
    wheel_def = b2d.shape_def(
        density=2.0 * weight,
        filter=shape_filter,
        material=b2d.surface_material(friction=0.9, custom_color=b2d.HexColor.DimGray),
    )
    bodies = [body]
    for dx in wheels:
        wheel = world.create_dynamic_body(position=(x + dx, ground + radius))
        wheel.create_shape(wheel_def, b2d.circle(radius=radius))
        world.create_revolute_joint(
            **pinned(body, wheel, wheel.position),
            enable_motor=True,
            motor_speed=-speed / radius,  # clockwise: to the right
            max_motor_torque=torque,
        )
        bodies.append(wheel)
    return bodies
