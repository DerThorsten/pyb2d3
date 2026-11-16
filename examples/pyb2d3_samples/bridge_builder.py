"""Bridge builder: draw a bridge while the world stands still, then send ever heavier
vehicles over it."""

import math

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.vehicles import VEHICLES, create_vehicle

GRID = 1.0  # new nodes are grid points
SNAP = 0.4  # distance to snap to an existing node
MAX_LENGTH = 4.0  # road / beam reach in x and in y (ropes can be any length)
GROUND, ROAD, CAR = 0x0001, 0x0002, 0x0004  # vehicles only touch ground and road

# name: (thickness, density, strength in N, color)
MATERIALS = {
    "road": (0.15, 2.0, 1500.0, b2d.HexColor.SaddleBrown),  # vehicles drive on it
    "beam": (0.08, 1.0, 1500.0, b2d.HexColor.Burlywood),  # pushes and pulls
    "rope": (0.03, 0.0, 1500.0, b2d.HexColor.Khaki),  # only pulls
}

# name: (top edge of the left cliff, top edge of the right cliff,
#        rocks in the gap: (x, top, half width))
LEVELS = {
    "gap": ((-8.0, 0.0), (8.0, 0.0), []),
    "wide gap with a rock": ((-12.0, 0.0), (12.0, 0.0), [(0.0, -3.0, 1.0)]),
    "climb": ((-8.0, 0.0), (8.0, 4.0), []),
}
# all anchors are grid points, and a straight road between the cliffs passes grid
# points at most 4 m apart (climb: 1 m up every 4 m)


def distance(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def span(p, q):
    """the larger of the x and y distances: beams reach a square, diagonals are longer"""
    return max(abs(q[0] - p[0]), abs(q[1] - p[1]))


@register_sample("Games", "Bridge Builder")
class BridgeBuilder(SampleBase):
    """Build a bridge, then test it: a car, a truck and a tank drive over it one after
    another, each heavier than the one before. While building the world stands still.

    Mouse (build): drag from a dot to draw a road, beam (both reach at most 4 m in x and
    in y) or rope.
    Double click a beam to erase it. Red dots are fixed to the cliffs. Only the road
    carries the vehicles.
    Mouse (test): drag the vehicles or the bridge around.
    Levels: the first starts with an example bridge, the others with an empty gap.
    Slider: vehicle weight, for a harder test.
    Hint: beams are bodies pinned to the nodes with revolute joints, ropes are distance
    joints that only pull. Joints break when overloaded, colors show the load.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.material = "road"
        self.weight = 1.0  # vehicle weight factor
        self.start = self.cursor = None
        self.parts, self.joints, self.vehicle = [], [], []
        self.building = True
        self.terrain = None
        self.set_level("gap")

        # an example on the first level: a truss (a road deck, beams on top, diagonals)
        deck = [self.add_node((x, 0.0)) for x in (-8.0, -4.0, 0.0, 4.0, 8.0)]
        top = [self.add_node((x, 2.0)) for x in (-6.0, -2.0, 2.0, 6.0)]
        self.beams = [(a, b, "road") for a, b in zip(deck[:-1], deck[1:])]
        self.beams += [(a, b, "beam") for a, b in zip(top[:-1], top[1:])]
        for k, t in enumerate(top):
            self.beams += [(deck[k], t, "beam"), (t, deck[k + 1], "beam")]

        if self.frontend.settings.headless:
            # nobody builds (e.g. the docs video): test right away, the tank already on
            # the bridge, so a short clip shows the load on the beams (at 0.9 of its
            # weight the example truss just holds it: up to 93% load)
            self.weight = 0.9
            self.to_test_mode()
            self.next_vehicle = len(VEHICLES) - 1
            self.send_vehicle(x=self.left[0] + 2.0)

        for widget in (
            widgets.RadioButtons("level", list(LEVELS), "gap", self.select_level),
            widgets.Separator(),
            widgets.RadioButtons("material", list(MATERIALS), self.material, self.set_material),
            widgets.Separator(),
            widgets.FloatSlider("vehicle weight", 0.5, 3.0, 0.1, self.weight, self.set_weight),
            widgets.Button("test / build", self.toggle),
            widgets.Button("clear", self.clear),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        top = max(self.left[1], self.right[1])
        return b2d.aabb(
            lower_bound=(self.left[0] - 8.0, -10.0), upper_bound=(self.right[0] + 8.0, top + 8.0)
        )

    # ---- levels ---------------------------------------------------------------------------

    def set_level(self, name):
        """the cliffs, rocks and anchor points of a level, no bridge"""
        self.to_build_mode()
        if self.terrain is not None:
            self.terrain.destroy()
        self.left, self.right, rocks = LEVELS[name]
        self.terrain = self.world.create_static_body(position=(0.0, 0.0))
        ground = b2d.shape_def(material=b2d.surface_material(friction=0.8))
        anchors = []
        for (x, y), side in ((self.left, -1.0), (self.right, 1.0)):
            # a cliff down to y = -10 with a wall at its far end; anchors on the face
            # and on the top (e.g. for tower braces)
            self.terrain.create_shape(
                ground, b2d.box(6.0, 0.5 * (y + 10.0), center=(x + side * 6.0, 0.5 * (y - 10.0)))
            )
            self.terrain.create_shape(ground, b2d.box(0.3, 1.0, center=(x + side * 11.7, y + 1.0)))
            anchors += [(x, y), (x, y - 2.0), (x, y - 4.0)]
            anchors += [(x + side * 2.0, y), (x + side * 4.0, y)]
        for x, top, half in rocks:
            self.terrain.create_shape(
                ground, b2d.box(half, 0.5 * (top + 10.0), center=(x, 0.5 * (top - 10.0)))
            )
            anchors += [(x - half, top), (x + half, top)]
        self.fixed = anchors
        self.nodes, self.beams = list(self.fixed), []

    def select_level(self, name):
        self.set_level(name)
        self.frontend.center_sample(margin_px=10)

    # ---- building -------------------------------------------------------------------------

    def set_material(self, value):
        self.material = value

    def set_weight(self, value):
        self.weight = value  # for the next vehicle

    def node_at(self, point):
        k = min(range(len(self.nodes)), key=lambda k: distance(self.nodes[k], point))
        return k if distance(self.nodes[k], point) < SNAP else None

    def add_node(self, point):
        k = self.node_at(point)
        if k is None:
            self.nodes.append(point)
            k = len(self.nodes) - 1
        return k

    def end_point(self, point):
        """a beam ends on a node or a grid point, at most MAX_LENGTH away in x and in y
        (ropes: any)"""
        limit = math.inf if self.material == "rope" else MAX_LENGTH
        start = self.nodes[self.start]
        k = self.node_at(point)
        if k is not None and span(start, self.nodes[k]) <= limit:
            return self.nodes[k]
        scale = min(1.0, limit / max(span(start, point), 1e-6))
        x, y = (start[i] + scale * (point[i] - start[i]) for i in (0, 1))
        grid = (round(x / GRID) * GRID, round(y / GRID) * GRID)
        return grid if span(start, grid) <= limit else (x, y)

    def clear(self):
        self.to_build_mode()
        self.nodes, self.beams = list(self.fixed), []

    def on_mouse_down(self, event):
        self.start = self.node_at(event.world_position) if self.building else None
        if self.start is None:
            super().on_mouse_down(event)
        else:
            self.cursor = self.end_point(event.world_position)

    def on_mouse_move(self, event):
        if self.start is None:
            super().on_mouse_move(event)
        else:
            self.cursor = self.end_point(event.world_position)

    def on_mouse_up(self, event):
        if self.start is not None:
            end = self.add_node(self.end_point(event.world_position))
            if end != self.start:
                self.beams.append((self.start, end, self.material))
            self.start = self.cursor = None
        super().on_mouse_up(event)

    def on_double_click(self, event):
        """erase the beam under the mouse"""
        if self.building and self.beams:
            p = event.world_position

            def gap(beam):  # distance of p to the beam's segment
                (ax, ay), (bx, by) = self.nodes[beam[0]], self.nodes[beam[1]]
                dx, dy = bx - ax, by - ay
                t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)
                t = min(max(t, 0.0), 1.0)
                return distance(p, (ax + t * dx, ay + t * dy))

            beam = min(self.beams, key=gap)
            if gap(beam) < SNAP:
                self.beams.remove(beam)
                # and the nodes (joints) no beam uses any more (not the anchors)
                used = {k for a, b, _ in self.beams for k in (a, b)}
                keep = [k for k in range(len(self.nodes)) if k < len(self.fixed) or k in used]
                index = {old: new for new, old in enumerate(keep)}
                self.nodes = [self.nodes[k] for k in keep]
                self.beams = [(index[a], index[b], name) for a, b, name in self.beams]

    # ---- testing --------------------------------------------------------------------------

    def toggle(self):
        if self.building:
            self.to_test_mode()
        else:
            self.to_build_mode()

    def to_build_mode(self):
        self.destroy_mouse_joint()
        for body in self.parts + self.vehicle:
            body.destroy()  # with its joints
        self.parts, self.joints, self.vehicle = [], [], []
        self.building = True

    def to_test_mode(self):
        """a small body per free node, a body per beam pinned to its two nodes, a
        distance joint per rope; then a car on the left cliff"""
        self.start = self.cursor = None
        self.building = False
        no_contacts = b2d.make_filter(category_bits=ROAD, mask_bits=0)
        node_bodies = []
        for k, node in enumerate(self.nodes):
            if k < len(self.fixed):
                node_bodies.append(self.anchor_body)
                continue
            body = self.world.create_dynamic_body(position=node)
            # about the mass of a beam: very light bodies between heavy ones make the
            # solver jitter (and the joint forces spike)
            node_def = b2d.shape_def(density=20.0, filter=no_contacts)
            body.create_shape(node_def, b2d.circle(radius=0.15))
            node_bodies.append(body)
            self.parts.append(body)

        # joints: (joint, strength, body + local point to draw it at (pins only));
        # members: (body, local point, body, local point, joint indices, thickness) for
        # drawing the load of every road / beam / rope over its shape
        self.members = []
        for a, b, name in self.beams:
            thickness, density, strength, color = MATERIALS[name]
            p, q = self.nodes[a], self.nodes[b]
            body_p, body_q = node_bodies[a], node_bodies[b]
            if name == "rope":
                length = distance(p, q)
                joint = self.world.create_distance_joint(
                    body_a=body_p,
                    body_b=body_q,
                    local_anchor_a=body_p.local_point(p),
                    local_anchor_b=body_q.local_point(q),
                    length=length,
                    enable_spring=True,  # no spring force (hertz 0): slack ...
                    enable_limit=True,  # ... up to its length
                    min_length=0.0,
                    max_length=length,
                )
                self.joints.append((joint, strength, None, None))
                ends = (body_p, body_p.local_point(p), body_q, body_q.local_point(q))
                self.members.append((*ends, [len(self.joints) - 1], 0.06))
                continue
            half = 0.5 * distance(p, q)
            body = self.world.create_dynamic_body(
                position=((p[0] + q[0]) / 2, (p[1] + q[1]) / 2),
                rotation=b2d.make_rot(math.atan2(q[1] - p[1], q[0] - p[0])),
            )
            # only the road carries the vehicles; its top is on the line between the
            # nodes (flush with the cliffs, no bump)
            road = name == "road"
            offset = -thickness if road else 0.0
            body.create_shape(
                b2d.shape_def(
                    density=density,
                    filter=b2d.make_filter(category_bits=ROAD, mask_bits=CAR if road else 0),
                    material=b2d.surface_material(friction=0.8, custom_color=color),
                ),
                b2d.capsule((-half, offset), (half, offset), thickness),
            )
            self.parts.append(body)
            for node_body, point in ((body_p, p), (body_q, q)):  # pinned to both nodes
                joint = self.world.create_revolute_joint(
                    body_a=node_body,
                    body_b=body,
                    local_anchor_a=node_body.local_point(point),
                    local_anchor_b=body.local_point(point),
                )
                self.joints.append((joint, strength, body, body.local_point(point)))
            ids = [len(self.joints) - 2, len(self.joints) - 1]
            self.members.append((body, (-half, offset), body, (half, offset), ids, thickness))
        self.stress = [0.0] * len(self.joints)
        self.next_vehicle = 0
        self.send_vehicle()

    def send_vehicle(self, x=None):
        """the next (heavier) vehicle starts on the left cliff (or at `x`)"""
        for body in self.vehicle:
            body.destroy()
        name = list(VEHICLES)[self.next_vehicle]
        vehicle_filter = b2d.make_filter(category_bits=CAR, mask_bits=GROUND | ROAD)
        edge, ground = self.left
        x = edge - 4.0 if x is None else x
        self.vehicle = create_vehicle(
            self.world, name, x, ground, vehicle_filter, weight=self.weight
        )
        self.next_vehicle += 1

    def update(self, dt):
        if self.building:  # the world stands still while building, the clock runs on
            self.world_time += dt
            self.world_iteration += 1
        else:
            super().update(dt)

    def pre_update(self, dt):
        """a vehicle that made it across makes room for the next one"""
        made_it = self.vehicle and self.vehicle[0].position.x > self.right[0] + 4.0
        if made_it and self.next_vehicle < len(VEHICLES):
            self.destroy_mouse_joint()
            self.send_vehicle()

    def post_update(self, dt):
        """break the joints whose force exceeds their strength"""
        for k, (joint, strength, _, _) in enumerate(self.joints):
            if joint.is_valid:
                force = joint.constraint_force
                self.stress[k] = math.hypot(force.x, force.y) / strength
                if self.stress[k] > 1.0:
                    joint.destroy()
            else:
                self.stress[k] = 1.0  # broken: shown red

    # ---- drawing --------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        (left, left_y), (right, right_y) = self.left, self.right
        low, high = min(left_y, right_y), max(left_y, right_y)
        if self.building:
            # the grid points a new beam can end on
            for i in range(int(left / GRID) - 4, int(right / GRID) + 5):
                for j in range(int((low - 5.0) / GRID), int((high + 6.0) / GRID) + 1):
                    dd.draw_point((i * GRID, j * GRID), 3.0, b2d.HexColor.DimGray)
            for a, b, name in self.beams:
                thickness, _, _, color = MATERIALS[name]
                dy = -thickness if name == "road" else 0.0  # the road's top on the line
                (ax, ay), (bx, by) = self.nodes[a], self.nodes[b]
                dd.draw_solid_capsule((ax, ay + dy), (bx, by + dy), thickness, color)
            for k, node in enumerate(self.nodes):
                color = b2d.HexColor.Red if k < len(self.fixed) else b2d.HexColor.White
                dd.draw_point(node, 10.0, color)
            if self.start is not None:
                dd.draw_segment(self.nodes[self.start], self.cursor, b2d.HexColor.White)
            text = "building: drag from a dot"
        else:
            # load (force / strength), green -> red: members by the average of their
            # joints, the joints (pins) as dots
            def color(load):
                load = min(load, 1.0)
                return b2d.rgb_to_hex_color(int(255 * load), int(255 * (1.0 - load)), 0)

            for body_p, p, body_q, q, ids, thickness in self.members:
                load = sum(self.stress[k] for k in ids) / len(ids)
                ends = tuple(body_p.world_point(p)), tuple(body_q.world_point(q))
                dd.draw_solid_capsule(*ends, thickness, color(load))
            for (joint, _, body, local), load in zip(self.joints, self.stress):
                if body is not None and joint.is_valid:
                    dd.draw_point(tuple(body.world_point(local)), 8.0, color(load))
            name = list(VEHICLES)[self.next_vehicle - 1]
            p = self.vehicle[0].position
            if p.y < low - 1.0:
                text = f"the {name} fell!"
            elif p.x > right + 1.0 and self.next_vehicle == len(VEHICLES):
                text = "all vehicles made it!"
            else:
                text = f"vehicle {self.next_vehicle} / {len(VEHICLES)}: the {name}"
        dd.draw_string((left, high + 6.0), text, b2d.HexColor.White)
