"""An hourglass: grains flow through a narrow neck; flip it and watch them run again."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import create_circles, destroy_bodies, hsv_colors


class BatchHourglass(SampleBase):
    """An hourglass full of grains: they pile up, arch over the neck and trickle through.

    Keys: space flips the glass.
    Hint: a narrow neck jams (arching); the numbers on top are counted with one
    numpy mask over all grain positions per frame.
    """

    half_height = 8.0
    half_width = 4.5
    grain_radius = 0.075
    # the glass ends move flip_speed * 8.6 m/s: with 0.3 m thick walls and 4 substeps no
    # grain is skipped (thin segments at 2 rad/s let grains tunnel out)
    flip_speed = 1.0  # rad / s
    wall_radius = 0.15

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.count = 1500
        self.neck = 0.9  # neck width
        self.glass = None
        self.grains = b2d.Bodies()
        self.angle = 0.0
        self.target_angle = 0.0
        self.flow = 0.0
        self.build()
        for widget in (
            widgets.Button("flip (space)", self.flip),
            widgets.IntSlider(
                "grains", 300, 2000, 100, self.count, self.set_count
            ),  # the bulb holds ~2050
            widgets.FloatSlider("neck width", 0.4, 2.0, 0.05, self.neck, self.set_neck),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        r = self.half_height + 1.0
        return b2d.aabb(lower_bound=(-r, -r), upper_bound=(r, r))

    # ---- the glass ------------------------------------------------------------------------

    def outline(self):
        """the right half of the glass outline from the top down (local coordinates)"""
        h, w, n = self.half_height, self.half_width, 0.5 * self.neck
        return [(0.0, h), (w, h), (w, 0.4 * h), (n, 0.0), (w, -0.4 * h), (w, -h), (0.0, -h)]

    def inside_top_bulb(self, x, y):
        """vectorized: points inside the upper half of the glass (with a margin)"""
        h, w, n = self.half_height, self.half_width, 0.5 * self.neck
        half = np.where(y > 0.4 * h, w, n + (w - n) * y / (0.4 * h))
        return (y > 0.3) & (y < h - 0.2) & (np.abs(x) < half - 2.5 * self.grain_radius)

    def wall_quads(self, points, side):
        """thick walls along a polyline: one quad per segment, inner edge on the
        outline (the glass gets no smaller), mitered joints (no overlap, no gap)"""
        thickness = 2.0 * self.wall_radius
        direction = np.diff(points, axis=0)
        direction /= np.linalg.norm(direction, axis=1)[:, None]
        normal = np.stack([-direction[:, 1], direction[:, 0]], axis=1) * side  # outwards
        # vertex offsets: the segment normal at both ends, the miter in between
        offset = np.concatenate([normal[:1], normal[:-1] + normal[1:], normal[-1:]])
        inner = 1.0 + np.einsum("ij,ij->i", normal[:-1], normal[1:])
        offset[1:-1] /= inner[:, None]
        outer = points + thickness * offset
        return [[points[k], points[k + 1], outer[k + 1], outer[k]] for k in range(len(points) - 1)]

    def build(self):
        destroy_bodies(self, self.grains)
        if self.glass is not None:
            self.glass.destroy()
        self.angle = self.target_angle = 0.0  # rebuilt upright, grains in the upper bulb
        self.glass = self.world.create_kinematic_body(
            position=(0.0, 0.0), rotation=b2d.make_rot(self.angle)
        )
        glass_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.5, custom_color=b2d.HexColor.LightSkyBlue)
        )
        right = np.array(self.outline())
        for side in (1.0, -1.0):
            for quad in self.wall_quads(right * (side, 1.0), side):
                self.glass.create_shape(glass_def, b2d.polygon(points=quad))

        # grains on a grid in the upper bulb, from the top down
        step = 2.15 * self.grain_radius
        xs = np.arange(-self.half_width, self.half_width, step)
        ys = np.arange(self.half_height, 0.0, -step)
        gx, gy = np.meshgrid(xs, ys)
        gx, gy = gx.ravel(), gy.ravel()
        inside = self.inside_top_bulb(gx, gy)
        local = np.stack([gx[inside], gy[inside]], axis=1)[: self.count]
        c, s = math.cos(self.angle), math.sin(self.angle)
        world = local @ np.array([[c, s], [-s, c]])
        colors = hsv_colors(
            0.08 + 0.06 * (local[:, 1] / self.half_height), saturation=0.55, value=0.95
        )
        self.grains = create_circles(
            self.world, world, self.grain_radius, colors=colors, friction=0.4, density=2.0
        )
        self.previous_top = len(self.grains)

    def set_count(self, value):
        self.count = int(value)
        self.build()

    def set_neck(self, value):
        self.neck = value
        self.build()

    def flip(self):
        self.target_angle += math.pi

    def on_key_down(self, event):
        if event.key == "space":
            self.flip()

    # ---- simulation -----------------------------------------------------------------------

    def pre_update(self, dt):
        # turn the kinematic glass towards the target angle; set every step: the
        # velocity of a target transform stays until the next one
        turning = self.angle != self.target_angle
        if turning:
            step = math.copysign(
                min(self.flip_speed * dt, abs(self.target_angle - self.angle)),
                self.target_angle - self.angle,
            )
            self.angle += step
        self.glass.set_target_transform(
            b2d.transform(p=(0.0, 0.0), q=b2d.make_rot(self.angle)), dt, wake=turning
        )

    def post_update(self, dt):
        top = self.count_top()
        self.flow = 0.9 * self.flow + 0.1 * max(0.0, (self.previous_top - top) / dt)
        self.previous_top = top

    def count_top(self):
        """grains in the bulb that is currently up (one mask over all positions)"""
        return int(np.count_nonzero(self.grains.position[:, 1] > 0.0))

    def post_debug_draw(self):
        top = self.count_top()
        text = f"top {top}  bottom {len(self.grains) - top}  flow {self.flow:.0f} grains/s"
        self.debug_draw.draw_string(
            (-self.half_width, self.half_height + 0.6), text, b2d.HexColor.White
        )
