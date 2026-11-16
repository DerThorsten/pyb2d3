"""Boids: flocks from three local rules, computed for all neighbor pairs with numpy."""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import (
    create_circles,
    hsv_colors,
    neighbor_pairs,
    pair_sum,
    unit_and_length,
)


@register_sample("Agents", "Boids Flocking")
class BatchBoids(SampleBase):
    """Boids steer by their neighbors only (separation, alignment, cohesion), yet
    flocks form and swirl around.
    Mouse: hold for a hawk, the boids scatter.
    Sliders: the three rule weights, count.
    Hint: separation 0: dense clumps.
    """

    hx, hy = 40.0, 25.0  # arena half size
    radius = 0.2
    view = 2.5  # neighbor radius
    separation_radius = 0.9

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 800
        self.separation = 1.5
        self.alignment = 1.0
        self.cohesion = 1.0
        self.speed = 6.0
        self.rng = np.random.default_rng(5)
        self.hawk = None
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=self.hx, hy=self.hy))
        self.bodies = b2d.Bodies()
        self.create_boids()
        for widget in (
            widgets.IntSlider("boids", 100, 2500, 100, self.count, self.set_count),
            widgets.FloatSlider(
                "separation", 0.0, 4.0, 0.1, self.separation, self.setter("separation")
            ),
            widgets.FloatSlider(
                "alignment", 0.0, 4.0, 0.1, self.alignment, self.setter("alignment")
            ),
            widgets.FloatSlider("cohesion", 0.0, 4.0, 0.1, self.cohesion, self.setter("cohesion")),
        ):
            self.frontend.add_widget(widget)

    def setter(self, name):
        """a widget callback setting attribute `name`"""
        return lambda value: setattr(self, name, value)

    def aabb(self):
        return b2d.aabb(lower_bound=(-self.hx, -self.hy), upper_bound=(self.hx, self.hy))

    def create_boids(self):
        """random positions + headings, colored by starting heading"""
        self.bodies.destroy()
        n = self.count
        m = 1.0
        positions = self.rng.uniform(
            (-self.hx + m, -self.hy + m), (self.hx - m, self.hy - m), (n, 2)
        )
        angle = self.rng.uniform(0, 2 * np.pi, n)
        self.bodies = create_circles(
            self.world,
            positions,
            self.radius,
            colors=hsv_colors(angle / (2 * np.pi), 0.6),
            friction=0.0,
            restitution=0.5,
            linear_damping=0.0,
        )
        self.bodies.linear_velocity = self.speed * np.stack([np.cos(angle), np.sin(angle)], axis=1)
        self.flock_count = 0
        self.pairs = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64))

    def set_count(self, value):
        """slider: recreate the boids"""
        self.count = int(value)
        self.create_boids()

    # ---- the three rules (+ walls, hawk) --------------------------------------------------------

    def pre_update(self, dt):
        """desired velocity from the rules -> one steering force call"""
        bodies = self.bodies
        p = bodies.position
        v = bodies.linear_velocity
        n = len(p)
        i, j, delta, dist = neighbor_pairs(p, self.view)
        self.pairs = (i, j)

        count = np.bincount(i, minlength=n) + np.bincount(j, minlength=n)
        has = np.maximum(count, 1)[:, None]
        # pair_sum(x): +x on body i, -x on body j; with x = p_j - p_i both get
        # "the other one minus me"
        # cohesion: towards the mean position of the neighbors
        cohesion = pair_sum(n, i, j, delta) / has
        # alignment: towards the mean velocity of the neighbors
        alignment = pair_sum(n, i, j, v[j] - v[i]) / has
        # separation: away from close neighbors, stronger when closer
        close = dist < self.separation_radius
        push = (
            delta[close]
            * ((self.separation_radius - dist[close]) / np.maximum(dist[close], 1e-3) ** 2)[:, None]
        )
        separation = -pair_sum(n, i[close], j[close], push)
        alone = count == 0
        cohesion[alone] = 0.0
        alignment[alone] = 0.0

        steer = (
            self.separation * 4.0 * separation
            + self.alignment * 0.8 * alignment
            + self.cohesion * 0.6 * cohesion
        )
        # soft walls: turn back before the edge
        margin = 4.0
        steer[:, 0] += np.clip(-self.hx + margin - p[:, 0], 0, None) - np.clip(
            p[:, 0] - self.hx + margin, 0, None
        )
        steer[:, 1] += np.clip(-self.hy + margin - p[:, 1], 0, None) - np.clip(
            p[:, 1] - self.hy + margin, 0, None
        )
        # the hawk: flee
        if self.hawk is not None:
            away, d = unit_and_length(p - self.hawk)
            steer += (40.0 * np.clip(1.0 - d / 10.0, 0.0, 1.0))[:, None] * away

        # keep the cruising speed: steer the speed towards `self.speed` along the heading
        heading, speed = unit_and_length(v)
        steer += (self.speed - speed)[:, None] * heading
        bodies.apply_force_to_center(bodies.mass[:, None] * steer * 2.0)

    def post_update(self, dt):
        """number of flocks: connected groups of the neighbor graph (union-find on the pairs)"""
        if self.world_iteration % 15:
            return
        i, j = self.pairs
        parent = np.arange(len(self.bodies))
        for _ in range(30):  # label propagation: min label over neighbors, until stable
            low = np.minimum(parent[i], parent[j])
            new = parent.copy()
            np.minimum.at(new, i, low)
            np.minimum.at(new, j, low)
            new = new[new]
            if np.array_equal(new, parent):
                break
            parent = new
        sizes = np.bincount(parent)
        self.flock_count = int(np.count_nonzero(sizes >= 5))

    # ---- mouse: the hawk ---------------------------------------------------------------------

    def on_mouse_down(self, event):
        """hawk at the cursor while the button is held (no dragging)"""
        self.mouse_pos = event.world_position
        self.hawk = np.array(self.mouse_pos, dtype=np.float64)

    def on_mouse_move(self, event):
        """move the hawk"""
        self.mouse_pos = event.world_position
        if self.hawk is not None:
            self.hawk = np.array(self.mouse_pos, dtype=np.float64)

    def on_mouse_up(self, event):
        """hawk gone"""
        super().on_mouse_up(event)
        self.hawk = None

    def on_mouse_leave(self, event):
        """hawk gone"""
        super().on_mouse_leave(event)
        self.hawk = None

    # ---- drawing -----------------------------------------------------------------------------

    def post_debug_draw(self):
        """hawk + flock statistics"""
        dd = self.debug_draw
        if self.hawk is not None:
            dd.draw_circle(tuple(self.hawk), 10.0, b2d.HexColor.OrangeRed)
            dd.draw_point(tuple(self.hawk), 10.0, b2d.HexColor.OrangeRed)
        heading, _ = unit_and_length(self.bodies.linear_velocity)
        i, j = self.pairs
        # local alignment: mean cos of the angle between neighbors (1: a flock flies as one)
        aligned = float(np.einsum("ij,ij->i", heading[i], heading[j]).mean()) if len(i) else 0.0
        text = (
            f"{len(self.bodies)} boids  {self.flock_count} flocks  {len(i)} neighbor pairs  "
            f"neighbor alignment {aligned:.2f}"
        )
        dd.draw_string((-self.hx, self.hy + 1.0), text, b2d.HexColor.White)
