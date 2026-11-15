"""Ports of box2d's samples/sample_collision.cpp."""

import math

import numpy as np
import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample, widgets

from ._collision_helpers import (
    BodySlotsSample,
    ProxyPairSample,
    TransformDragSample,
    colors,
    draw_geometry,
    draw_manifold,
    octagon_points,
    with_position,
)
from ._common import Box2dSample


def setter(obj, name):
    return lambda value: setattr(obj, name, value)


@register_sample("Collision", "Shape Distance")
class ShapeDistance(ProxyPairSample):
    """Distance between two convex shapes (GJK), optionally stepping through the simplexes."""

    camera_center = (0.0, 0.0)
    camera_zoom = 3.0
    simplex_capacity = 20

    def __init__(self, frontend, settings):
        super().__init__(
            frontend,
            settings,
            segment=b2d.segment((-0.5, 0.0), (0.5, 0.0)),
            box=b2d.make_square(0.5),
            type_a="box",
            type_b="box",
            radius_a=0.0,
            radius_b=0.0,
        )
        self.cache = b2d.SimplexCache()
        self.use_cache = False
        self.draw_simplex = False
        self.simplex_index = 0

        add = self.frontend.add_widget
        self.add_shape_widgets()
        add(widgets.Checkbox("use cache", self.use_cache, setter(self, "use_cache")))
        add(widgets.Checkbox("draw simplex", self.draw_simplex, self.set_draw_simplex))
        add(widgets.IntSlider("index", 0, self.simplex_capacity - 1, 1, 0, setter(self, "simplex_index")))

    def set_draw_simplex(self, value):
        self.draw_simplex = value
        self.simplex_index = 0

    @staticmethod
    def witness_points(simplex):
        if simplex.count == 1:
            return simplex.v1.w_a, simplex.v1.w_b
        vertices = (simplex.v1, simplex.v2, simplex.v3)[: simplex.count]
        point_a = sum((v.a * v.w_a for v in vertices), b2d.Vec2(0, 0))
        if simplex.count == 2:
            return point_a, sum((v.a * v.w_b for v in vertices), b2d.Vec2(0, 0))
        return point_a, point_a

    def post_debug_draw(self):
        dd = self.debug_draw
        distance_input = b2d.DistanceInput()
        distance_input.proxy_a = self.proxy_a
        distance_input.proxy_b = self.proxy_b
        distance_input.transform = self.transform
        distance_input.use_radii = self.radius_a > 0.0 or self.radius_b > 0.0
        if not self.use_cache:
            self.cache = b2d.SimplexCache()
        output, simplexes = b2d.compute_shape_distance(distance_input, self.cache, self.simplex_capacity)

        # shape A is at the origin, so the distance output is in world coordinates
        self.draw_shape(self.type_a, b2d.Transform(), self.radius_a, colors.Cyan)
        self.draw_shape(self.type_b, self.transform, self.radius_b, colors.Bisque)

        if self.draw_simplex and simplexes:
            index = min(self.simplex_index, len(simplexes) - 1)
            simplex = simplexes[index]
            if index > 0:
                # the first recorded simplex does not have valid barycentric coordinates
                point_a, point_b = self.witness_points(simplex)
                dd.draw_segment(point_a, point_b, colors.White)
                dd.draw_point(point_a, 10.0, colors.White)
                dd.draw_point(point_b, 10.0, colors.White)
            vertices = (simplex.v1, simplex.v2, simplex.v3)[: simplex.count]
            for vertex, color in zip(vertices, (colors.Red, colors.Green, colors.Blue)):
                dd.draw_point(vertex.w_a, 10.0, color)
                dd.draw_point(vertex.w_b, 10.0, color)
        else:
            dd.draw_segment(output.point_a, output.point_b, colors.DimGray)
            dd.draw_point(output.point_a, 10.0, colors.White)
            dd.draw_point(output.point_b, 10.0, colors.White)
            dd.draw_segment(output.point_a, output.point_a + 0.5 * output.normal, colors.Yellow)

        self.draw_indices()
        dd.draw_string(
            b2d.mid_point(output.point_a, output.point_b),
            f"distance = {output.distance:.2f}, iterations = {output.iterations}",
            colors.White,
        )


@register_sample("Collision", "Dynamic Tree")
class DynamicTree(Box2dSample):
    """Tests the box2d bounding volume hierarchy (BVH).

    The dynamic tree can be used independently as a spatial data structure.
    """

    camera_center = (500.0, 500.0)
    camera_zoom = 25.0 * 21.0
    aabb_margin = 0.1

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.rng = np.random.default_rng()
        self.fill = 0.25
        self.move_fraction = 0.05
        self.move_delta = 0.1
        self.ratio = 5.0
        self.grid = 1.0
        # box2d uses 1000 x 1000 in release and 100 x 100 in debug builds
        self.row_count = 100
        self.column_count = 100
        self.build_tree()

        self.start_point = b2d.Vec2(0, 0)
        self.end_point = b2d.Vec2(0, 0)
        self.mode = None
        self.hits = set()

        add = self.frontend.add_widget

        def rebuilding(name):
            def callback(value):
                setattr(self, name, value)
                self.build_tree()

            return callback

        add(widgets.IntSlider("rows", 0, 1000, 1, self.row_count, rebuilding("row_count")))
        add(widgets.IntSlider("columns", 0, 1000, 1, self.column_count, rebuilding("column_count")))
        add(widgets.FloatSlider("fill", 0.0, 1.0, 0.01, self.fill, rebuilding("fill")))
        add(widgets.FloatSlider("grid", 0.5, 2.0, 0.01, self.grid, rebuilding("grid")))
        add(widgets.FloatSlider("ratio", 1.0, 10.0, 0.01, self.ratio, rebuilding("ratio")))
        add(widgets.FloatSlider("move", 0.0, 1.0, 0.01, self.move_fraction, setter(self, "move_fraction")))
        add(widgets.FloatSlider("delta", 0.0, 1.0, 0.01, self.move_delta, setter(self, "move_delta")))

    def build_tree(self):
        rng = self.rng
        rows, columns = np.meshgrid(np.arange(self.row_count), np.arange(self.column_count), indexing="ij")
        corners = np.stack([-40.0 + columns.ravel() * self.grid, -4.0 + rows.ravel() * self.grid], axis=1)
        corners = corners[rng.uniform(0.0, 1.0, len(corners)) <= self.fill]
        count = len(corners)

        ratio = rng.uniform(1.0, self.ratio, count)
        width = rng.uniform(0.1, 0.5, count)
        wide = rng.uniform(-1.0, 1.0, count) > 0.0
        self.positions = corners
        self.widths = np.where(wide[:, None], np.stack([ratio * width, width], 1), np.stack([width, ratio * width], 1))
        self.lower = corners.copy()
        self.upper = corners + self.widths
        self.fat_lower = self.lower - self.aabb_margin
        self.fat_upper = self.upper + self.aabb_margin

        self.tree = b2d.DynamicTree(16)
        self.proxy_ids = [
            self.tree.create_proxy(b2d.aabb(lo, hi), b2d.DEFAULT_CATEGORY_BITS, i)
            for i, (lo, hi) in enumerate(zip(self.fat_lower, self.fat_upper))
        ]
        self.boxes = [b2d.aabb(lo, hi) for lo, hi in zip(self.lower, self.upper)]

    def on_mouse_down(self, event):
        if self.mode is None:
            self.mode = "query" if "shift" in self.pressed_keys() else "ray"
            self.start_point = self.end_point = event.world_position

    def on_mouse_up(self, event):
        self.mode = None

    def on_mouse_move(self, event):
        self.end_point = event.world_position

    def query_box(self):
        return b2d.aabb(b2d.min(self.start_point, self.end_point), b2d.max(self.start_point, self.end_point))

    def query(self):
        hits = set()
        if self.mode == "query":

            def found(proxy_id, user_data):
                hits.add(user_data)
                return True

            self.tree.overlap_aabb(self.query_box(), found)
        elif self.mode == "ray":

            def found(ray_input, proxy_id, user_data):
                hits.add(user_data)
                return ray_input.max_fraction

            ray = b2d.ray_cast_input(self.start_point, self.end_point - self.start_point, 1.0)
            self.tree.cast_ray(ray, found)
        self.hits = hits

    def move_proxies(self):
        moving = np.flatnonzero(self.move_fraction > self.rng.uniform(0.0, 1.0, len(self.positions)))
        delta = self.move_delta * self.rng.uniform(-1.0, 1.0, (len(moving), 2))
        self.positions[moving] += delta
        self.lower[moving] = self.positions[moving] + delta
        self.upper[moving] = self.lower[moving] + self.widths[moving]
        for i in moving:
            self.boxes[i] = b2d.aabb(self.lower[i], self.upper[i])

        contained = np.all(self.fat_lower[moving] <= self.lower[moving], axis=1) & np.all(
            self.upper[moving] <= self.fat_upper[moving], axis=1
        )
        moved = moving[~contained]
        self.fat_lower[moved] = self.lower[moved] - self.aabb_margin
        self.fat_upper[moved] = self.upper[moved] + self.aabb_margin
        for i in moved:
            self.tree.move_proxy(self.proxy_ids[i], b2d.aabb(self.fat_lower[i], self.fat_upper[i]))

    def post_update(self, dt):
        self.query()
        self.move_proxies()
        self.tree.validate()

    def post_debug_draw(self):
        dd = self.debug_draw
        if self.mode == "query":
            dd.draw_aabb(self.query_box(), colors.White)
        elif self.mode == "ray":
            dd.draw_segment(self.start_point, self.end_point, colors.White)
            dd.draw_point(self.start_point, 5.0, colors.Green)
            dd.draw_point(self.end_point, 5.0, colors.Red)

        hits = self.hits
        for i, box in enumerate(self.boxes):
            dd.draw_aabb(box, colors.Green if i in hits else colors.Blue)


_CAST_RAY = {
    b2d.Circle: b2d.cast_ray_circle,
    b2d.Capsule: b2d.cast_ray_capsule,
    b2d.Polygon: b2d.cast_ray_polygon,
    b2d.Segment: b2d.cast_ray_segment,
}


@register_sample("Collision", "Ray Cast")
class RayCast(TransformDragSample):
    """Ray casts against the individual shape types."""

    camera_center = (0.0, 20.0)
    camera_zoom = 17.5
    mouse_modes = {None: "ray", "shift": "drag", "ctrl": "rotate"}
    rotate_scale = 0.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.shapes = [
            b2d.circle((0.0, 0.0), 2.0),
            b2d.capsule((-1.0, 1.0), (1.0, -1.0), 1.5),
            b2d.make_box(2.0, 2.0),
            b2d.polygon(points=[(-2.0, 0.0), (2.0, 0.0), (2.0, 3.0)]),
            b2d.segment((-3.0, 0.0), (3.0, 0.0)),
        ]
        self.ray_start = b2d.Vec2(0.0, 30.0)
        self.ray_end = b2d.Vec2(0.0, 0.0)
        self.show_fraction = False

        add = self.frontend.add_widget
        self.add_transform_widgets()
        add(widgets.Checkbox("show fraction", self.show_fraction, setter(self, "show_fraction")))
        add(widgets.Button("Reset", self.reset_transform))

    def on_mouse_down(self, event):
        super().on_mouse_down(event)
        if self.mode == "ray":
            self.ray_start = event.world_position

    def on_mouse_move(self, event):
        super().on_mouse_move(event)
        if self.mode == "ray":
            self.ray_end = event.world_position

    def post_debug_draw(self):
        offset = b2d.Vec2(-20.0, 20.0)
        rotation = b2d.make_rot(self.angle)
        translation = self.ray_end - self.ray_start
        max_fraction = 1.0
        hit = None
        for shape in self.shapes:
            transform = b2d.transform(p=self.position + offset, q=rotation)
            draw_geometry(self.debug_draw, shape, transform, colors.Yellow)

            ray = b2d.ray_cast_input(
                b2d.inv_transform_point(transform, self.ray_start),
                b2d.inv_rotate_vector(rotation, translation),
                max_fraction,
            )
            output = _CAST_RAY[type(shape)](shape, ray)
            if output.hit:
                hit_point = b2d.transform_point(transform, output.point)
                hit = (output.fraction, hit_point, b2d.rotate_vector(rotation, output.normal))
                max_fraction = output.fraction
            offset = offset + (10.0, 0.0)
        self.draw_ray(hit)

    def draw_ray(self, hit):
        dd = self.debug_draw
        p1, p2 = self.ray_start, self.ray_end
        if hit is None:
            dd.draw_segment(p1, p2, colors.White)
            dd.draw_point(p1, 5.0, colors.Green)
            dd.draw_point(p2, 5.0, colors.Red)
            return

        fraction, hit_point, normal = hit
        if fraction == 0.0:
            p = hit_point
            dd.draw_point(hit_point, 5.0, colors.Peru)
        else:
            p = p1 + fraction * (p2 - p1)
            dd.draw_segment(p1, p, colors.White)
            dd.draw_point(p1, 5.0, colors.Green)
            dd.draw_point(hit_point, 5.0, colors.White)
            dd.draw_segment(p, p + normal, colors.Violet)

        if self.show_fraction:
            dd.draw_string(p + (0.05, -0.02), f"{fraction:.2f}", colors.White)


class _CastContext:
    """Up to three hits gathered by the cast callbacks of the Cast World sample."""

    def __init__(self, sample):
        self.sample = sample
        self.hits = []  # (fraction, point, normal)

    def skip(self, shape, fraction):
        # ignore a specific shape, also ignore initial overlap
        return self.sample.is_ignored(shape) or fraction == 0.0

    def any(self, shape, point, normal, fraction):
        """Any hit: check for obstruction, the hit is not necessarily the closest one."""
        if self.skip(shape, fraction):
            return -1.0
        self.hits = [(fraction, point, normal)]
        # terminate the cast
        return 0.0

    def closest(self, shape, point, normal, fraction):
        """Closest hit: clip the cast to the current fraction."""
        if self.skip(shape, fraction):
            return -1.0
        self.hits = [(fraction, point, normal)]
        return fraction

    def multiple(self, shape, point, normal, fraction):
        """Up to three hits in the (unsorted) order box2d reports them."""
        if self.skip(shape, fraction):
            return -1.0
        self.hits.append((fraction, point, normal))
        # stop once the buffer is full, else continue without clipping
        return 0.0 if len(self.hits) == 3 else 1.0

    def sorted(self, shape, point, normal, fraction):
        """The three closest hits, sorted by fraction."""
        if self.skip(shape, fraction):
            return -1.0
        if len(self.hits) == 3 and fraction >= self.hits[2][0]:
            # not closer: don't consider fractions further than the largest one acquired
            return self.hits[2][0]
        self.hits = sorted(self.hits + [(fraction, point, normal)], key=lambda hit: hit[0])[:3]
        return self.hits[2][0] if len(self.hits) == 3 else 1.0


@register_sample("Collision", "Cast World")
class CastWorld(BodySlotsSample):
    """Ray and shape casts on a world. Initial overlap is ignored, so is the shape in slot 7."""

    camera_center = (2.0, 14.0)
    camera_zoom = 25.0 * 0.75
    modes = ("Any", "Closest", "Multiple", "Sorted")
    cast_types = ("Ray", "Circle", "Capsule", "Polygon")

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        ground.create_shape(b2d.shape_def(), b2d.segment((-40.0, 0.0), (40.0, 0.0)))

        self.polygons = [
            b2d.polygon(points=[(-0.1, 0.0), (0.1, 0.0), (0.0, 1.5)], radius=0.5),
            b2d.polygon(points=octagon_points()),
        ]
        self.box = b2d.make_box(0.5, 0.5)
        self.capsule = b2d.capsule((-0.5, 0.0), (0.5, 0.0), 0.25)
        self.circle = b2d.circle((0.0, 0.0), 0.5)
        self.segment = b2d.segment((-1.0, 0.0), (1.0, 0.0))

        self.mode = "Closest"
        self.cast_type = "Ray"
        self.cast_radius = 0.5
        self.simple = False

        self.ray_start = b2d.Vec2(-20.0, 10.0)
        self.ray_end = b2d.Vec2(20.0, 10.0)
        self.dragging = False
        self.angle = 0.0
        self.base_angle = 0.0
        self.angle_anchor = b2d.Vec2(0.0, 0.0)
        self.rotating = False

        add = self.frontend.add_widget
        add(widgets.Checkbox("Simple", self.simple, setter(self, "simple")))
        add(widgets.Dropdown("Type", list(self.cast_types), self.cast_type, setter(self, "cast_type")))
        add(widgets.FloatSlider("Radius", 0.0, 2.0, 0.1, self.cast_radius, setter(self, "cast_radius")))
        add(widgets.Dropdown("Mode", list(self.modes), self.mode, setter(self, "mode")))
        self.add_slot_widgets(["Polygon", "Box", "Circle", "Capsule", "Segment", "Chain"])

    def body_options(self, slot):
        body_type = (b2d.BodyType.STATIC, b2d.BodyType.KINEMATIC, b2d.BodyType.DYNAMIC)[slot % 3]
        if body_type == b2d.BodyType.DYNAMIC:
            return dict(type=body_type, gravity_scale=0.0)
        return dict(type=body_type)

    def create_shape(self, body, kind, slot):
        shape_def = b2d.shape_def()
        if kind == 5:
            points = [(1.0, 0.0), (-1.0, 0.0), (-1.0, -1.0), (1.0, -1.0)]
            body.create_chain(b2d.chain_def(points=points, is_loop=True))
            return
        shape = (self.polygons[slot & 1], self.box, self.circle, self.capsule, self.segment)[kind]
        body.create_shape(shape_def, shape)

    def on_mouse_down(self, event):
        shift = "shift" in self.pressed_keys()
        if not shift and not self.rotating:
            self.ray_start = self.ray_end = event.world_position
            self.dragging = True
        elif shift and not self.dragging:
            self.rotating = True
            self.angle_anchor = event.world_position
            self.base_angle = self.angle

    def on_mouse_up(self, event):
        self.dragging = False
        self.rotating = False

    def on_mouse_move(self, event):
        if self.dragging:
            self.ray_end = event.world_position
        elif self.rotating:
            self.angle = self.base_angle + (event.world_position - self.angle_anchor).x

    def cast_shape(self):
        """The swept shape (as geometry for drawing) and its proxy."""
        rotation = b2d.make_rot(self.angle)
        r = self.cast_radius
        if self.cast_type == "Circle":
            shape = b2d.circle((0.0, 0.0), r)
            return shape, b2d.make_proxy([shape.center], r)
        if self.cast_type == "Capsule":
            shape = b2d.capsule(
                b2d.rotate_vector(rotation, (-0.25, 0.0)), b2d.rotate_vector(rotation, (0.25, 0.0)), r
            )
            return shape, b2d.make_proxy([shape.center1, shape.center2], r)
        shape = b2d.make_offset_rounded_box(0.125, 0.25, (0.0, 0.0), rotation, r)
        return shape, b2d.make_proxy(shape.vertices, shape.radius)

    def post_debug_draw(self):
        dd = self.debug_draw
        translation = self.ray_end - self.ray_start

        if self.simple:
            # this version doesn't have a callback, so it doesn't skip the ignored shape
            result = self.world.cast_ray_closest(self.ray_start, translation)
            if result.hit and result.fraction > 0.0:
                dd.draw_point(result.point, 5.0, colors.Green)
                dd.draw_segment(self.ray_start, self.ray_start + result.fraction * translation, colors.LightGray)
                dd.draw_segment(result.point, result.point + 0.5 * result.normal, colors.Magenta)
            else:
                dd.draw_segment(self.ray_start, self.ray_end, colors.LightGray)
        else:
            context = _CastContext(self)
            callback = getattr(context, self.mode.lower())
            shape = None
            if self.cast_type == "Ray":
                self.world.cast_ray(self.ray_start, translation, callback)
            else:
                shape, proxy = self.cast_shape()
                self.world.cast_shape(proxy, translation, callback, origin=self.ray_start)

            for (fraction, point, normal), color in zip(context.hits, (colors.Red, colors.Green, colors.Blue)):
                c = self.ray_start + fraction * translation
                dd.draw_point(point, 5.0, color)
                dd.draw_segment(self.ray_start, c, colors.LightGray)
                dd.draw_segment(point, point + normal, colors.Magenta)
                # the swept shape rests at the contact position c
                if shape is not None:
                    draw_geometry(dd, shape, b2d.transform(p=c), colors.Yellow)

            if not context.hits:
                dd.draw_segment(self.ray_start, self.ray_end, colors.LightGray)
                # no hit, so the swept shape rests at the end of the ray
                if shape is not None:
                    color = colors.Gray if self.cast_type == "Circle" else colors.Yellow
                    draw_geometry(dd, shape, b2d.transform(p=self.ray_end), color)

        dd.draw_point(self.ray_start, 5.0, colors.Green)
        self.draw_ignore_label("ign")


@register_sample("Collision", "Overlap World")
class OverlapWorld(BodySlotsSample):
    """Shape overlap queries on a world: overlapped shapes are destroyed, the shape in slot 7 is skipped."""

    camera_center = (0.0, 10.0)
    camera_zoom = 25.0 * 0.7
    max_doomed = 16
    query_shapes = ("Circle", "Capsule", "Box")

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.polygons = [
            b2d.polygon(points=[(-0.5, 0.0), (0.5, 0.0), (0.0, 1.5)]),
            b2d.polygon(points=[(-0.1, 0.0), (0.1, 0.0), (0.0, 1.5)]),
            b2d.polygon(points=octagon_points()),
            b2d.make_box(0.5, 0.5),
        ]
        self.shapes = self.polygons + [
            b2d.circle((0.0, 0.0), 0.5),
            b2d.capsule((-0.5, 0.0), (0.5, 0.0), 0.25),
            b2d.segment((-1.0, 0.0), (1.0, 0.0)),
        ]

        self.shape_type = "Circle"
        self.position = b2d.Vec2(0.0, 10.0)
        self.angle = 0.0
        self.base_angle = 0.0
        self.start_position = b2d.Vec2(0.0, 0.0)
        self.dragging = False
        self.rotating = False

        self.create_n(0, 10)

        self.add_slot_widgets(["Polygon 1", "Polygon 2", "Polygon 3", "Box", "Circle", "Capsule", "Segment"])
        self.frontend.add_widget(
            widgets.RadioButtons("Overlap Shape", list(self.query_shapes), self.shape_type, setter(self, "shape_type"))
        )

    def create_shape(self, body, kind, slot):
        body.create_shape(b2d.shape_def(), self.shapes[kind])

    def on_mouse_down(self, event):
        shift = "shift" in self.pressed_keys()
        if not shift and not self.rotating:
            self.dragging = True
            self.position = event.world_position
        elif shift and not self.dragging:
            self.rotating = True
            self.start_position = event.world_position
            self.base_angle = self.angle

    def on_mouse_up(self, event):
        self.dragging = False
        self.rotating = False

    def on_mouse_move(self, event):
        if self.dragging:
            self.position = event.world_position
        elif self.rotating:
            self.angle = self.base_angle + (event.world_position - self.start_position).x

    def query_shape(self):
        """The query shape built near the origin (placed with the query origin) and its proxy."""
        rotation = b2d.make_rot(self.angle)
        if self.shape_type == "Circle":
            shape = b2d.circle((0.0, 0.0), 1.0)
            return shape, b2d.make_proxy([shape.center], shape.radius)
        if self.shape_type == "Capsule":
            shape = b2d.capsule(b2d.rotate_vector(rotation, (-1.0, 0.0)), b2d.rotate_vector(rotation, (1.0, 0.0)), 0.5)
            return shape, b2d.make_proxy([shape.center1, shape.center2], shape.radius)
        shape = b2d.make_offset_box(2.0, 0.5, (0.0, 0.0), rotation)
        return shape, b2d.make_proxy(shape.vertices, shape.radius)

    def post_update(self, dt):
        doomed = []

        def overlap(shape):
            if not self.is_ignored(shape) and len(doomed) < self.max_doomed:
                doomed.append(shape.body)
            return True

        _, proxy = self.query_shape()
        self.world.overlap_shape(proxy, overlap, origin=self.position)
        for body in doomed:
            if body in self.bodies:
                self.destroy_slot(self.bodies.index(body))

    def post_debug_draw(self):
        dd = self.debug_draw
        shape, _ = self.query_shape()
        if isinstance(shape, b2d.Polygon):
            dd.draw_polygon(np.asarray(shape.vertices) + tuple(self.position), colors.White)
        else:
            draw_geometry(dd, shape, b2d.transform(p=self.position), colors.White)
        self.draw_ignore_label("skip")


def _collide(shape_a, shape_b, transform, cache=None):
    """b2Collide* for the pair of shape types."""
    name = _COLLIDE[type(shape_a), type(shape_b)]
    if cache is not None:
        return getattr(b2d, name)(shape_a, shape_b, transform, cache)
    return getattr(b2d, name)(shape_a, shape_b, transform)


_COLLIDE = {
    (b2d.Circle, b2d.Circle): "collide_circles",
    (b2d.Capsule, b2d.Circle): "collide_capsule_and_circle",
    (b2d.Segment, b2d.Circle): "collide_segment_and_circle",
    (b2d.Polygon, b2d.Circle): "collide_polygon_and_circle",
    (b2d.Capsule, b2d.Capsule): "collide_capsules",
    (b2d.Polygon, b2d.Capsule): "collide_polygon_and_capsule",
    (b2d.Segment, b2d.Capsule): "collide_segment_and_capsule",
    (b2d.Polygon, b2d.Polygon): "collide_polygons",
    (b2d.Segment, b2d.Polygon): "collide_segment_and_polygon",
    (b2d.ChainSegment, b2d.Circle): "collide_chain_segment_and_circle",
    (b2d.ChainSegment, b2d.Capsule): "collide_chain_segment_and_capsule",
    (b2d.ChainSegment, b2d.Polygon): "collide_chain_segment_and_polygon",
}


class _ManifoldDrawing:
    """Manifold drawing options shared by the Manifold and Smooth Manifold samples."""

    def add_manifold_checkboxes(self, labels):
        for name, label in labels.items():
            setattr(self, name, False)
            self.frontend.add_widget(widgets.Checkbox(label, False, setter(self, name)))

    def draw_manifold(self, manifold, transform_a, **kwargs):
        draw_manifold(
            self.debug_draw,
            manifold,
            transform_a,
            show_ids=self.show_ids,
            show_separation=self.show_separation,
            **kwargs,
        )


def _rounded_square(round_):
    h = 0.5 - round_
    return b2d.make_rounded_box(h, h, round_)


@register_sample("Collision", "Manifold")
class Manifold(_ManifoldDrawing, TransformDragSample):
    """Tests manifolds and contact points."""

    camera_center = (1.8, 0.0)
    camera_zoom = 25.0 * 0.45

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings, position=(0.17, 1.12))
        self.round = 0.1
        self.enable_caching = True
        self.reset_caches()
        self.wedge = b2d.compute_hull([(-0.1, -0.5), (0.1, -0.5), (0.0, 0.5)])

        p1s = [(0.175740838, 0.224936664), (-0.301293969, 0.194021404), (-0.105151534, -0.432157338)]
        p2s = [(-0.427884758, -0.225028217), (0.0566576123, -0.128772855), (0.176625848, 0.338923335)]
        self.wedges = (b2d.polygon(points=p1s, radius=0.158798501), b2d.polygon(points=p2s, radius=0.205900759))

        def chain_segment(ghost1, point1, point2, ghost2):
            return b2d.chain_segment(b2d.segment(point1, point2), ghost1, ghost2)

        self.chain_segment1 = chain_segment((2.0, 1.0), (1.0, 1.0), (-1.0, 0.0), (-2.0, 0.0))
        self.chain_segment2 = chain_segment((3.0, 1.0), (2.0, 1.0), (1.0, 1.0), (-1.0, 0.0))

        add = self.frontend.add_widget
        self.add_transform_widgets()
        add(widgets.FloatSlider("round", 0.0, 0.4, 0.1, self.round, setter(self, "round")))
        self.add_manifold_checkboxes(
            {
                "show_count": "show count",
                "show_ids": "show ids",
                "show_separation": "show separation",
                "show_anchors": "show anchors",
            }
        )
        add(widgets.Checkbox("enable caching", self.enable_caching, setter(self, "enable_caching")))
        add(widgets.Button("Reset", self.reset_transform))

    def reset_caches(self):
        self.rox_caches = (b2d.SimplexCache(), b2d.SimplexCache())
        self.capsule_caches = (b2d.SimplexCache(), b2d.SimplexCache())

    def rows(self):
        """Rows of (shape A, shape B, draw the polygon cores) triples."""
        circle = b2d.circle((0.0, 0.0), 0.5)
        capsule = b2d.capsule((-0.5, 0.0), (0.5, 0.0), 0.25)
        segment = b2d.segment((-1.0, 0.0), (1.0, 0.0))
        square = b2d.make_square(0.5)
        rounded_square = b2d.make_square(0.5)
        rounded_square.radius = self.round
        rox = _rounded_square(self.round)
        wox = b2d.make_polygon(self.wedge, self.round)
        triangle = b2d.polygon(points=[(-0.05, 0.0), (0.05, 0.0), (0.0, 0.1)])
        return [
            [
                (b2d.circle((0.0, 0.0), 0.5), b2d.circle((0.0, 0.0), 1.0), False),
                (capsule, circle, False),
                (segment, circle, False),
                (rounded_square, circle, False),
                (capsule, b2d.capsule((0.25, 0.0), (1.0, 0.0), 0.1), False),
                (
                    b2d.make_offset_box(0.25, 1.0, (1.0, -1.0), 0.25 * math.pi),
                    b2d.capsule((-0.4, 0.0), (-0.1, 0.0), 0.1),
                    False,
                ),
                (segment, capsule, False),
            ],
            [
                (square, square, False),
                (b2d.make_box(2.0, 0.1), b2d.make_square(0.25), False),
                (square, rox, False),
                (rox, rox, False),
                (segment, rox, False),
                (wox, wox, True),
                (*self.wedges, True),
            ],
            [(b2d.make_box(1.0, 1.0), triangle, False)],
        ]

    def collide(self, offset, shape_a, shape_b, cache=None):
        transform_a = b2d.transform(p=offset)
        transform_b = b2d.transform(p=self.position + offset, q=b2d.make_rot(self.angle))
        manifold = _collide(shape_a, shape_b, b2d.inv_mul_transforms(transform_a, transform_b), cache)
        return transform_a, transform_b, manifold

    def draw_pair(self, offset, shape_a, shape_b, draw_cores):
        dd = self.debug_draw
        transform_a, transform_b, manifold = self.collide(offset, shape_a, shape_b)
        for shape, transform, color in (
            (shape_a, transform_a, colors.Aquamarine),
            (shape_b, transform_b, colors.PaleGoldenrod),
        ):
            draw_geometry(dd, shape, transform, color)
            if draw_cores:
                draw_geometry(dd, shape, transform, color, radius=0.0)
        self.draw_local_manifold(manifold, transform_a, transform_b)

    def draw_local_manifold(self, manifold, transform_a, transform_b):
        if self.show_count:
            self.debug_draw.draw_string(
                b2d.mid_point(transform_a.p, transform_b.p), str(manifold.point_count), colors.White
            )
        if self.show_anchors:
            self.draw_manifold(manifold, transform_a, point_size=5.0, point_color=colors.Red)
        else:
            self.draw_manifold(manifold, transform_a)

    def draw_chain_segments(self, transform_a):
        dd = self.debug_draw
        tp = lambda p: b2d.transform_point(transform_a, p)  # noqa: E731
        for chain_segment, ghost_is_next in ((self.chain_segment1, True), (self.chain_segment2, False)):
            p1, p2 = tp(chain_segment.segment.point1), tp(chain_segment.segment.point2)
            dd.draw_segment(p1, p2, colors.Aquamarine)
            dd.draw_point(p1, 4.0, colors.Aquamarine)
            dd.draw_point(p2, 4.0, colors.Aquamarine)
            if ghost_is_next:
                dd.draw_segment(p2, tp(chain_segment.ghost2), colors.LightGray)
            else:
                dd.draw_segment(tp(chain_segment.ghost1), p1, colors.LightGray)

    def post_debug_draw(self):
        if not self.enable_caching:
            self.reset_caches()
        dd = self.debug_draw
        increment = b2d.Vec2(4.0, 0.0)

        for y, row in zip((-5.0, 0.0, 5.0), self.rows()):
            offset = b2d.Vec2(-10.0, y)
            for shape_a, shape_b, draw_cores in row:
                self.draw_pair(offset, shape_a, shape_b, draw_cores)
                offset = offset + increment

        # chain-segment vs circle
        circle = b2d.circle((0.0, 0.0), 0.5)
        segment = self.chain_segment1
        transform_a, transform_b, manifold = self.collide(offset, segment, circle)
        tp = lambda p: b2d.transform_point(transform_a, p)  # noqa: E731
        p1, p2 = tp(segment.segment.point1), tp(segment.segment.point2)
        dd.draw_segment(tp(segment.ghost1), p1, colors.LightGray)
        dd.draw_segment(p1, p2, colors.Aquamarine)
        dd.draw_segment(p2, tp(segment.ghost2), colors.LightGray)
        draw_geometry(dd, circle, transform_b, colors.PaleGoldenrod)
        self.draw_local_manifold(manifold, transform_a, transform_b)
        offset = offset + 2.0 * increment

        # chain-segment vs rounded polygon and chain-segment vs capsule
        rox = _rounded_square(self.round)
        capsule = b2d.capsule((-0.5, 0.0), (0.5, 0.0), 0.25)
        for shape, caches in ((rox, self.rox_caches), (capsule, self.capsule_caches)):
            manifolds = []
            for chain_segment, cache in zip((self.chain_segment1, self.chain_segment2), caches):
                transform_a, transform_b, manifold = self.collide(offset, chain_segment, shape, cache)
                manifolds.append(manifold)
            self.draw_chain_segments(transform_a)
            draw_geometry(dd, shape, transform_b, colors.PaleGoldenrod)
            if isinstance(shape, b2d.Polygon):
                center = b2d.transform_point(transform_b, shape.centroid)
            else:
                center = b2d.mid_point(
                    b2d.transform_point(transform_b, shape.center1), b2d.transform_point(transform_b, shape.center2)
                )
            dd.draw_point(center, 5.0, colors.Gainsboro)
            for manifold in manifolds:
                self.draw_local_manifold(manifold, transform_a, transform_b)
            offset = offset + 2.0 * increment


# https://betravis.github.io/shape-tools/path-to-polygon/
_SMOOTH_POINTS = [
    (-20.58325, 14.54175), (-21.90625, 15.8645), (-24.552, 17.1875), (-27.198, 11.89575),
    (-29.84375, 15.8645), (-29.84375, 21.15625), (-25.875, 23.802), (-20.58325, 25.125),
    (-25.875, 29.09375), (-20.58325, 31.7395), (-11.0089998, 23.2290001), (-8.67700005, 21.15625),
    (-6.03125, 21.15625), (-7.35424995, 29.09375), (-3.38549995, 29.09375), (1.90625, 30.41675),
    (5.875, 17.1875), (11.16675, 25.125), (9.84375, 29.09375), (13.8125, 31.7395),
    (21.75, 30.41675), (28.3644981, 26.448), (25.71875, 18.5105), (24.3957481, 13.21875),
    (17.78125, 11.89575), (15.1355, 7.92700005), (5.875, 9.25), (1.90625, 11.89575),
    (-3.25, 11.89575), (-3.25, 9.9375), (-4.70825005, 9.25), (-8.67700005, 9.25),
    (-11.323, 11.89575), (-13.96875, 11.89575), (-15.29175, 14.54175), (-19.2605, 14.54175),
]  # fmt: skip


@register_sample("Collision", "Smooth Manifold")
class SmoothManifold(_ManifoldDrawing, TransformDragSample):
    """Manifolds of a circle or rounded box against a loop of chain segments (smooth collision)."""

    camera_center = (2.0, 20.0)
    camera_zoom = 21.0
    drag_scale = 1.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings, position=(0.0, 20.0))
        self.shape_type = "Box"
        self.round = 0.0

        n = len(_SMOOTH_POINTS)
        self.segments = [
            b2d.chain_segment(
                b2d.segment(_SMOOTH_POINTS[i], _SMOOTH_POINTS[(i + 1) % n]),
                _SMOOTH_POINTS[i - 1],
                _SMOOTH_POINTS[(i + 2) % n],
            )
            for i in range(n)
        ]

        add = self.frontend.add_widget
        add(widgets.Dropdown("Shape", ["Circle", "Box"], self.shape_type, setter(self, "shape_type")))
        self.add_transform_widgets(("x Offset", "y Offset", "Angle"))
        add(widgets.FloatSlider("Round", 0.0, 0.4, 0.1, self.round, setter(self, "round")))
        self.add_manifold_checkboxes(
            {"show_ids": "Show Ids", "show_separation": "Show Separation", "show_anchors": "Show Anchors"}
        )
        add(widgets.Button("Reset", self.reset_transform))

    def post_debug_draw(self):
        dd = self.debug_draw
        transform_a = b2d.Transform()
        transform_b = self.transform

        for segment in self.segments:
            p1 = segment.segment.point1
            dd.draw_segment(p1, segment.segment.point2, colors.Yellow)
            dd.draw_point(p1, 4.0, colors.Yellow)

        if self.shape_type == "Circle":
            shape = b2d.circle((0.0, 0.0), 0.5)
        else:
            shape = _rounded_square(self.round)
        draw_geometry(dd, shape, transform_b, colors.Magenta)

        xf = b2d.inv_mul_transforms(transform_a, transform_b)
        for segment in self.segments:
            cache = None if self.shape_type == "Circle" else b2d.SimplexCache()
            manifold = _collide(segment, shape, xf, cache)
            self.draw_manifold(
                manifold, transform_a, line_color=colors.White, point_size=5.0, point_color=colors.Green
            )


@register_sample("Collision", "Shape Cast")
class ShapeCast(ProxyPairSample):
    """Casts shape B along a translation against shape A (b2ShapeCast)."""

    camera_center = (0.0, 0.25)
    camera_zoom = 3.0
    mouse_modes = {None: "drag", "shift": "rotate", "ctrl": "sweep"}

    def __init__(self, frontend, settings):
        super().__init__(
            frontend,
            settings,
            segment=b2d.segment((0.0, 0.0), (0.5, 0.0)),
            box=b2d.make_box(8.984375, 0.5),
            type_a="box",
            type_b="point",
            radius_a=0.0,
            radius_b=0.2,
            position=(-0.6, 0.0),
        )
        self.translation = b2d.Vec2(2.0, 0.0)
        self.encroach = False

        self.add_shape_widgets()
        self.frontend.add_widget(widgets.Checkbox("encroach", self.encroach, setter(self, "encroach")))

    def on_mouse_move(self, event):
        super().on_mouse_move(event)
        if self.mode == "sweep":
            self.translation = event.world_position - self.start_point

    def post_debug_draw(self):
        dd = self.debug_draw
        proxy_a, proxy_b = self.proxy_a, self.proxy_b
        transform = self.transform

        cast_input = b2d.ShapeCastPairInput()
        cast_input.proxy_a = proxy_a
        cast_input.proxy_b = proxy_b
        cast_input.transform = transform
        cast_input.translation_b = self.translation
        cast_input.max_fraction = 1.0
        cast_input.can_encroach = self.encroach
        output = b2d.cast_shape(cast_input)

        t = output.fraction if output.hit else 1.0
        hit_transform = with_position(transform, transform.p + t * self.translation)

        distance_input = b2d.DistanceInput()
        distance_input.proxy_a = proxy_a
        distance_input.proxy_b = proxy_b
        distance_input.transform = hit_transform
        distance_input.use_radii = False
        distance_output, _ = b2d.compute_shape_distance(distance_input)

        self.draw_shape(self.type_a, b2d.Transform(), self.radius_a, colors.Cyan)
        self.draw_shape(self.type_b, transform, self.radius_b, colors.LightGreen)
        end_transform = with_position(transform, transform.p + self.translation)
        self.draw_shape(self.type_b, end_transform, self.radius_b, colors.IndianRed)

        if output.hit:
            self.draw_shape(self.type_b, hit_transform, self.radius_b, colors.Plum)
            if output.fraction > 0.0:
                dd.draw_point(output.point, 5.0, colors.White)
                dd.draw_segment(output.point, output.point + 0.5 * output.normal, colors.Yellow)
            else:
                dd.draw_point(output.point, 5.0, colors.Peru)

        self.draw_indices()
        dd.draw_string(
            hit_transform.p,
            f"fraction = {output.fraction:.3g}, distance = {distance_output.distance:.2f}",
            colors.White,
        )


def _rot(c, s):
    q = b2d.Rot()
    q.c, q.s = c, s
    return q


def _sweep(c1, c2, q1, q2):
    sweep = b2d.Sweep()
    sweep.c1, sweep.c2, sweep.q1, sweep.q2 = c1, c2, q1, q2
    return sweep


@register_sample("Collision", "Time of Impact")
class TimeOfImpact(Box2dSample):
    """Time of impact of a thin capsule sweeping past a box (b2TimeOfImpact)."""

    camera_center = (-16.0, 45.0)
    camera_zoom = 5.0

    vertices_a = [(-16.25, 44.75), (-15.75, 44.75), (-15.75, 45.25), (-16.25, 45.25)]
    vertices_b = [(0.0, -0.125), (0.0, 0.125)]
    radius_a = 0.0
    radius_b = 0.0299999993

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.sweep_a = _sweep((0.0, 0.0), (0.0, 0.0), b2d.Rot(), b2d.Rot())
        self.sweep_b = _sweep(
            (-15.8332710, 45.3520279),
            (-15.8324337, 45.3413048),
            _rot(-0.540891349, 0.841092527),
            _rot(-0.457797021, 0.889056742),
        )
        self.proxy_a = b2d.make_proxy(self.vertices_a, self.radius_a)
        self.proxy_b = b2d.make_proxy(self.vertices_b, self.radius_b)

    def post_debug_draw(self):
        dd = self.debug_draw
        toi_input = b2d.TOIInput()
        toi_input.proxy_a = self.proxy_a
        toi_input.proxy_b = self.proxy_b
        toi_input.sweep_a = self.sweep_a
        toi_input.sweep_b = self.sweep_b
        toi_input.max_fraction = 1.0
        output = b2d.compute_time_of_impact(toi_input)

        def world_points(sweep, vertices, t):
            transform = b2d.get_sweep_transform(sweep, t)
            return [b2d.transform_point(transform, v) for v in vertices]

        dd.draw_polygon(world_points(self.sweep_a, self.vertices_a, 0.0), colors.Gray)
        # B at t = 0, at the time of impact and at t = 1
        dd.draw_solid_capsule(*world_points(self.sweep_b, self.vertices_b, 0.0), self.radius_b, colors.Green)
        dd.draw_polygon(world_points(self.sweep_b, self.vertices_b, output.fraction), colors.Orange)
        end_points = world_points(self.sweep_b, self.vertices_b, 1.0)
        dd.draw_solid_capsule(*end_points, self.radius_b, colors.Red)

        text = f"toi = {output.fraction:g}"
        if output.state == b2d.TOIState.HIT:
            distance_input = b2d.DistanceInput()
            distance_input.proxy_a = self.proxy_a
            distance_input.proxy_b = self.proxy_b
            distance_input.transform = b2d.inv_mul_transforms(
                b2d.get_sweep_transform(self.sweep_a, output.fraction),
                b2d.get_sweep_transform(self.sweep_b, output.fraction),
            )
            distance_input.use_radii = False
            distance_output, _ = b2d.compute_shape_distance(distance_input)
            text += f", distance = {distance_output.distance:g}"
        dd.draw_string(end_points[1], text, colors.White)
