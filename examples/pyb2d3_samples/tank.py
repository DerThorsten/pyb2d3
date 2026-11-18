"""A tank with real tracks: ~60 chain links wrapped around suspended road wheels and driven by
sprocket motors, an elevating gun that fires explosive shells, and terrain to drive over.
"""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3 import extensions as ext
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.joints import pinned

# collision categories: the tank parts only touch what they have to
WORLD, HULL, WHEEL, TRACK, SHELL, DEBRIS = 1, 2, 4, 8, 16, 32
EVERYTHING = 0xFFFF
DEBRIS_FILTER = b2d.make_filter(category_bits=DEBRIS, mask_bits=EVERYTHING)

START = (0.0, 1.6)
MOTOR_TORQUE = 1500.0
MUZZLE_SPEED = 45.0
SHELL_LIFETIME = 4.0
RELOAD_TIME = 0.6
EXPLOSION_RADIUS = 3.0
CRATE_SIZE = 0.45  # half size of the crates
BARREL_RADIUS = 0.4


def terrain_height(x):
    """Rolling hills, a crater, a jump ramp, a rough stretch and a big hill (x: float or array)."""

    def bump(x0, x1, height):
        t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
        return height * np.sin(np.pi * t) ** 2

    h = bump(20, 40, 1.5) + bump(40, 60, 2.0) - bump(70, 86, 2.5) + bump(215, 265, 7.0)
    h += np.where((x >= 95) & (x < 105), 0.35 * (x - 95), 0.0)
    h += np.where((x >= 115) & (x < 150), 0.3 * np.abs(np.sin(np.pi * (x - 115) / 1.5)), 0.0)
    return h


def convex_hull(points):
    """Counter-clockwise convex hull of 2d points (monotone chain)."""

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def half(points):
        chain = []
        for p in points:
            while len(chain) >= 2 and cross(chain[-2], chain[-1], p) <= 0:
                chain.pop()
            chain.append(p)
        return chain[:-1]

    points = sorted(map(tuple, points))
    return np.array(half(points) + half(reversed(points)))


def resample_loop(polygon, spacing):
    """Points evenly spaced along a closed polygon."""
    closed = np.vstack([polygon, polygon[:1]])
    arc_length = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(closed, axis=0), axis=1))])
    s = np.linspace(0.0, arc_length[-1], round(arc_length[-1] / spacing), endpoint=False)
    return np.stack(
        [np.interp(s, arc_length, closed[:, 0]), np.interp(s, arc_length, closed[:, 1])], 1
    )


class Tank:
    # local coordinates, the tank faces +x
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

    def __init__(self, world, position):
        self.world = world
        self.origin = b2d.Vec2(position)
        self.hull = world.create_dynamic_body(position=self.origin)
        hull_def = b2d.shape_def(
            density=2.0, filter=b2d.make_filter(category_bits=HULL, mask_bits=WORLD | DEBRIS)
        )
        self.hull.create_shape(hull_def, b2d.polygon(points=self.hull_outline))
        self.hull.create_shape(hull_def, b2d.polygon(points=self.turret_outline))

        self.create_wheels()
        self.create_track()
        self.create_gun()

    def create_wheels(self):
        """Sprocket and idler: revolute motors. Road wheels: motors on sprung wheel joints."""
        wheel_def = b2d.shape_def(
            density=1.5,
            filter=b2d.make_filter(category_bits=WHEEL, mask_bits=WORLD | TRACK | DEBRIS),
            material=b2d.surface_material(friction=1.2),
        )
        self.wheels = []
        for center, radius in [self.sprocket, self.idler, *self.road_wheels, *self.return_rollers]:
            wheel = self.world.create_dynamic_body(
                position=self.origin + center, allow_fast_rotation=True
            )
            wheel.create_shape(wheel_def, b2d.circle(radius=radius))
            self.wheels.append(wheel)
        # in the order of creation above
        sprocket_and_idler = self.wheels[:2]
        road_wheels = self.wheels[2:7]
        rollers = self.wheels[7:]

        self.motors = []
        for wheel in sprocket_and_idler:
            joint = self.world.create_revolute_joint(
                **pinned(self.hull, wheel, wheel.position),
                enable_motor=True,
                max_motor_torque=MOTOR_TORQUE,
            )
            self.motors.append(joint)
        for wheel in road_wheels:
            joint = self.world.create_wheel_joint(
                # the suspension axis is the x-axis of frame A: rotate it upright
                **pinned(self.hull, wheel, wheel.position, q_a=0.5 * math.pi),
                enable_spring=True,
                hertz=4.0,
                damping_ratio=0.7,
                enable_limit=True,
                lower_translation=-0.25,
                upper_translation=0.2,
                enable_motor=True,
                max_motor_torque=0.5 * MOTOR_TORQUE,
            )
            self.motors.append(joint)
        for roller in rollers:
            self.world.create_revolute_joint(**pinned(self.hull, roller, roller.position))

    def create_track(self):
        # the track runs along the convex envelope of all wheels, offset by the link radius
        angles = np.linspace(0.0, 2.0 * np.pi, 48, endpoint=False)
        unit_circle = np.stack([np.cos(angles), np.sin(angles)], axis=1)
        wheels = [self.sprocket, self.idler, *self.road_wheels, *self.return_rollers]
        envelope = np.concatenate(
            [np.array(c) + (r + self.link_radius + 0.01) * unit_circle for c, r in wheels]
        )
        points = resample_loop(convex_hull(envelope), self.link_spacing) + np.array(self.origin)

        link_def = b2d.shape_def(
            density=4.0,
            # links never collide with each other (same negative group)
            filter=b2d.make_filter(
                category_bits=TRACK, mask_bits=WORLD | WHEEL | DEBRIS, group_index=-1
            ),
            material=b2d.surface_material(friction=1.0),
        )
        self.links = []
        for p, q in zip(points, np.roll(points, -1, axis=0)):
            half_length = 0.5 * np.linalg.norm(q - p)
            angle = math.atan2(q[1] - p[1], q[0] - p[0])
            link = self.world.create_dynamic_body(
                position=0.5 * (p + q), rotation=b2d.make_rot(angle)
            )
            capsule = b2d.capsule((-half_length, 0.0), (half_length, 0.0), self.link_radius)
            link.create_shape(link_def, capsule)
            self.links.append(link)
        # close the loop: link i and link i+1 share the point i+1
        for i in range(len(self.links)):
            j = (i + 1) % len(self.links)
            self.world.create_revolute_joint(**pinned(self.links[i], self.links[j], points[j]))

    def create_gun(self):
        pivot = self.origin + self.gun_pivot
        self.barrel = self.world.create_dynamic_body(position=pivot)
        self.barrel.create_shape(
            b2d.shape_def(
                density=1.0, filter=b2d.make_filter(category_bits=HULL, mask_bits=WORLD | DEBRIS)
            ),
            b2d.box(0.5 * self.barrel_length, 0.1, center=(0.5 * self.barrel_length, 0.0)),
        )
        self.gun_joint = self.world.create_revolute_joint(
            **pinned(self.hull, self.barrel, pivot),
            enable_limit=True,
            lower_angle=-0.1,
            upper_angle=0.55,
            enable_motor=True,
            max_motor_torque=800.0,
        )

    def drive(self, speed):
        for motor in self.motors:
            motor.target_motor_speed = speed
        self.hull.awake = True

    def set_motor_torque(self, torque):
        for motor in self.motors:
            motor.max_motor_torque = torque

    def recover(self, surface_y):
        """Move every part rigidly with the hull to an upright pose above `surface_y`."""
        hull_transform = self.hull.transform
        target = b2d.transform(p=(hull_transform.p.x, surface_y + 2.0), q=0.0)
        for body in [self.hull, *self.wheels, *self.links, self.barrel]:
            relative = b2d.inv_mul_transforms(hull_transform, body.transform)
            moved = b2d.mul_transforms(target, relative)
            body.set_transform(moved.p, moved.q)
            body.linear_velocity = (0.0, 0.0)
            body.angular_velocity = 0.0
            body.awake = True


@register_sample("Games", "Tank", video=True)
class TankSample(SampleBase):
    """A tank with chain tracks on suspended road wheels and an explosive gun.

    Keys: a / d drive, w / s raise / lower the gun, space fires, r puts a flipped tank back.
    Hint: shoot the legs of the watchtowers; uncheck "follow tank" to look around.
    """

    substeps = 8  # the long chain of track links needs more sub-steps

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.speed = 8.0
        self.follow = True
        self.reload = 0.0
        self.effects = []  # (position, radius, remaining time) of muzzle flashes and explosions
        self.camera_position = b2d.Vec2(START)

        self.create_terrain()
        self.create_targets()
        self.tank = Tank(self.world, START)
        self.create_gun()

        self.frontend.add_widget(
            widgets.FloatSlider("speed", 1.0, 20.0, 0.5, self.speed, self.set_speed)
        )
        self.frontend.add_widget(
            widgets.FloatSlider(
                "torque", 200.0, 5000.0, 50.0, MOTOR_TORQUE, self.tank.set_motor_torque
            )
        )
        self.frontend.add_widget(widgets.Button("fire", self.fire))
        self.frontend.add_widget(widgets.Button("recover (r)", self.recover))
        self.frontend.add_widget(widgets.Checkbox("follow tank", self.follow, self.set_follow))

    def aabb(self):
        x, y = START
        return b2d.aabb(lower_bound=(x - 14.0, y - 9.0), upper_bound=(x + 14.0, y + 9.0))

    def create_terrain(self):
        x = np.arange(-40.0, 330.5, 0.5)
        top = list(zip(x, terrain_height(x)))
        points = [(-40.0, -20.0), (-40.0, 15.0), *top, (330.0, 15.0), (330.0, -20.0)]
        self.world.create_static_body().create_chain(
            b2d.chain_def(
                points=points[::-1],
                is_loop=True,
                material=b2d.surface_material(friction=0.9),
                filter=b2d.make_filter(category_bits=WORLD, mask_bits=EVERYTHING),
            )
        )

    def create_gun(self):
        """An emitter at the muzzle that fires one shell per burst and removes old shells."""
        self.gun = ext.RadialEmitter(
            self.world,
            b2d.shape_def(
                density=20.0,
                # shells hit only the world and the debris, never the tank
                filter=b2d.make_filter(category_bits=SHELL, mask_bits=WORLD | DEBRIS),
                material=b2d.surface_material(custom_color=b2d.HexColor.Gold),
            ),
            b2d.circle(radius=0.12),
            body=self.tank.barrel,
            local_frame=b2d.transform((self.tank.barrel_length, 0.0)),
            body_def=b2d.body_def(is_bullet=True),
            rate=0.0,
            capacity=20,
            speed=MUZZLE_SPEED,
            lifetime=SHELL_LIFETIME,
        )

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
        log_def = b2d.shape_def(
            density=0.8,
            filter=DEBRIS_FILTER,
            material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.SaddleBrown),
        )
        for i in range(6):
            log = self.world.create_dynamic_body(position=(280.0 + 4.0 * i, 0.5))
            log.create_shape(log_def, b2d.capsule((-1.0, 0.0), (1.0, 0.0), 0.4))
        # the finale before the end wall
        self.crate_pyramid(312.0, base=9, color=b2d.HexColor.Tan)

    def crate_wall(self, x, columns, rows, color=b2d.HexColor.Peru):
        y0, s = float(terrain_height(x)), CRATE_SIZE
        crate_def = b2d.shape_def(
            density=0.5, filter=DEBRIS_FILTER, material=b2d.surface_material(custom_color=color)
        )
        for row in range(rows):
            for column in range(columns):
                position = (x + 2.05 * s * column, y0 + s + 2.02 * s * row)
                self.world.create_dynamic_body(position=position).create_shape(
                    crate_def, b2d.box(s, s)
                )

    def crate_pyramid(self, x, base, color=b2d.HexColor.Burlywood):
        y0, s = float(terrain_height(x)), CRATE_SIZE
        crate_def = b2d.shape_def(
            density=0.5, filter=DEBRIS_FILTER, material=b2d.surface_material(custom_color=color)
        )
        for row in range(base):
            for column in range(base - row):
                position = (x + 2.1 * s * (column + 0.5 * row), y0 + s + 2.02 * s * row)
                self.world.create_dynamic_body(position=position).create_shape(
                    crate_def, b2d.box(s, s)
                )

    def barrels(self, x, base):
        y0, r = float(terrain_height(x)), BARREL_RADIUS
        barrel_def = b2d.shape_def(
            density=0.8,
            filter=DEBRIS_FILTER,
            material=b2d.surface_material(friction=0.4, custom_color=b2d.HexColor.Firebrick),
        )
        for row in range(base):
            for column in range(base - row):
                position = (x + r * (2 * column + row), y0 + r + 1.75 * r * row)
                self.world.create_dynamic_body(position=position).create_shape(
                    barrel_def, b2d.circle(radius=r)
                )

    def watchtower(self, x, height=6.0, width=2.6):
        """Two stilts with cross braces, a platform and crates on top: shoot the legs."""
        y0 = float(terrain_height(x))
        middle = x + 0.5 * width
        brace_angle = math.atan2(height, width)
        brace = b2d.box(0.5 * math.hypot(width, height), 0.06)
        # (position, angle, geometry) of the planks
        planks = [
            ((x, y0 + 0.5 * height), 0.0, b2d.box(0.12, 0.5 * height)),
            ((x + width, y0 + 0.5 * height), 0.0, b2d.box(0.12, 0.5 * height)),
            ((middle, y0 + 0.5 * height), brace_angle, brace),
            ((middle, y0 + 0.5 * height), -brace_angle, brace),
            ((middle, y0 + height + 0.15), 0.0, b2d.box(0.5 * width + 0.6, 0.15)),
        ]
        plank_def = b2d.shape_def(
            density=0.6,
            filter=DEBRIS_FILTER,
            material=b2d.surface_material(custom_color=b2d.HexColor.Sienna),
        )
        for position, angle, geometry in planks:
            plank = self.world.create_dynamic_body(position=position, rotation=b2d.make_rot(angle))
            plank.create_shape(plank_def, geometry)

        crate_def = b2d.shape_def(
            density=0.5,
            filter=DEBRIS_FILTER,
            material=b2d.surface_material(custom_color=b2d.HexColor.Peru),
        )
        top = y0 + height
        for position in [
            (middle - 0.85, top + 0.7),
            (middle, top + 0.7),
            (middle + 0.85, top + 0.7),
        ]:
            self.world.create_dynamic_body(position=position).create_shape(
                crate_def, b2d.box(0.4, 0.4)
            )
        self.world.create_dynamic_body(position=(middle, top + 1.55)).create_shape(
            crate_def, b2d.box(0.4, 0.4)
        )

    def set_speed(self, value):
        self.speed = value

    def set_follow(self, value):
        self.follow = value

    def on_key_down(self, event):
        if event.key == "space":
            self.fire()
        elif event.key == "r":
            self.recover()

    def recover(self):
        """Right the tank above the highest surface (terrain or debris) below it."""
        query = b2d.make_query_filter(category_bits=WORLD, mask_bits=WORLD | DEBRIS)
        x = self.tank.hull.position.x
        top = float(terrain_height(x))
        for dx in (-3.8, 0.0, 4.0):  # the back, the middle and the front
            hit = self.world.cast_ray_closest((x + dx, 60.0), (0.0, -120.0), query)
            if hit.hit:
                top = max(top, hit.point.y)
        self.tank.recover(top)

    def fire(self):
        if self.reload > 0.0:
            return
        self.reload = RELOAD_TIME
        # the emitter returns the reaction of the shell: the recoil
        impulse, angular_impulse = self.gun.burst(1)
        barrel = self.tank.barrel
        barrel.apply_linear_impulse_to_center(impulse)
        barrel.apply_angular_impulse(angular_impulse)
        muzzle = barrel.world_point((self.tank.barrel_length, 0.0))
        self.effects.append((muzzle, 0.5, 0.1))

    def pre_update(self, dt):
        self.tank.drive(self.speed * (self.is_key_pressed("a") - self.is_key_pressed("d")))
        aim = float(self.is_key_pressed("w") - self.is_key_pressed("s"))
        self.tank.gun_joint.target_motor_speed = aim
        self.reload = max(0.0, self.reload - dt)
        self.gun.step(dt)  # ages the shells and destroys the old ones (rate 0: no new ones)

    def post_update(self, dt):
        for shell in self.gun.particles:
            if any(contact.manifold.point_count > 0 for contact in shell.contact_data):
                self.world.explode(
                    position=shell.position,
                    radius=EXPLOSION_RADIUS,
                    falloff=1.0,
                    impulse_per_length=12.0,
                    mask_bits=DEBRIS,
                )
                self.effects.append((shell.position, EXPLOSION_RADIUS, 0.25))
                shell.destroy()  # the emitter drops it on its next step
        self.effects = [(p, r, t - dt) for p, r, t in self.effects if t > dt]

        if self.follow:
            # move the camera along with the tank
            position = self.tank.hull.position
            self.frontend.drag_camera(tuple(self.camera_position - position))
            self.camera_position = b2d.Vec2(position)

    def post_debug_draw(self):
        # growing circles for muzzle flashes and explosions
        for position, radius, remaining in self.effects:
            self.debug_draw.draw_circle(
                position, radius * (1.0 - remaining), b2d.HexColor.OrangeRed
            )
            self.debug_draw.draw_point(position, 12.0, b2d.HexColor.Yellow)
