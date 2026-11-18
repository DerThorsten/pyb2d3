"""Goo game: build a wobbly tower from goo balls linked by distance joints."""

import math
from dataclasses import dataclass
from itertools import combinations

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample
import pyb2d3_sandbox.widgets as widgets

GOO_RADIUS = 0.5
EDGE_LENGTH = 2.0  # the length of a link in the start triangle (and of balloon strings)
REACH = 2 * EDGE_LENGTH  # a new goo links to goos at most this far away
# a new goo links to the linked pair whose squared distances to it add up to at most this
MAX_PAIR_DISTANCE = REACH**2
# a release this close to the middle of two unlinked goos links them
LINK_SNAP = GOO_RADIUS / 2

# the ground: a flat floor with a deep shaft in it (clockwise)
GROUND = [(60, 100), (60, 0), (20, 0), (20, -100), (5, -100), (5, 0), (-100, 0), (-100, 100)]


@dataclass
class GooType:
    name: str
    color: tuple
    edge_color: tuple
    density: float = 1.0
    hertz: float = 4.0  # stiffness of its links
    gravity_scale: float = 1.0
    enable_spring: bool = True  # False: rigid links
    max_links: int = 40
    fixed_length: bool = False  # links pull to EDGE_LENGTH instead of the placing distance
    hangs_on_one: bool = False  # links to the closest goo only, not to a pair


GOO_TYPES = [
    GooType("Plain Goo", (50, 50, 255), (50, 50, 255)),
    GooType(
        "Balloon Goo",
        (255, 0, 0),
        (255, 100, 0),  # a rope
        density=0.5,
        hertz=8.0,
        gravity_scale=-1.0,  # floats up
        enable_spring=False,
        max_links=1,
        fixed_length=True,
        hangs_on_one=True,
    ),
    GooType(  # forms dangling chains
        "Drip Goo",
        (200, 200, 200),
        (200, 200, 200),
        density=0.25,
        hertz=2.0,
        max_links=2,
        hangs_on_one=True,
    ),
    GooType("Heavy Goo", (10, 10, 0), (10, 10, 0), density=15.0, hertz=10.0),
]


class Goo:
    def __init__(self, world, kind, position):
        self.kind = kind
        self.neighbours = []
        self.body = world.create_dynamic_body(
            position=position, gravity_scale=kind.gravity_scale, fixed_rotation=True
        )
        material = b2d.surface_material(
            restitution=0.2, friction=0.5, custom_color=b2d.hex_color(*kind.color)
        )
        self.body.create_shape(
            b2d.shape_def(density=kind.density, material=material, enable_contact_events=False),
            b2d.circle(radius=GOO_RADIUS),
        )

    @property
    def position(self):
        p = self.body.position
        return (p[0], p[1])

    def has_room(self):
        return len(self.neighbours) < self.kind.max_links


@register_sample("Games", "Goo Game")
class GooGame(SampleBase):
    """Build structures from goo balls linked by spring joints.
    Mouse: press, move to preview, release to place a goo (it links to goos nearby);
    release between two goos to link just them.
    Goo Type: plain, balloon (floats up), drip (chains), heavy.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.kind = GOO_TYPES[0]  # the type of the next goo
        self.goos = []
        self.goo_of_body = {}  # body -> goo, for the results of world queries
        self.links = []  # (goo, goo): drawn in the color of the first goo
        self.placement = None  # what releasing the mouse would do, see find_placement
        self.dragging_camera = False

        self.anchor_body.create_chain(b2d.chain_def(points=GROUND, is_loop=True))
        self.create_start_triangle()

        self.frontend.add_widget(
            widgets.RadioButtons(
                label="Goo Type",
                options=[kind.name for kind in GOO_TYPES],
                value=self.kind.name,
                callback=self.set_kind,
            )
        )

    def create_start_triangle(self):
        h = EDGE_LENGTH / 2 * math.sqrt(3)
        a, b, c = (
            self.add_goo(GOO_TYPES[0], p)
            for p in (
                (-EDGE_LENGTH / 2, GOO_RADIUS),
                (EDGE_LENGTH / 2, GOO_RADIUS),
                (0, h + GOO_RADIUS),
            )
        )
        self.link(a, b)
        self.link(b, c)
        self.link(c, a)
        if self.frontend.settings.headless:
            # one more goo makes it a bit wobbly (e.g. for the docs)
            d = self.add_goo(GOO_TYPES[0], (3.5, 3))
            self.link(b, d)
            self.link(c, d)

    def aabb(self):
        margin = 10 + GOO_RADIUS
        xs = [goo.position[0] for goo in self.goos]
        ys = [goo.position[1] for goo in self.goos]
        return b2d.aabb(
            lower_bound=(min(xs) - margin, min(ys) - margin),
            upper_bound=(max(xs) + margin, max(ys) + margin),
        )

    def set_kind(self, name):
        self.kind = next(kind for kind in GOO_TYPES if kind.name == name)

    def add_goo(self, kind, position):
        goo = Goo(self.world, kind, position)
        self.goos.append(goo)
        self.goo_of_body[goo.body] = goo
        return goo

    def link(self, a, b):
        """a distance joint with the settings of `a`'s type"""
        if a.kind.fixed_length:
            length = EDGE_LENGTH
        else:
            length = a.body.distance_to(b.body.position)
        self.world.create_joint(
            b2d.distance_joint_def(
                body_a=a.body,
                body_b=b.body,
                length=length,
                hertz=a.kind.hertz,
                damping_ratio=0.5,
                enable_spring=a.kind.enable_spring,
                collide_connected=True,
            )
        )
        a.neighbours.append(b)
        b.neighbours.append(a)
        self.links.append((a, b))

    def reachable_goos(self, pos):
        """(goo, squared distance) of the goos near `pos` that can take one more link
        and have no obstacle between them and `pos`"""
        result = []

        def callback(shape):
            goo = self.goo_of_body.get(shape.body)  # (the query also finds the ground)
            if goo is not None:
                d = b2d.distance_squared(goo.position, pos)
                if d <= REACH**2 and goo.has_room() and not self.blocked(goo, pos):
                    result.append((goo, d))
            return True  # continue the query

        box = b2d.aabb(
            lower_bound=(pos[0] - REACH, pos[1] - REACH),
            upper_bound=(pos[0] + REACH, pos[1] + REACH),
        )
        self.world.overlap_aabb(box, callback)
        return result

    def blocked(self, goo, pos):
        p = goo.position
        return self.world.cast_ray_closest(origin=p, translation=(pos[0] - p[0], pos[1] - p[1])).hit

    def find_placement(self, pos):
        """what a release at `pos` does: ("link", [a, b]) links two goos,
        ("goo", goos) places a new goo linked to `goos`, None: nothing"""
        near = self.reachable_goos(pos)
        if not near:
            return None
        if self.kind.hangs_on_one:
            closest, _ = min(near, key=lambda item: item[1])
            return ("goo", [closest])

        pairs = list(combinations(near, 2))
        unlinked = [(a, b) for (a, _), (b, _) in pairs if b not in a.neighbours]
        if unlinked:

            def gap(pair):  # squared distance of pos to the middle of the pair
                (ax, ay), (bx, by) = pair[0].position, pair[1].position
                return b2d.distance_squared(((ax + bx) / 2, (ay + by) / 2), pos)

            pair = min(unlinked, key=gap)
            if gap(pair) <= LINK_SNAP**2:
                return ("link", list(pair))

        linked = [(da + db, a, b) for (a, da), (b, db) in pairs if b in a.neighbours]
        if linked:
            d, a, b = min(linked, key=lambda item: item[0])
            if d <= MAX_PAIR_DISTANCE:
                return ("goo", [a, b])
        return None

    def on_mouse_down(self, event):
        self.is_mouse_down = True
        self.mouse_pos = event.world_position
        self.placement = self.find_placement(self.mouse_pos)
        self.dragging_camera = self.placement is None

    def on_mouse_move(self, event):
        if self.dragging_camera:
            self.frontend.drag_camera(event.world_delta)
        elif self.is_mouse_down:  # update the preview
            self.mouse_pos = event.world_position
            self.placement = self.find_placement(self.mouse_pos)

    def on_mouse_up(self, event):
        if self.is_mouse_down and not self.dragging_camera:
            placement = self.find_placement(event.world_position)
            if placement is not None:
                what, goos = placement
                if what == "link":
                    self.link(*goos)
                else:
                    new = self.add_goo(self.kind, event.world_position)
                    for goo in goos:
                        self.link(new, goo)
        self.placement = None
        self.is_mouse_down = self.dragging_camera = False

    def post_debug_draw(self):
        dd = self.debug_draw
        for a, b in self.links:
            dd.draw_segment(a.position, b.position, a.kind.edge_color)

        if self.placement is not None:  # the preview
            what, goos = self.placement
            if what == "link":
                dd.draw_segment(goos[0].position, goos[1].position, self.kind.edge_color)
            else:
                for goo in goos:
                    dd.draw_segment(goo.position, self.mouse_pos, self.kind.edge_color)
                self.draw_goo(self.mouse_pos, self.kind.color)

        for goo in self.goos:
            self.draw_goo(goo.position, goo.kind.color)

    def draw_goo(self, pos, color):
        """a ball with two eyes looking right (goos never rotate)"""
        dd = self.debug_draw
        x, y = pos[0], pos[1]
        dd.draw_solid_circle(transform=b2d.transform((x, y)), radius=GOO_RADIUS, color=color)
        dd.draw_circle((x, y), radius=GOO_RADIUS, color=(0, 0, 0))
        eye = GOO_RADIUS / 4
        offset = GOO_RADIUS / 2.5
        for ex in (x - offset, x + offset):
            ey = y - offset / 2
            dd.draw_solid_circle(
                transform=b2d.transform((ex, ey)), radius=eye, color=(255, 255, 255)
            )
            dd.draw_solid_circle(
                transform=b2d.transform((ex + eye / 2, ey)), radius=eye / 2, color=(0, 0, 0)
            )
