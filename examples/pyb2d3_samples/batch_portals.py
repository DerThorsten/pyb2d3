"""Portals: balls that touch a portal come out of its partner, velocity rotated along."""

import math
from dataclasses import dataclass

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .batch_common import create_circles, destroy_bodies, hsv_colors


@dataclass
class Portal:
    """a portal on a wall: center, unit normal (pointing into the room), half width"""

    center: np.ndarray
    normal: np.ndarray
    half_width: float
    color: int

    @property
    def tangent(self):
        return np.array([-self.normal[1], self.normal[0]])


def rotation_between(a, b):
    """2x2 matrix rotating direction a onto direction b"""
    angle = math.atan2(b[1], b[0]) - math.atan2(a[1], a[0])
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s], [s, c]])


@register_sample("Fields & Space", "Portals")
class BatchPortals(SampleBase):
    """Balls bounce through two pairs of portals, leaving with the velocity rotated
    like the portal.
    Sliders: balls, exit speed cap.
    Hint: the floor portal leads to the ceiling: balls fall forever, faster each
    loop.
    """

    half_width = 14.0
    height = 20.0
    ball_radius = 0.22
    cooldown = 0.3  # s: no second teleport right after one
    funnel_top = 4.0  # height of the funnel at the walls
    funnel_half_width = 1.8  # its bottom: the floor portal

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.count = 300
        self.max_speed = 16.0
        self.rng = np.random.default_rng(2)
        w, h = self.half_width, self.height
        orange, blue = 0xFF9A3C, 0x3CB4FF
        # pair 1: floor (bottom of the funnel) <-> ceiling above it: an endless fall
        # pair 2: on the left funnel slope <-> high on the right wall
        slope = np.array([w - self.funnel_half_width, -self.funnel_top])  # left slope, downhill
        slope_normal = np.array([-slope[1], slope[0]]) / np.linalg.norm(slope)
        slope_center = np.array([-w, self.funnel_top]) + 0.5 * slope
        self.portals = [
            Portal(np.array([0.0, 0.0]), np.array([0.0, 1.0]), self.funnel_half_width, orange),
            Portal(np.array([0.0, h]), np.array([0.0, -1.0]), self.funnel_half_width, orange),
            Portal(slope_center, slope_normal, 1.6, blue),
            Portal(np.array([w, 0.65 * h]), np.array([-1.0, 0.0]), 1.6, blue),
        ]
        self.partner = [1, 0, 3, 2]
        self.create_room()
        self.bodies = b2d.Bodies()
        self.create_balls()
        self.teleports = 0
        self.per_portal = [0, 0, 0, 0]  # entries per portal
        self.rate = 0.0
        for widget in (
            widgets.IntSlider("balls", 50, 1000, 50, self.count, self.set_count),
            widgets.FloatSlider(
                "exit speed cap", 4.0, 30.0, 1.0, self.max_speed, self.set_max_speed
            ),
            widgets.Button("reset", self.create_balls),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.half_width - 1, -1.0),
            upper_bound=(self.half_width + 1, self.height + 2.0),
        )

    def set_count(self, value):
        self.count = int(value)
        self.create_balls()

    def set_max_speed(self, value):
        self.max_speed = value

    # ---- setup ------------------------------------------------------------------------------

    def create_room(self):
        """walls, ceiling and a funnel down to the floor portal"""
        w, h = self.half_width, self.height
        room = self.world.create_static_body()
        wall = b2d.shape_def(
            material=b2d.surface_material(
                friction=0.2, restitution=0.2, custom_color=b2d.HexColor.SlateGray
            )
        )
        hw, top = self.funnel_half_width, self.funnel_top
        for a, b in [
            ((-w, top), (-w, h)),
            ((w, top), (w, h)),
            ((-w, h), (w, h)),
            ((-w, top), (-hw, 0.0)),
            ((w, top), (hw, 0.0)),
            ((-hw, 0.0), (hw, 0.0)),
        ]:
            room.create_shape(wall, b2d.segment(a, b))

    def create_balls(self):
        """balls on a grid in the upper half of the room"""
        destroy_bodies(self, self.bodies)
        step = 2.4 * self.ball_radius
        xs = np.arange(-self.half_width + 1.0, self.half_width - 1.0, step)
        rows = int(math.ceil(self.count / len(xs)))
        ys = self.height - 1.0 - step * np.arange(rows)
        gx, gy = np.meshgrid(xs, ys)
        positions = np.stack([gx.ravel(), gy.ravel()], axis=1)[: self.count]
        colors = hsv_colors(np.linspace(0.0, 1.0, len(positions), endpoint=False), 0.55, 1.0)
        self.bodies = create_circles(
            self.world,
            positions,
            self.ball_radius,
            colors=colors,
            density=1.0,
            friction=0.1,
            restitution=0.3,
            enable_sleep=False,
        )
        self.since_teleport = np.full(len(positions), self.cooldown)

    # ---- teleporting ------------------------------------------------------------------------

    def pre_update(self, dt):
        """per portal: a mask of the balls touching it (and moving into it), then one
        batch call puts them in front of the partner portal with rotated velocities"""
        self.since_teleport += dt
        p = self.bodies.position.astype(np.float64)
        v = self.bodies.linear_velocity.astype(np.float64)
        moved = 0
        for i, portal in enumerate(self.portals):
            offset = p - portal.center
            depth = offset @ portal.normal  # distance in front of the portal
            along = offset @ portal.tangent
            into = v @ portal.normal  # < 0: moving into the portal
            # reach: touching, or touching within this step (fast balls would bounce first)
            reach = self.ball_radius + 0.12 + np.maximum(-into, 0.0) * dt
            mask = (
                (np.abs(along) < portal.half_width - 0.5 * self.ball_radius)
                & (depth < reach)
                & (depth > -self.ball_radius)
                & (into < 0.5)
                & (self.since_teleport >= self.cooldown)
            )
            if not mask.any():
                continue
            out = self.portals[self.partner[i]]
            # going in along -normal = coming out along the partner's normal
            rot = rotation_between(-portal.normal, out.normal)
            limit = out.half_width - self.ball_radius
            positions = (
                out.center
                + np.clip(along[mask], -limit, limit)[:, None] * (rot @ portal.tangent)
                + (self.ball_radius + 0.05) * out.normal
            )
            velocities = v[mask] @ rot.T
            speed = np.linalg.norm(velocities, axis=1)
            velocities *= (np.minimum(speed, self.max_speed) / np.maximum(speed, 1e-6))[:, None]
            # always leave the partner portal (at least a little)
            push = np.maximum(1.0 - velocities @ out.normal, 0.0)
            velocities += push[:, None] * out.normal
            batch = self.bodies[mask]
            batch.set_transform(positions, (1.0, 0.0))
            batch.linear_velocity = velocities
            self.since_teleport[mask] = 0.0
            p[mask], v[mask] = positions, velocities
            moved += int(mask.sum())
            self.per_portal[i] += int(mask.sum())
        self.teleports += moved
        self.rate = 0.98 * self.rate + 0.02 * moved / dt

    # ---- drawing ----------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        for portal in self.portals:
            for k in range(3):  # a thick line: three parallel segments
                shift = (0.06 + 0.07 * k) * portal.normal
                a = portal.center - portal.half_width * portal.tangent + shift
                b = portal.center + portal.half_width * portal.tangent + shift
                dd.draw_segment(tuple(a), tuple(b), portal.color)
        speed = np.linalg.norm(self.bodies.linear_velocity, axis=1)
        text = (
            f"{len(self.bodies)} balls, {self.teleports} teleports ({self.rate:.0f}/s), "
            f"mean speed {float(speed.mean()):.1f}"
        )
        dd.draw_string((-self.half_width, self.height + 1.2), text, b2d.HexColor.White)
