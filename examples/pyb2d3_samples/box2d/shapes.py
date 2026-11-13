"""Ports of box2d's samples/sample_shapes.cpp."""

import math
import random
from functools import partial

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample, widgets

from ._common import Box2dSample
from ._shapes_helpers import WHITE, parse_svg_path, random_polygon, random_vec2

RED = b2d.HexColor.Red.value
GREEN = b2d.HexColor.Green.value
YELLOW = b2d.HexColor.Yellow.value

SHAPE_TYPES = ["Circle", "Capsule", "Box"]


def shape_type_dropdown(value, callback):
    return widgets.Dropdown(label="Shape", options=SHAPE_TYPES, value=value, callback=callback)


def create_box_container(world):
    """Ground box with a wall on each side, used by the Rounded and Ellipse samples."""
    ground = world.create_static_body()
    for hx, hy, center in ((20.0, 1.0, (0.0, -1.0)), (1.0, 5.0, (19.0, 5.0)), (1.0, 5.0, (-19.0, 5.0))):
        ground.create_shape(b2d.shape_def(), b2d.box(hx, hy, center=center))
    return ground


@register_sample("Shapes", "Chain Shape")
class ChainShape(Box2dSample):
    """A shape rolling and sliding along a closed chain."""

    camera_center = (0.0, 0.0)
    camera_zoom = 25.0 * 1.75

    points = [
        (-56.885498, 12.8985004), (-56.885498, 16.2057495), (56.885498, 16.2057495), (56.885498, -16.2057514),
        (51.5935059, -16.2057514), (43.6559982, -10.9139996), (35.7184982, -10.9139996), (27.7809982, -10.9139996),
        (21.1664963, -14.2212505), (11.9059982, -16.2057514), (0, -16.2057514), (-10.5835037, -14.8827496),
        (-17.1980019, -13.5597477), (-21.1665001, -12.2370014), (-25.1355019, -9.5909977), (-31.75, -3.63799858),
        (-38.3644981, 6.2840004), (-42.3334999, 9.59125137), (-47.625, 11.5755005),
    ]  # fmt: skip

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.shape_type = "Circle"
        self.material = b2d.surface_material(
            friction=0.2, custom_color=b2d.HexColor.SteelBlue.value, user_material_id=42
        )
        self.body = None

        ground = self.world.create_static_body()
        self.chain = ground.create_chain(b2d.chain_def(self.points, material=self.material, is_loop=True))
        self.launch()

        self.frontend.add_widget(shape_type_dropdown(self.shape_type, self.set_shape_type))
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Friction", min_value=0.0, max_value=1.0, step=0.01, value=0.2, callback=self.set_friction
            )
        )
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Restitution", min_value=0.0, max_value=2.0, step=0.1, value=0.0, callback=self.set_restitution
            )
        )
        self.frontend.add_widget(widgets.Button(label="Launch", callback=self.launch))

    def launch(self):
        if self.body is not None:
            self.body.destroy()
        self.body = self.world.create_dynamic_body(position=(-55.0, 13.5))
        geometry = {
            "Circle": b2d.circle(radius=0.5),
            "Capsule": b2d.capsule((-0.5, 0.0), (0.5, 0.0), 0.25),
            "Box": b2d.box(0.5, 0.5),
        }[self.shape_type]
        self.shape = self.body.create_shape(b2d.shape_def(material=self.material), geometry)

    def set_shape_type(self, shape_type):
        self.shape_type = shape_type
        self.launch()

    def set_friction(self, friction):
        self.material.friction = friction
        self.shape.surface_material = self.material
        self.chain.set_all_surface_materials(self.material)

    def set_restitution(self, restitution):
        self.material.restitution = restitution
        self.shape.surface_material = self.material

    def post_debug_draw(self):
        self.debug_draw.draw_segment((0, 0), (0.5, 0), RED)
        self.debug_draw.draw_segment((0, 0), (0, 0.5), GREEN)


@register_sample("Shapes", "Chain Segment")
class ChainSegment(Box2dSample):
    """Stand-alone chain segment shapes whose geometry can be changed at runtime."""

    camera_center = (0.0, 0.0)
    camera_zoom = 25.0 * 1.0

    segment_count = 32

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.shape_type = "Circle"
        self.body = None
        self.mutate_index = 0

        # walk right-to-left so the right-perpendicular normal of (point2 - point1) points up
        point_count = self.segment_count + 3
        self.points = []
        for i in range(point_count):
            x = 25.0 - 50.0 * i / (point_count - 1)
            self.points.append((x, 1.5 * math.sin(0.18 * x)))

        ground = self.world.create_static_body()
        self.segment_shapes = [
            ground.create_shape(b2d.shape_def(), self.chain_segment(i)) for i in range(self.segment_count)
        ]
        self.launch()

        self.frontend.add_widget(shape_type_dropdown(self.shape_type, self.set_shape_type))
        self.frontend.add_widget(widgets.Button(label="Launch", callback=self.launch))
        self.frontend.add_widget(widgets.Button(label="Mutate", callback=self.mutate))

    def chain_segment(self, i):
        p = self.points
        return b2d.chain_segment(b2d.segment(p[i + 1], p[i + 2]), ghost1=p[i], ghost2=p[i + 3])

    def launch(self):
        if self.body is not None:
            self.body.destroy()
        self.body = self.world.create_dynamic_body(position=(-18.0, 5.0))
        geometry = {
            "Circle": b2d.circle(radius=0.25),
            "Capsule": b2d.capsule((-0.5, 0.0), (0.5, 0.0), 0.25),
            "Box": b2d.make_square(0.5),
        }[self.shape_type]
        self.body.create_shape(b2d.shape_def(), geometry)

    def set_shape_type(self, shape_type):
        self.shape_type = shape_type
        self.launch()

    def mutate(self):
        # index in [1, point_count - 2]: the first and last points are ghosts and are not mutated
        index = self.mutate_index + 1
        self.mutate_index = (self.mutate_index + 1) % self.segment_count

        x, y = self.points[index]
        self.points[index] = (x, y + 0.25)

        # the segments that use this point
        for i in (index - 2, index - 1, index):
            if 0 <= i < self.segment_count:
                self.segment_shapes[i].chain_segment = self.chain_segment(i)


@register_sample("Shapes", "Compound Shapes")
class CompoundShapes(Box2dSample):
    """Careful creation of compound shapes leads to better simulation and avoids objects getting stuck.

    This also shows how to get the combined AABB of a body.
    """

    camera_center = (0.0, 6.0)
    camera_zoom = 25.0 * 0.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        self.draw_body_aabbs = False

        self.create_ground_segment(50.0, -50.0)

        self.tables = []
        for x, leg_hy in ((-15.0, 1.5), (-5.0, 2.0)):
            table = world.create_dynamic_body(position=(x, 1.0))
            table.create_shapes(
                b2d.shape_def(),
                [
                    b2d.box(3.0, 0.5, center=(0.0, 3.5)),
                    b2d.box(0.5, leg_hy, center=(-2.5, leg_hy)),
                    b2d.box(0.5, leg_hy, center=(2.5, leg_hy)),
                ],
            )
            self.tables.append(table)

        self.ships = []
        for x, left_mid, right_mid in ((5.0, (0.0, 4.0 / 3.0), (0.0, 4.0 / 3.0)), (15.0, (1.0, 2.0), (-1.0, 2.0))):
            ship = world.create_dynamic_body(position=(x, 1.0))
            ship.create_shapes(
                b2d.shape_def(),
                [
                    b2d.polygon(points=[(-2.0, 0.0), left_mid, (0.0, 4.0)]),
                    b2d.polygon(points=[(2.0, 0.0), right_mid, (0.0, 4.0)]),
                ],
            )
            self.ships.append(ship)

        self.frontend.add_widget(widgets.Button(label="Intrude", callback=self.spawn))
        self.frontend.add_widget(widgets.Checkbox(label="Body AABBs", value=False, callback=self.set_draw_body_aabbs))

    def spawn(self):
        obstructions = [(table, b2d.box(4.0, 0.1, center=(0.0, 3.0))) for table in self.tables]
        obstructions += [(ship, b2d.circle(center=(0.0, 2.0), radius=0.5)) for ship in self.ships]
        for body, geometry in obstructions:
            obstruction = self.world.create_dynamic_body(position=body.position, rotation=body.rotation)
            obstruction.create_shape(b2d.shape_def(), geometry)

    def set_draw_body_aabbs(self, flag):
        self.draw_body_aabbs = flag

    def post_debug_draw(self):
        if self.draw_body_aabbs:
            for body in self.tables + self.ships:
                self.debug_draw.draw_aabb(body.compute_bounds(), YELLOW)


@register_sample("Shapes", "Filter")
class Filter(Box2dSample):
    """Collision filtering with category and mask bits."""

    camera_center = (0.0, 5.0)
    camera_zoom = 25.0 * 0.5

    GROUND = 0x00000001
    TEAMS = (0x00000002, 0x00000004, 0x00000008)
    ALL_BITS = 0xFFFFFFFF

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        ground.create_shape(
            b2d.shape_def(filter=b2d.make_filter(category_bits=self.GROUND, mask_bits=self.ALL_BITS)),
            b2d.segment((-20.0, 0.0), (20.0, 0.0)),
        )

        self.players = []
        self.shapes = []
        for i, team in enumerate(self.TEAMS):
            player = world.create_dynamic_body(position=(0.0, 2.0 + 3.0 * i))
            mask = self.GROUND
            for other in self.TEAMS:
                if other != team:
                    mask |= other
            shape_def = b2d.shape_def(filter=b2d.make_filter(category_bits=team, mask_bits=mask))
            self.players.append(player)
            self.shapes.append(player.create_shape(shape_def, b2d.box(2.0, 1.0)))

        for i, shape in enumerate(self.shapes):
            for j, team in enumerate(self.TEAMS):
                if i != j:
                    self.frontend.add_widget(
                        widgets.Checkbox(
                            label=f"Player {i + 1} collides with team {j + 1}",
                            value=True,
                            callback=partial(self.set_collides, shape, team),
                        )
                    )

    @staticmethod
    def set_collides(shape, team, flag):
        f = shape.filter
        f.mask_bits = f.mask_bits | team if flag else f.mask_bits & ~team
        shape.filter = f

    def post_debug_draw(self):
        for i, player in enumerate(self.players):
            p = player.position
            self.debug_draw.draw_string((p.x - 0.5, p.y), f"player {i + 1}", WHITE)


def odd_even_filter(shape_a, shape_b):
    """Disables collision between shapes with odd and even (non-zero) user data."""
    index_a, index_b = shape_a.user_data, shape_b.user_data
    if index_a == 0 or index_b == 0:
        return True
    return (index_a & 1) + (index_b & 1) != 1


@register_sample("Shapes", "Custom Filter")
class CustomFilter(Box2dSample):
    """A custom filter callback that disables collision between odd and even shapes."""

    camera_center = (0.0, 5.0)
    camera_zoom = 10.0

    count = 10

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        # a plain function: a bound method would keep the sample alive through the world
        world.set_custom_filter_callback(odd_even_filter)

        self.create_ground_segment(-40.0, 40.0)

        self.bodies = []
        for i in range(self.count):
            body = world.create_dynamic_body(position=(-self.count + 2.0 * i, 5.0))
            body.create_shape(b2d.shape_def(enable_custom_filtering=True, user_data=i + 1), b2d.make_square(1.0))
            self.bodies.append(body)

    def post_debug_draw(self):
        for i, body in enumerate(self.bodies):
            self.debug_draw.draw_string(body.position, str(i), WHITE)


@register_sample("Shapes", "Friction")
class Friction(Box2dSample):
    """Boxes with different friction sliding down ramps."""

    camera_center = (0.0, 14.0)
    camera_zoom = 25.0 * 0.6

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        shape_def = b2d.shape_def(material=b2d.surface_material(friction=0.2))
        ground.create_shape(shape_def, b2d.segment((-40.0, 0.0), (40.0, 0.0)))
        for hx, hy, center, angle in (
            (13.0, 0.25, (-4.0, 22.0), -0.25),
            (0.25, 1.0, (10.5, 19.0), 0.0),
            (13.0, 0.25, (4.0, 14.0), 0.25),
            (0.25, 1.0, (-10.5, 11.0), 0.0),
            (13.0, 0.25, (-4.0, 6.0), -0.25),
        ):
            ground.create_shape(shape_def, b2d.box(hx, hy, center=center, rotation=angle))

        for i, friction in enumerate((0.75, 0.5, 0.35, 0.1, 0.0)):
            body = world.create_dynamic_body(position=(-15.0 + 4.0 * i, 28.0))
            body.create_shape(
                b2d.shape_def(density=25.0, material=b2d.surface_material(friction=friction)), b2d.box(0.5, 0.5)
            )


@register_sample("Shapes", "Rolling Resistance")
class RollingResistance(Box2dSample):
    """Balls with increasing rolling resistance. Keys 1, 2, 3 select flat, uphill and downhill ground."""

    camera_center = (5.0, 20.0)
    camera_zoom = 27.5

    resist_scale = 0.02
    lifts = {"1": 0.0, "2": 5.0, "3": -5.0}

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.lift = 0.0
        self.bodies = []
        self.create_scene()

    def create_scene(self):
        for body in self.bodies:
            body.destroy()
        self.bodies = []

        for i in range(20):
            ground = self.world.create_static_body()
            ground.create_shape(b2d.shape_def(), b2d.segment((-40.0, 2.0 * i), (40.0, 2.0 * i + self.lift)))

            body = self.world.create_dynamic_body(
                position=(-39.5, 2.0 * i + 0.75), angular_velocity=-10.0, linear_velocity=(5.0, 0.0)
            )
            material = b2d.surface_material(rolling_resistance=self.resist_scale * i)
            body.create_shape(b2d.shape_def(material=material), b2d.circle(radius=0.5))
            self.bodies += [ground, body]

    def on_key_down(self, event):
        if event.key in self.lifts:
            self.lift = self.lifts[event.key]
            self.create_scene()

    def post_debug_draw(self):
        for i in range(20):
            self.debug_draw.draw_string((-41.5, 2.0 * i + 1.0), f"{self.resist_scale * i:.2f}", WHITE)


@register_sample("Shapes", "Conveyor Belt")
class ConveyorBelt(Box2dSample):
    """A conveyor belt made with the tangent speed of a surface material."""

    camera_center = (2.0, 7.5)
    camera_zoom = 12.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        self.create_ground_segment()

        platform = world.create_static_body(position=(-5.0, 5.0))
        platform.create_shape(
            b2d.shape_def(material=b2d.surface_material(friction=0.8, tangent_speed=2.0)),
            b2d.box(10.0, 0.25, radius=0.25),
        )

        for i in range(5):
            body = world.create_dynamic_body(position=(-10.0 + 2.0 * i, 7.0))
            body.create_shape(b2d.shape_def(), b2d.make_square(0.5))


@register_sample("Shapes", "Tangent Speed")
class TangentSpeed(Box2dSample):
    """Balls carried up through a chain whose segments have different tangent speeds."""

    camera_center = (60.0, -15.0)
    camera_zoom = 38.0

    total_count = 200
    path = (
        "m 613.8334,185.20833 -42.33338,0 h -37.04166 l -34.39581,0 -29.10417,-2.64583 -26.45834,-7.9375 "
        "-26.45833,-13.22917 -23.81251,-21.16666 h -13.22916 v 44.97916 H 68.791712 V 0 h -21.16671 v "
        "206.375 l 566.208398,-1e-5 z"
    )
    belt_colors = ("DarkBlue", "DarkCyan", "DarkGoldenrod", "DarkGray", "DarkGreen", "DarkKhaki", "DarkMagenta")

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.friction = 0.6
        self.rolling_resistance = 0.3
        self.balls = []
        self.step_count = 0

        points = parse_svg_path(self.path, offset=(-47.375002, 0.25), scale=0.2)
        materials = [b2d.surface_material(friction=0.6) for _ in points]
        for i, color in enumerate(self.belt_colors):
            materials[i].tangent_speed = -10.0 * (i + 1)
            materials[i].custom_color = getattr(b2d.HexColor, color).value

        ground = self.world.create_static_body()
        ground.create_chain(b2d.chain_def(points, materials=materials, is_loop=True))

        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Friction", min_value=0.0, max_value=2.0, step=0.01, value=self.friction, callback=self.set_friction
            )
        )
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Rolling Resistance",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                value=self.rolling_resistance,
                callback=self.set_rolling_resistance,
            )
        )

    def drop_ball(self):
        body = self.world.create_dynamic_body(position=(110.0, -30.0))
        material = b2d.surface_material(friction=self.friction, rolling_resistance=self.rolling_resistance)
        body.create_shape(b2d.shape_def(material=material), b2d.circle(radius=0.5))
        return body

    def reset(self):
        for body in self.balls:
            body.destroy()
        self.balls = []

    def set_friction(self, friction):
        self.friction = friction
        self.reset()

    def set_rolling_resistance(self, rolling_resistance):
        self.rolling_resistance = rolling_resistance
        self.reset()

    def pre_update(self, dt):
        if self.step_count % 25 == 0 and len(self.balls) < self.total_count:
            self.balls.append(self.drop_ball())
        self.step_count += 1


@register_sample("Shapes", "Modify Geometry")
class ModifyGeometry(Box2dSample):
    """Modify the geometry of an existing shape.

    This is only supported on dynamic and kinematic shapes because static shapes don't look for new collisions.
    """

    camera_center = (0.0, 5.0)
    camera_zoom = 25.0 * 0.25

    # shape class, geometry property, geometry for a scale
    geometries = {
        "Circle": (b2d.CircleShape, "circle", lambda s: b2d.circle(radius=0.5 * s)),
        "Capsule": (b2d.CapsuleShape, "capsule", lambda s: b2d.capsule((-0.5 * s, 0.0), (0.0, 0.5 * s), 0.5 * s)),
        "Segment": (b2d.SegmentShape, "segment", lambda s: b2d.segment((-0.5 * s, 0.0), (0.75 * s, 0.0))),
        "Polygon": (b2d.PolygonShape, "polygon", lambda s: b2d.box(0.5 * s, 0.75 * s)),
    }

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        ground.create_shape(b2d.shape_def(), b2d.box(10.0, 1.0, center=(0.0, -1.0)))

        body = world.create_dynamic_body(position=(0.0, 4.0))
        body.create_shape(b2d.shape_def(), b2d.box(1.0, 1.0))

        self.shape_type = "Circle"
        self.scale = 1.0
        self.body = world.create_kinematic_body(position=(0.0, 1.0))
        self.shape = self.body.create_shape(b2d.shape_def(), b2d.circle(radius=0.5))

        self.frontend.add_widget(
            widgets.RadioButtons(
                label="Shape", options=list(self.geometries), value=self.shape_type, callback=self.set_shape_type
            )
        )
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Scale", min_value=0.1, max_value=10.0, step=0.01, value=self.scale, callback=self.set_scale
            )
        )
        self.frontend.add_widget(
            widgets.RadioButtons(
                label="Body Type",
                options=["Static", "Kinematic", "Dynamic"],
                value="Kinematic",
                callback=self.set_body_type,
            )
        )

    def update_shape(self):
        cls, prop, make_geometry = self.geometries[self.shape_type]
        self.shape = cls(self.shape.id)
        setattr(self.shape, prop, make_geometry(self.scale))
        self.body.update_mass_from_shapes()

    def set_shape_type(self, shape_type):
        self.shape_type = shape_type
        self.update_shape()

    def set_scale(self, scale):
        self.scale = scale
        self.update_shape()

    def set_body_type(self, name):
        self.body.type = getattr(b2d.BodyType, name.upper())


@register_sample("Shapes", "Chain Link")
class ChainLink(Box2dSample):
    """How to link two chain shapes together.

    This is a useful technique for building large game levels with smooth collision.
    """

    camera_center = (0.0, 5.0)
    camera_zoom = 25.0 * 0.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        # each chain gets ghost points from the other one, which carries on past both its ends
        for points, ghost1, ghost2 in (
            ([(0.0, 0.0), (-40.0, 0.0), (-40.0, -1.0), (0.0, -1.0)], (40.0, 1.0), (40.0, -1.0)),
            ([(0.0, -1.0), (40.0, -1.0), (40.0, 0.0), (0.0, 0.0)], (-40.0, -1.0), (-40.0, 0.0)),
        ):
            chain_def = b2d.chain_def(points, is_loop=False)
            chain_def.ghost1 = ghost1
            chain_def.ghost2 = ghost2
            ground.create_chain(chain_def)

        for x, geometry in (
            (-5.0, b2d.circle(radius=0.5)),
            (0.0, b2d.capsule((-0.5, 0.0), (0.5, 0.0), 0.25)),
            (5.0, b2d.box(0.5, 0.5)),
        ):
            body = world.create_dynamic_body(position=(x, 2.0))
            body.create_shape(b2d.shape_def(), geometry)


@register_sample("Shapes", "Rounded")
class Rounded(Box2dSample):
    """A pile of random rounded polygons."""

    camera_center = (2.0, 8.0)
    camera_zoom = 25.0 * 0.55

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        create_box_container(self.world)

        shape_def = b2d.shape_def(material=b2d.surface_material(rolling_resistance=0.3))
        for i in range(10):
            for j in range(10):
                body = self.world.create_dynamic_body(position=(-5.0 + j, 2.0 + i))
                polygon = random_polygon(0.5)
                polygon.radius = random.uniform(0.05, 0.25)
                body.create_shape(shape_def, polygon)


@register_sample("Shapes", "Ellipse")
class Ellipse(Box2dSample):
    """Ellipses approximated by a rounded diamond polygon."""

    camera_center = (2.0, 8.0)
    camera_zoom = 25.0 * 0.55

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        create_box_container(self.world)

        diamond = [(0.0, -0.25), (0.0, 0.25), (0.05, 0.075), (-0.05, 0.075), (0.05, -0.075), (-0.05, -0.075)]
        polygon = b2d.polygon(points=diamond, radius=0.2)
        shape_def = b2d.shape_def(material=b2d.surface_material(rolling_resistance=0.2))
        for i in range(10):
            for j in range(10):
                body = self.world.create_dynamic_body(position=(-5.0 + j, 2.0 + i))
                body.create_shape(shape_def, polygon)


@register_sample("Shapes", "Offset")
class Offset(Box2dSample):
    """Shapes that are offset from their body origin."""

    camera_center = (2.0, 8.0)
    camera_zoom = 25.0 * 0.55

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body(position=(-1.0, 1.0))
        ground.create_shape(b2d.shape_def(), b2d.box(1.0, 1.0, center=(10.0, -2.0), rotation=0.5 * math.pi))

        body = world.create_dynamic_body(position=(13.5, -0.75))
        body.create_shape(b2d.shape_def(), b2d.capsule((-5.0, 1.0), (-4.0, 1.0), 0.25))

        body = world.create_dynamic_body(position=(0.0, 0.0))
        body.create_shape(b2d.shape_def(), b2d.box(0.75, 0.5, center=(9.0, 2.0), rotation=0.5 * math.pi))

    def post_debug_draw(self):
        self.debug_draw.draw_transform(b2d.transform())


@register_sample("Shapes", "Explosion")
class Explosion(Box2dSample):
    """How to use explosions; demonstrates the projected perimeter."""

    camera_center = (0.0, 0.0)
    camera_zoom = 14.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        self.reference_angle = 0.0
        self.radius = 7.0
        self.falloff = 3.0
        self.impulse = 10.0

        ground = world.create_static_body()
        self.joints = []
        r = 8.0
        for angle in range(0, 360, 30):
            a = math.radians(angle)
            position = (r * math.cos(a), r * math.sin(a))
            body = world.create_dynamic_body(position=position, gravity_scale=0.0)
            body.create_shape(b2d.shape_def(), b2d.box(1.0, 0.1))
            self.joints.append(
                world.create_weld_joint(
                    body_a=ground,
                    body_b=body,
                    local_frame_a=b2d.transform(p=position, q=self.reference_angle),
                    angular_hertz=0.5,
                    angular_damping_ratio=0.7,
                    linear_hertz=0.5,
                    linear_damping_ratio=0.7,
                )
            )

        self.frontend.add_widget(widgets.Button(label="Explode", callback=self.explode))
        for name, lo in (("radius", 0.0), ("falloff", 0.0), ("impulse", -20.0)):
            self.frontend.add_widget(
                widgets.FloatSlider(
                    label=name,
                    min_value=lo,
                    max_value=20.0,
                    step=0.1,
                    value=getattr(self, name),
                    callback=partial(setattr, self, name),
                )
            )

    def explode(self):
        self.world.explode(position=(0, 0), radius=self.radius, falloff=self.falloff, impulse_per_length=self.impulse)

    def pre_update(self, dt):
        self.reference_angle = b2d.unwind_angle(self.reference_angle + math.radians(60.0) * dt)
        for joint in self.joints:
            frame = joint.local_frame_a
            frame.q = b2d.make_rot(self.reference_angle)
            joint.local_frame_a = frame

    def post_debug_draw(self):
        self.debug_draw.draw_circle((0, 0), self.radius + self.falloff, b2d.HexColor.Box2DBlue.value)
        self.debug_draw.draw_circle((0, 0), self.radius, b2d.HexColor.Box2DYellow.value)


@register_sample("Shapes", "Recreate Static")
class RecreateStatic(Box2dSample):
    """A static shape being recreated every step."""

    camera_center = (0.0, 2.5)
    camera_zoom = 3.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        body = self.world.create_dynamic_body(position=(0.0, 1.0))
        body.create_shape(b2d.shape_def(), b2d.box(1.0, 1.0))
        self.ground = None

    def pre_update(self, dt):
        if self.ground is not None:
            self.ground.destroy()
        self.ground = self.world.create_static_body()
        # invoke contact creation so that contact points are created immediately on a static body
        self.ground.create_shape(
            b2d.shape_def(invoke_contact_creation=True), b2d.segment((-10.0, 0.0), (10.0, 0.0))
        )


@register_sample("Shapes", "Wind")
class Wind(Box2dSample):
    """A chain of shapes blowing in a noisy wind (drag and lift)."""

    camera_center = (0.0, 1.0)
    camera_zoom = 2.0

    max_count = 60

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.ground = self.world.create_static_body()
        self.shape_type = "Capsule"
        self.wind = [6.0, 0.0]
        self.drag = 1.0
        self.lift = 0.75
        self.count = 10
        self.noise = (0.0, 0.0)
        self.current_wind = (0.0, 0.0)
        self.bodies = []
        self.create_scene()

        self.frontend.add_widget(shape_type_dropdown(self.shape_type, self.set_shape_type))
        for axis in range(2):
            self.frontend.add_widget(
                widgets.FloatSlider(
                    label=f"Wind {'xy'[axis]}",
                    min_value=-20.0,
                    max_value=20.0,
                    step=0.1,
                    value=self.wind[axis],
                    callback=partial(self.wind.__setitem__, axis),
                )
            )
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Drag", min_value=0.0, max_value=1.0, step=0.01, value=self.drag, callback=partial(setattr, self, "drag")
            )
        )
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Lift", min_value=0.0, max_value=4.0, step=0.01, value=self.lift, callback=partial(setattr, self, "lift")
            )
        )
        self.frontend.add_widget(
            widgets.IntSlider(
                label="Count", min_value=1, max_value=self.max_count, step=1, value=self.count, callback=self.set_count
            )
        )

    def create_scene(self):
        for body in self.bodies:
            body.destroy()
        self.bodies = []

        radius = 0.1
        geometry = {
            "Circle": b2d.circle(radius=radius),
            "Capsule": b2d.capsule((0.0, -radius), (0.0, radius), 0.25 * radius),
            "Box": b2d.box(0.25 * radius, 1.25 * radius),
        }[self.shape_type]
        shape_def = b2d.shape_def(density=20.0)

        parent, anchor = self.ground, (0.0, 2.0 + radius)
        for i in range(self.count):
            body = self.world.create_dynamic_body(
                position=(0.0, 2.0 - 2.0 * radius * i), gravity_scale=0.5, enable_sleep=False
            )
            body.create_shape(shape_def, geometry)
            self.world.create_revolute_joint(
                body_a=parent,
                body_b=body,
                local_frame_a=b2d.transform(p=anchor),
                local_frame_b=b2d.transform(p=(0.0, radius)),
                draw_scale=0.1,
                hertz=0.1,
                damping_ratio=0.0,
                enable_spring=True,
            )
            self.bodies.append(body)
            parent, anchor = body, (0.0, -radius)

    def set_shape_type(self, shape_type):
        self.shape_type = shape_type
        self.create_scene()

    def set_count(self, count):
        self.count = int(count)
        self.create_scene()

    def pre_update(self, dt):
        wx, wy = self.wind
        speed = math.hypot(wx, wy)
        dx, dy = (wx / speed, wy / speed) if speed > 1e-9 else (0.0, 0.0)
        nx, ny = self.noise
        self.current_wind = (speed * (dx + nx), speed * (dy + ny))

        for body in self.bodies:
            for shape in body.shapes:
                shape.apply_wind(self.current_wind, self.drag, self.lift, True)

        rx, ry = random_vec2(-0.3, 0.3)
        self.noise = (nx + 0.05 * (rx - nx), ny + 0.05 * (ry - ny))

    def post_debug_draw(self):
        wx, wy = self.current_wind
        self.debug_draw.draw_segment((0.0, 0.0), (0.2 * wx, 0.2 * wy), b2d.HexColor.Magenta.value)
