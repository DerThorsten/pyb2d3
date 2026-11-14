"""A tank with real tracks: ~60 chain links wrapped around suspended road wheels and driven by
sprocket motors, an elevating gun that fires explosive shells, and terrain to drive over.

Keys: a / d drive, w / s raise / lower the gun, space fires, r puts a flipped tank back on its tracks.
"""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .examples_common.joints import pinned

# collision categories: the tank parts only touch what they have to
WORLD, HULL, WHEEL, TRACK, SHELL, DEBRIS = (1 << i for i in range(6))


def collision_filter(category, mask, group_index=0):
    return b2d.make_filter(category_bits=category, mask_bits=mask, group_index=group_index)


def convex_hull(points):
    """Counter-clockwise convex hull (monotone chain), for any number of points."""

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def half(points):
        chain = []
        for p in points:
            while len(chain) >= 2 and cross(chain[-2], chain[-1], p) <= 0:
                chain.pop()
            chain.append(p)
        return chain

    points = sorted(map(tuple, points))
    return np.array(half(points)[:-1] + half(reversed(points))[:-1])


def resample_loop(polygon, spacing):
    """Points evenly spaced along a closed polygon."""
    closed = np.vstack([polygon, polygon[:1]])
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(closed, axis=0), axis=1))])
    s = np.linspace(0.0, arc[-1], int(round(arc[-1] / spacing)), endpoint=False)
    return np.stack([np.interp(s, arc, closed[:, 0]), np.interp(s, arc, closed[:, 1])], axis=1)


def terrain_height(x):
    """Rolling hills, a crater, a jump ramp, a rough stretch and a big hill."""

    def bump(x0, x1, height):
        t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
        return height * np.sin(np.pi * t) ** 2

    h = bump(20, 40, 1.5) + bump(40, 60, 2.0) - bump(70, 86, 2.5) + bump(215, 265, 7.0)
    h += np.where((x >= 95) & (x < 105), 0.35 * (x - 95), 0.0)
    h += np.where((x >= 115) & (x < 150), 0.3 * np.abs(np.sin(np.pi * (x - 115) / 1.5)), 0.0)
    return h


class Tank:
    # hull and turret outlines (local coordinates, the tank faces +x)
    hull_outline = [(-3.6, 0.35), (3.6, 0.35), (4.0, 0.9), (3.3, 1.3), (-3.4, 1.3), (-3.8, 0.8)]
    turret_outline = [(-1.6, 1.3), (1.0, 1.3), (1.5, 1.7), (1.1, 2.1), (-1.4, 2.1), (-1.8, 1.7)]
    # (center, radius) of the wheels the track wraps around
    sprocket = ((-3.15, -0.1), 0.5)
    idler = ((3.2, -0.1), 0.45)
    road_wheels = [((x, -0.75), 0.4) for x in (-2.2, -1.1, 0.0, 1.1, 2.2)]
    return_rollers = [((x, 0.05), 0.14) for x in (-1.3, 1.3)]
    gun_pivot = (1.3, 1.75)
    barrel_length = 3.4
    link_radius = 0.09
    link_spacing = 0.3

    def __init__(self, world, position, motor_torque):
        self.world = world
        origin = b2d.Vec2(position)
        hull_filter = collision_filter(HULL, WORLD | DEBRIS)

        self.wheels = []
        self.hull = world.create_dynamic_body(position=origin)
        hull_def = b2d.shape_def(density=2.0, filter=hull_filter, material=b2d.surface_material(friction=0.6))
        for outline in (self.hull_outline, self.turret_outline):
            self.hull.create_shape(hull_def, b2d.polygon(points=outline))

        # sprocket and idler: plain revolute motors; road wheels: motors on sprung wheel joints
        wheel_def = b2d.shape_def(
            density=1.5,
            filter=collision_filter(WHEEL, WORLD | TRACK | DEBRIS),
            material=b2d.surface_material(friction=1.2),
        )
        self.motors = []
        for center, radius in (self.sprocket, self.idler):
            wheel = self.create_wheel(origin + center, radius, wheel_def)
            self.motors.append(
                world.create_revolute_joint(
                    **pinned(self.hull, wheel, wheel.position), enable_motor=True, max_motor_torque=motor_torque
                )
            )
        for center, radius in self.road_wheels:
            wheel = self.create_wheel(origin + center, radius, wheel_def)
            self.motors.append(
                world.create_wheel_joint(
                    # the suspension axis is the x-axis of frame A: rotate it upright
                    **pinned(self.hull, wheel, wheel.position, q_a=0.5 * math.pi),
                    enable_spring=True,
                    hertz=4.0,
                    damping_ratio=0.7,
                    enable_limit=True,
                    lower_translation=-0.25,
                    upper_translation=0.2,
                    enable_motor=True,
                    max_motor_torque=0.5 * motor_torque,
                )
            )
        for center, radius in self.return_rollers:
            roller = self.create_wheel(origin + center, radius, wheel_def)
            world.create_revolute_joint(**pinned(self.hull, roller, roller.position))

        self.links = self.create_track(origin)
        self.barrel = self.create_gun(origin)

    def create_wheel(self, position, radius, shape_def):
        wheel = self.world.create_dynamic_body(position=position, allow_fast_rotation=True)
        wheel.create_shape(shape_def, b2d.circle(radius=radius))
        self.wheels.append(wheel)
        return wheel

    @property
    def bodies(self):
        return [self.hull, *self.wheels, *self.links, self.barrel]

    def recover(self, surface_y):
        """Put the tank back on its tracks: every part moves rigidly with the hull to an upright
        pose above `surface_y`."""
        hull_transform = self.hull.transform
        target = b2d.transform(p=(hull_transform.p.x, surface_y + 2.0), q=0.0)
        for body in self.bodies:
            relative = b2d.inv_mul_transforms(hull_transform, body.transform)
            moved = b2d.mul_transforms(target, relative)
            body.set_transform(moved.p, moved.q)
            body.linear_velocity = (0.0, 0.0)
            body.angular_velocity = 0.0
            body.awake = True

    def create_track(self, origin):
        # the track runs along the convex envelope of all wheels, offset by the link radius
        angles = np.linspace(0.0, 2.0 * np.pi, 48, endpoint=False)
        circle = np.stack([np.cos(angles), np.sin(angles)], axis=1)
        wheels = [self.sprocket, self.idler, *self.road_wheels, *self.return_rollers]
        samples = np.concatenate(
            [np.array(center) + (radius + self.link_radius + 0.01) * circle for center, radius in wheels]
        )
        points = resample_loop(convex_hull(samples), self.link_spacing) + np.array(origin)

        link_def = b2d.shape_def(
            density=4.0,
            # links never collide with each other (same negative group)
            filter=collision_filter(TRACK, WORLD | WHEEL | DEBRIS, group_index=-1),
            material=b2d.surface_material(friction=1.0),
        )
        links = []
        for p, q in zip(points, np.roll(points, -1, axis=0)):
            half_length = 0.5 * np.linalg.norm(q - p)
            angle = math.atan2(q[1] - p[1], q[0] - p[0])
            link = self.world.create_dynamic_body(position=0.5 * (p + q), rotation=b2d.make_rot(angle))
            link.create_shape(link_def, b2d.capsule((-half_length, 0.0), (half_length, 0.0), self.link_radius))
            links.append(link)
        # chain the links into a closed loop
        for i, (a, b) in enumerate(zip(links, links[1:] + links[:1])):
            self.world.create_revolute_joint(**pinned(a, b, points[(i + 1) % len(points)]))
        return links

    def create_gun(self, origin):
        pivot = origin + self.gun_pivot
        barrel = self.world.create_dynamic_body(position=pivot)
        barrel.create_shape(
            b2d.shape_def(density=1.0, filter=collision_filter(HULL, WORLD | DEBRIS)),
            b2d.box(0.5 * self.barrel_length, 0.1, center=(0.5 * self.barrel_length, 0.0)),
        )
        self.gun = self.world.create_revolute_joint(
            **pinned(self.hull, barrel, pivot),
            enable_limit=True,
            lower_angle=-0.1,
            upper_angle=0.55,
            enable_motor=True,
            max_motor_torque=800.0,
        )
        return barrel

    @property
    def position(self):
        return self.hull.position

    def drive(self, speed):
        for motor in self.motors:
            motor.target_motor_speed = speed
        self.hull.awake = True

    def set_motor_torque(self, torque):
        for motor in self.motors:
            motor.max_motor_torque = torque

    def aim(self, speed):
        self.gun.target_motor_speed = speed

    def muzzle(self):
        """Position and direction of the barrel's end."""
        return self.barrel.world_point((self.barrel_length, 0.0)), self.barrel.world_vector((1.0, 0.0))


class TankSample(SampleBase):
    """A tank with chain tracks on suspended road wheels and an explosive gun."""

    start = (0.0, 1.6)
    substeps = 8  # the long chain of track links needs more sub-steps
    muzzle_speed = 45.0
    shell_lifetime = 4.0
    reload_time = 0.6
    explosion_radius = 3.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.speed = 8.0
        self.motor_torque = 1500.0
        self.follow = True
        self.shells = {}  # body -> remaining lifetime
        self.effects = []  # (position, radius, remaining time) of flashes and explosions
        self.reload = 0.0
        self.camera_position = b2d.Vec2(self.start)

        self.create_terrain()
        self.create_targets()
        self.tank = Tank(self.world, self.start, self.motor_torque)

        for widget in (
            widgets.FloatSlider("speed", 1.0, 20.0, 0.5, self.speed, self.set_speed),
            widgets.FloatSlider("torque", 200.0, 5000.0, 50.0, self.motor_torque, self.set_motor_torque),
            widgets.Button("fire", self.fire),
            widgets.Button("recover (r)", self.recover),
            widgets.Checkbox("follow tank", self.follow, self.set_follow),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        # the initial view: the tank and the first targets
        x, y = self.start
        return b2d.aabb(lower_bound=(x - 14.0, y - 9.0), upper_bound=(x + 14.0, y + 9.0))

    # ---- scene ----------------------------------------------------------------------------

    def create_terrain(self):
        x = np.arange(-40.0, 330.5, 0.5)
        top = list(zip(x, terrain_height(x)))
        points = [(-40.0, -20.0), (-40.0, 15.0), *top, (330.0, 15.0), (330.0, -20.0)]
        ground = self.world.create_static_body()
        ground.create_chain(
            b2d.chain_def(
                points=points[::-1],
                is_loop=True,
                material=b2d.surface_material(friction=0.9),
                filter=collision_filter(WORLD, 0xFFFF),
            )
        )

    # ---- things to destroy ------------------------------------------------------------------

    @staticmethod
    def debris_def(color, density=0.5, friction=0.6):
        return b2d.shape_def(
            density=density,
            filter=collision_filter(DEBRIS, 0xFFFF),
            material=b2d.surface_material(friction=friction, custom_color=color),
        )

    @staticmethod
    def ground_y(x):
        return float(terrain_height(np.array(x)))

    def add_body(self, position, shape_def, geometry, rotation=0.0):
        body = self.world.create_dynamic_body(position=position, rotation=b2d.make_rot(rotation))
        body.create_shape(shape_def, geometry)
        return body

    def crate_wall(self, x, columns, rows, size=0.45, color=b2d.HexColor.Peru):
        shape_def, box, y0 = self.debris_def(color), b2d.box(size, size), self.ground_y(x)
        for row in range(rows):
            for column in range(columns):
                self.add_body((x + 2.05 * size * column, y0 + size + 2.02 * size * row), shape_def, box)

    def crate_pyramid(self, x, base, size=0.45, color=b2d.HexColor.Burlywood):
        shape_def, box, y0 = self.debris_def(color), b2d.box(size, size), self.ground_y(x)
        for row in range(base):
            for column in range(base - row):
                position = (x + (column + 0.5 * row) * 2.1 * size, y0 + size + 2.02 * size * row)
                self.add_body(position, shape_def, box)

    def barrels(self, x, base, radius=0.4):
        shape_def = self.debris_def(b2d.HexColor.Firebrick, density=0.8, friction=0.4)
        circle, y0 = b2d.circle(radius=radius), self.ground_y(x)
        for row in range(base):
            for column in range(base - row):
                position = (x + (2 * column + row) * radius, y0 + radius + 1.75 * radius * row)
                self.add_body(position, shape_def, circle)

    def watchtower(self, x, height=6.0, width=2.6):
        """Planks on stilts, a platform and crates on top: shoot the legs."""
        plank_def = self.debris_def(b2d.HexColor.Sienna, density=0.6)
        y0 = self.ground_y(x)
        hy = 0.5 * height
        for dx in (0.0, width):
            self.add_body((x + dx, y0 + hy), plank_def, b2d.box(0.12, hy))
        # cross braces
        diagonal = math.hypot(width, height)
        angle = math.atan2(height, width)
        for sign in (1.0, -1.0):
            self.add_body(
                (x + 0.5 * width, y0 + hy), plank_def, b2d.box(0.5 * diagonal, 0.06), rotation=sign * angle
            )
        self.add_body((x + 0.5 * width, y0 + height + 0.15), plank_def, b2d.box(0.5 * width + 0.6, 0.15))
        crate_def, box = self.debris_def(b2d.HexColor.Peru), b2d.box(0.4, 0.4)
        for i in range(3):
            self.add_body((x + 0.5 * width + 0.85 * (i - 1), y0 + height + 0.7), crate_def, box)
        self.add_body((x + 0.5 * width, y0 + height + 1.55), crate_def, box)

    def create_targets(self):
        # right in front of the tank
        self.crate_wall(12.0, columns=3, rows=5)
        self.barrels(16.5, base=4)
        # between the hills and the crater
        self.watchtower(63.0)
        # behind the crater and the jump
        self.crate_pyramid(88.0, base=5)
        self.crate_wall(108.0, columns=2, rows=7, color=b2d.HexColor.Chocolate)
        # the shooting range
        self.crate_pyramid(160.0, base=7)
        self.watchtower(175.0, height=8.0, width=3.0)
        self.crate_wall(190.0, columns=4, rows=8)
        self.barrels(200.0, base=5)
        # logs to drive over behind the big hill
        log_def = self.debris_def(b2d.HexColor.SaddleBrown, density=0.8, friction=0.8)
        for i in range(6):
            self.add_body((280.0 + 4.0 * i, 0.5), log_def, b2d.capsule((-1.0, 0.0), (1.0, 0.0), 0.4))
        # the finale before the end wall
        self.crate_pyramid(312.0, base=9, color=b2d.HexColor.Tan)

    # ---- controls -------------------------------------------------------------------------

    def set_speed(self, value):
        self.speed = value

    def set_motor_torque(self, value):
        self.motor_torque = value
        self.tank.set_motor_torque(value)

    def set_follow(self, value):
        self.follow = value

    def on_key_down(self, event):
        if event.key == "space":
            self.fire()
        elif event.key == "r":
            self.recover()

    def recover(self):
        """Right the tank above the highest surface (terrain or debris) below its front, middle and back."""
        query = b2d.make_query_filter(category_bits=WORLD, mask_bits=WORLD | DEBRIS)
        x = self.tank.position.x
        top = self.ground_y(x)
        for dx in (-3.8, 0.0, 4.0):
            hit = self.world.cast_ray_closest((x + dx, 60.0), (0.0, -120.0), query)
            if hit.hit:
                top = max(top, hit.point.y)
        self.tank.recover(top)

    def fire(self):
        if self.reload > 0.0:
            return
        self.reload = self.reload_time
        muzzle, direction = self.tank.muzzle()
        shell = self.world.create_dynamic_body(
            position=muzzle,
            is_bullet=True,
            linear_velocity=self.tank.hull.linear_velocity + self.muzzle_speed * direction,
        )
        shell.create_shape(
            b2d.shape_def(
                density=20.0,
                filter=collision_filter(SHELL, WORLD | DEBRIS),
                material=b2d.surface_material(custom_color=b2d.HexColor.Gold),
            ),
            b2d.circle(radius=0.12),
        )
        # recoil
        self.tank.barrel.apply_linear_impulse_to_center(-shell.mass * self.muzzle_speed * direction)
        self.shells[shell] = self.shell_lifetime
        self.effects.append((muzzle, 0.5, 0.1))

    # ---- simulation -----------------------------------------------------------------------

    def pre_update(self, dt):
        drive = self.is_key_pressed("a") - self.is_key_pressed("d")
        self.tank.drive(drive * self.speed)
        self.tank.aim(1.0 * (self.is_key_pressed("w") - self.is_key_pressed("s")))
        self.reload = max(0.0, self.reload - dt)

    def post_update(self, dt):
        for shell, lifetime in list(self.shells.items()):
            if self.touches_something(shell):
                self.explode(shell.position)
                lifetime = 0.0
            lifetime -= dt
            if lifetime <= 0.0:
                # remove first: destroy() resets the handle (and with it its hash)
                del self.shells[shell]
                shell.destroy()
            else:
                self.shells[shell] = lifetime
        self.effects = [(p, r, t - dt) for p, r, t in self.effects if t > dt]

        if self.follow:
            # move the camera by the tank's displacement
            position = self.tank.position
            self.frontend.drag_camera(tuple(self.camera_position - position))
            self.camera_position = b2d.Vec2(position)

    @staticmethod
    def touches_something(body):
        return any(data.manifold.point_count > 0 for data in body.contact_data)

    def explode(self, position):
        self.world.explode(
            position=position,
            radius=self.explosion_radius,
            falloff=1.0,
            impulse_per_length=12.0,
            mask_bits=DEBRIS,
        )
        self.effects.append((position, self.explosion_radius, 0.25))

    # ---- drawing --------------------------------------------------------------------------

    def post_debug_draw(self):
        # muzzle flashes and explosions
        dd = self.debug_draw
        for position, radius, remaining in self.effects:
            dd.draw_circle(position, radius * (1.0 - remaining), b2d.HexColor.OrangeRed)
            dd.draw_point(position, 12.0, b2d.HexColor.Yellow)
