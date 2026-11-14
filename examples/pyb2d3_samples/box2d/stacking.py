"""Ports of box2d's samples/sample_stacking.cpp."""

import math

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample, widgets

from ._common import Box2dSample
from ._stacking_helpers import ROUNDED_BOX, create_column, launch_body


def _ground_box(world, hx, hy, position, **shape_kwargs):
    ground = world.create_static_body(position=position)
    ground.create_shape(b2d.shape_def(**shape_kwargs), b2d.box(hx, hy))
    return ground


@register_sample("Stacking", "Single Box")
class SingleBox(Box2dSample):
    """A single box sliding on the ground."""

    camera_center = (0.0, 2.5)
    camera_zoom = 3.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        extent = 1.0
        ground_width = 66.0 * extent
        self.create_ground_segment(-ground_width, ground_width)
        self.body = self.world.create_dynamic_body(position=(0.0, 1.0), linear_velocity=(5.0, 0.0))
        self.body.create_shape(b2d.shape_def(), b2d.box(extent, extent))


@register_sample("Stacking", "Tilted Stack")
class TiltedStack(Box2dSample):
    """Leaning towers of rounded boxes."""

    camera_center = (7.5, 7.5)
    camera_zoom = 20.0
    columns = 10
    rows = 10

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        _ground_box(self.world, 1000.0, 1.0, (0.0, -1.0))

        shape_def = b2d.shape_def(density=1.0, material=b2d.surface_material(friction=0.3))
        offset = 0.2
        dx = 5.0
        xroot = -0.5 * dx * (self.columns - 1.0)
        self.bodies = []
        for j in range(self.columns):
            x = xroot + j * dx
            for i in range(self.rows):
                body = self.world.create_dynamic_body(position=(x + offset * i, 0.5 + 1.0 * i))
                body.create_shape(shape_def, ROUNDED_BOX)
                self.bodies.append(body)


@register_sample("Stacking", "Vertical Stack")
class VerticalStack(Box2dSample):
    """Continuous collision: bullets against a stack, no chain reaction tunneling.

    Press 'b' to fire bullets.
    """

    camera_center = (-7.0, 9.0)
    camera_zoom = 14.0
    max_columns = 10
    max_rows = 160
    max_bullets = 8
    shape_types = ["Circle", "Box"]

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        ground.create_shape(b2d.shape_def(), b2d.segment((10.0, 0.0), (10.0, 80.0)))
        ground.create_shape(b2d.shape_def(), b2d.segment((-100.0, 0.0), (100.0, 0.0)))

        self.shape_type = "Box"
        self.row_count = 12
        self.column_count = 1
        self.bullet_count = 1
        self.bullet_type = "Circle"
        self.bodies = []
        self.bullets = []
        self.create_stacks()

        add = self.frontend.add_widget
        add(widgets.Dropdown(label="Shape", options=self.shape_types, value=self.shape_type,
                             callback=lambda v: self.reset(shape_type=v)))
        add(widgets.IntSlider(label="Rows", min_value=1, max_value=self.max_rows, step=1, value=self.row_count,
                              callback=lambda v: self.reset(row_count=v)))
        add(widgets.IntSlider(label="Columns", min_value=1, max_value=self.max_columns, step=1,
                              value=self.column_count, callback=lambda v: self.reset(column_count=v)))
        add(widgets.IntSlider(label="Bullets", min_value=1, max_value=self.max_bullets, step=1,
                              value=self.bullet_count, callback=lambda v: setattr(self, "bullet_count", v)))
        add(widgets.Dropdown(label="Bullet Shape", options=self.shape_types, value=self.bullet_type,
                             callback=lambda v: setattr(self, "bullet_type", v)))
        add(widgets.Button(label="Fire Bullets", callback=self.refire_bullets))
        add(widgets.Button(label="Destroy Body", callback=self.destroy_body))
        add(widgets.Button(label="Reset Stack", callback=self.reset))

    def create_stacks(self):
        for body in self.bodies:
            if body.is_valid:
                body.destroy()

        shape_def = b2d.shape_def(density=1.0, material=b2d.surface_material(friction=0.3))
        if self.shape_type == "Circle":
            geometry, offset = b2d.circle(radius=0.5), 0.0
        else:
            geometry, offset = ROUNDED_BOX, 0.01

        dx = -3.0
        xroot = 8.0
        self.bodies = []
        for j in range(self.column_count):
            self.bodies += create_column(self.world, xroot + j * dx, self.row_count, shape_def, geometry, offset)

    def reset(self, **changes):
        for name, value in changes.items():
            setattr(self, name, value)
        self.destroy_bullets()
        self.create_stacks()

    def destroy_body(self):
        """Destroy the lowest remaining body of each column."""
        for j in range(self.column_count):
            column = self.bodies[j * self.row_count : (j + 1) * self.row_count]
            for body in column:
                if body.is_valid:
                    body.destroy()
                    break

    def destroy_bullets(self):
        for bullet in self.bullets:
            if bullet.is_valid:
                bullet.destroy()
        self.bullets = []

    def fire_bullets(self):
        shape_def = b2d.shape_def(density=4.0)
        geometry = b2d.box(0.25, 0.25) if self.bullet_type == "Box" else b2d.circle(radius=0.25)
        for i in range(self.bullet_count):
            bullet = launch_body(self.world, (-26.7 - i, 6.0))
            bullet.create_shape(shape_def, geometry)
            self.bullets.append(bullet)

    def refire_bullets(self):
        self.destroy_bullets()
        self.fire_bullets()

    def on_key_down(self, event):
        if event.key == "b":
            self.fire_bullets()


@register_sample("Stacking", "Circle Stack")
class CircleStack(Box2dSample):
    """A simple circle stack that also shows how to collect hit events."""

    camera_center = (0.0, 5.0)
    camera_zoom = 6.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        # shape user data: index of the shape (ground = 0)
        ground = world.create_static_body()
        ground.create_shape(b2d.shape_def(), b2d.segment((-10.0, 0.0), (10.0, 0.0)))

        world.gravity = (0.0, -20.0)
        world.set_contact_tuning(0.25 * 360.0, 10.0, 3.0)

        circle = b2d.circle(radius=0.5)
        y = 0.75
        for i in range(4):
            body = world.create_dynamic_body(position=(0.0, y))
            shape_def = b2d.shape_def(
                enable_hit_events=True,
                material=b2d.surface_material(friction=0.0, restitution=0.8),
                user_data=i + 1,
                density=1.0 + 4.0 * i,
            )
            body.create_shape(shape_def, circle)
            y += 1.25

        self.events = []  # (index_a, index_b, point) of every hit so far

    def post_update(self, dt):
        for hit in self.world.get_contact_events().hit_events():
            self.events.append((hit.shape_a.user_data, hit.shape_b.user_data, hit.point))

    def post_debug_draw(self):
        white = b2d.HexColor.White.value
        for index_a, index_b, point in self.events:
            self.debug_draw.draw_point(point, 10.0, white)
            self.debug_draw.draw_string(point, f"{index_a}, {index_b}", white)


@register_sample("Stacking", "Capsule Stack")
class CapsuleStack(Box2dSample):
    """A stack of capsules."""

    camera_center = (0.0, 5.0)
    camera_zoom = 6.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        _ground_box(self.world, 10.0, 1.0, (0.0, -1.0))

        a = 0.25
        capsule = b2d.capsule((-4.0 * a, 0.0), (4.0 * a, 0.0), a)
        y = 2.0 * a
        for _ in range(20):
            body = self.world.create_dynamic_body(position=(0.0, y))
            body.create_shape(b2d.shape_def(), capsule)
            y += 3.0 * a


@register_sample("Stacking", "Cliff")
class Cliff(Box2dSample):
    """Capsules, boxes and circles sliding off ledges."""

    camera_center = (0.0, 5.0)
    camera_zoom = 25.0 * 0.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        shape_def = b2d.shape_def()
        ground.create_shape(shape_def, b2d.box(100.0, 1.0, center=(0.0, -1.0)))
        ground.create_shape(shape_def, b2d.segment((-14.0, 4.0), (-8.0, 4.0)))
        ground.create_shape(shape_def, b2d.box(3.0, 0.5, center=(0.0, 4.0)))
        ground.create_shape(shape_def, b2d.capsule((8.5, 4.0), (13.5, 4.0), 0.5))

        self.flip = False
        self.bodies = []
        self.create_bodies()
        self.frontend.add_widget(widgets.Button(label="Flip", callback=self.toggle_flip))

    def toggle_flip(self):
        self.flip = not self.flip
        self.create_bodies()

    def create_bodies(self):
        for body in self.bodies:
            if body.is_valid:
                body.destroy()
        self.bodies = []

        sign = -1.0 if self.flip else 1.0
        capsule = b2d.capsule((-0.25, 0.0), (0.25, 0.0), 0.25)
        circle = b2d.circle(radius=0.5)
        square = b2d.make_square(0.5)

        offset = -4.0 if self.flip else 0.0
        circle_offset = 4.0 if self.flip else 0.0
        groups = [
            (capsule, 0.01, 2.0, [(-9.0 + offset, 4.25), (2.0 + offset, 4.75), (13.0 + offset, 4.75)]),
            (square, 0.01, 2.5, [(-11.0, 4.5), (0.0, 5.0), (11.0, 5.0)]),
            (circle, 0.2, 1.5, [(-13.0 + circle_offset, 4.5), (-2.0 + circle_offset, 5.0), (9.0 + circle_offset, 5.0)]),
        ]
        for geometry, friction, speed, positions in groups:
            shape_def = b2d.shape_def(material=b2d.surface_material(friction=friction))
            for position in positions:
                body = self.world.create_dynamic_body(position=position, linear_velocity=(speed * sign, 0.0))
                body.create_shape(shape_def, geometry)
                self.bodies.append(body)


@register_sample("Stacking", "Arch")
class Arch(Box2dSample):
    """An arch of polygons held together by friction only."""

    camera_center = (0.0, 8.0)
    camera_zoom = 25.0 * 0.35

    ps1 = [
        (16.0, 0.0),
        (14.93803712795643, 5.133601056842984),
        (13.79871746027416, 10.24928069555078),
        (12.56252963284711, 15.34107019122473),
        (11.20040987372525, 20.39856541571217),
        (9.66521217819836, 25.40369899225096),
        (7.87179930638133, 30.3179337000085),
        (5.635199558196225, 35.03820717801641),
        (2.405937953536585, 39.09554102558315),
    ]
    ps2 = [
        (24.0, 0.0),
        (22.33619528222415, 6.02299846205841),
        (20.54936888969905, 12.00964361211476),
        (18.60854610798073, 17.9470321677465),
        (16.46769273811807, 23.81367936585418),
        (14.05325025774858, 29.57079353071012),
        (11.23551045834022, 35.13775818285372),
        (7.752568160730571, 40.30450679009583),
        (3.016931552701656, 44.28891593799322),
    ]

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        scale = 0.25
        ps1 = [(scale * x, scale * y) for x, y in self.ps1]
        ps2 = [(scale * x, scale * y) for x, y in self.ps2]

        shape_def = b2d.shape_def(material=b2d.surface_material(friction=0.6))
        ground = world.create_static_body()
        ground.create_shape(shape_def, b2d.segment((-100.0, 0.0), (100.0, 0.0)))

        def mirror(p):
            return (-p[0], p[1])

        quads = [[ps1[i], ps2[i], ps2[i + 1], ps1[i + 1]] for i in range(8)]
        quads += [[mirror(ps2[i]), mirror(ps1[i]), mirror(ps1[i + 1]), mirror(ps2[i + 1])] for i in range(8)]
        quads.append([ps1[8], ps2[8], mirror(ps2[8]), mirror(ps1[8])])
        for quad in quads:
            body = world.create_dynamic_body()
            body.create_shape(shape_def, b2d.polygon(quad))

        for i in range(4):
            body = world.create_dynamic_body(position=(0.0, 0.5 + ps2[8][1] + 1.0 * i))
            body.create_shape(shape_def, b2d.box(2.0, 0.5))


@register_sample("Stacking", "Double Domino")
class DoubleDomino(Box2dSample):
    """A row of dominoes knocked over by an impulse."""

    camera_center = (0.0, 4.0)
    camera_zoom = 25.0 * 0.25

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        _ground_box(self.world, 100.0, 1.0, (0.0, -1.0))

        box = b2d.box(0.125, 0.5)
        shape_def = b2d.shape_def(material=b2d.surface_material(friction=0.6))
        count = 15
        x = -0.5 * count
        for i in range(count):
            body = self.world.create_dynamic_body(position=(x, 0.5))
            body.create_shape(shape_def, box)
            if i == 0:
                body.apply_linear_impulse((0.2, 0.0), (x, 1.0), True)
            x += 1.0


@register_sample("Stacking", "Confined")
class Confined(Box2dSample):
    """A grid of weightless circles packed into a box."""

    camera_center = (0.0, 10.0)
    camera_zoom = 25.0 * 0.5
    grid_count = 25

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        shape_def = b2d.shape_def()
        for p1, p2 in [
            ((-10.5, 0.0), (10.5, 0.0)),
            ((-10.5, 0.0), (-10.5, 20.5)),
            ((10.5, 0.0), (10.5, 20.5)),
            ((-10.5, 20.5), (10.5, 20.5)),
        ]:
            ground.create_shape(shape_def, b2d.capsule(p1, p2, 0.5))

        circle = b2d.circle(radius=0.5)
        n = self.grid_count
        for column in range(n):
            for row in range(n):
                x = -8.75 + column * 18.0 / n
                y = 1.5 + row * 18.0 / n
                body = self.world.create_dynamic_body(position=(x, y), gravity_scale=0.0)
                body.create_shape(shape_def, circle)


@register_sample("Stacking", "Card House")
class CardHouse(Box2dSample):
    """A house of cards (from PEEL)."""

    camera_center = (0.75, 0.9)
    camera_zoom = 25.0 * 0.05

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        shape_def = b2d.shape_def(material=b2d.surface_material(friction=0.7))
        ground = self.world.create_static_body(position=(0.0, -2.0))
        ground.create_shape(shape_def, b2d.box(40.0, 2.0))

        card_height = 0.2
        card_thickness = 0.001
        angle0 = 25.0 * math.pi / 180.0
        angle1 = -25.0 * math.pi / 180.0
        angle2 = 0.5 * math.pi
        card_box = b2d.box(card_thickness, card_height)

        def card(position, angle):
            body = self.world.create_dynamic_body(position=position, rotation=angle)
            body.create_shape(shape_def, card_box)

        nb = 5
        z0 = 0.0
        y = card_height - 0.02
        while nb:
            z = z0
            for i in range(nb):
                if i != nb - 1:
                    card((z + 0.25, y + card_height - 0.015), angle2)
                card((z, y), angle1)
                z += 0.175
                card((z, y), angle0)
                z += 0.175
            y += card_height * 2.0 - 0.03
            z0 += 0.175
            nb -= 1
