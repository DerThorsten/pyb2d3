"""Boids: flocks from three local rules, computed for all neighbor pairs with numpy."""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import hsv_colors, pair_sum

HX, HY = 40.0, 25.0  # arena half size
RADIUS = 0.2
SPEED = 6.0  # cruising speed
VIEW = 2.5  # boids see their neighbors up to this distance
SEPARATION_RADIUS = 0.9
WALL_MARGIN = 4.0  # boids turn back this far from the walls
HAWK_RADIUS = 10.0


@register_sample("Agents", "Boids Flocking", video=True)
class BatchBoids(SampleBase):
    """Boids steer by their neighbors only (separation, alignment, cohesion), yet
    flocks form and swirl around.
    Mouse: hold for a hawk, the boids scatter.
    Sliders: the three rule weights, count.
    Hint: separation 0: dense clumps.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 800
        self.separation = 1.5
        self.alignment = 1.0
        self.cohesion = 1.0
        self.rng = np.random.default_rng(5)
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=HX, hy=HY))
        self.bodies = b2d.Bodies()
        self.create_boids()
        for widget in (
            widgets.IntSlider("boids", 100, 2500, 100, self.count, self.set_count),
            widgets.FloatSlider("separation", 0.0, 4.0, 0.1, self.separation, self.set_separation),
            widgets.FloatSlider("alignment", 0.0, 4.0, 0.1, self.alignment, self.set_alignment),
            widgets.FloatSlider("cohesion", 0.0, 4.0, 0.1, self.cohesion, self.set_cohesion),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-HX, -HY), upper_bound=(HX, HY))

    def create_boids(self):
        """random positions and headings, colored by the starting heading"""
        self.bodies.destroy()
        positions = self.rng.uniform((-HX + 1, -HY + 1), (HX - 1, HY - 1), (self.count, 2))
        angle = self.rng.uniform(0, 2 * np.pi, self.count)
        colors = hsv_colors(angle / (2 * np.pi), 0.6)
        material = b2d.surface_material(friction=0.0, restitution=0.5)
        self.bodies, shapes = self.world.create_bodies(
            positions, b2d.shape_def(material=material), b2d.circle(radius=RADIUS)
        )
        # per-body colors and all velocities at once with the batch api
        shapes.custom_color = colors
        self.bodies.linear_velocity = SPEED * np.stack([np.cos(angle), np.sin(angle)], axis=1)
        self.flock_count = 0
        self.pairs = ([], [])

    def set_count(self, value):
        self.count = int(value)
        self.create_boids()

    def set_separation(self, value):
        self.separation = value

    def set_alignment(self, value):
        self.alignment = value

    def set_cohesion(self, value):
        self.cohesion = value

    def on_mouse_down(self, event):
        # no super(): the button summons the hawk instead of dragging bodies / the camera
        self.is_mouse_down = True
        self.mouse_pos = event.world_position

    def hawk(self):
        """the hawk is at the mouse while the button is held"""
        return np.array(self.mouse_pos) if self.is_mouse_down else None

    def pre_update(self, dt):
        """a steering acceleration per boid from the rules, applied in one batch call"""
        p = self.bodies.position
        v = self.bodies.linear_velocity
        n = len(p)
        i, j, delta, distance = self.bodies.neighbor_pairs(VIEW)  # (C++, b2d.extensions)
        self.pairs = (i, j)
        neighbors = np.bincount(i, minlength=n) + np.bincount(j, minlength=n)
        mean = 1.0 / np.maximum(neighbors, 1)[:, None]  # (0 for a boid without neighbors)

        # pair_sum(x) adds +x to boid i and -x to boid j: with x = (something of j) -
        # (something of i) both get "the other one minus me"
        # cohesion: towards the mean position of the neighbors
        cohesion = pair_sum(n, i, j, delta) * mean
        # alignment: towards the mean velocity of the neighbors
        alignment = pair_sum(n, i, j, v[j] - v[i]) * mean
        # separation: away from close neighbors, stronger when closer
        close = distance < SEPARATION_RADIUS
        d = distance[close]
        push = delta[close] * ((SEPARATION_RADIUS - d) / np.maximum(d, 1e-3) ** 2)[:, None]
        separation = -pair_sum(n, i[close], j[close], push)

        steer = (
            4.0 * self.separation * separation
            + 0.8 * self.alignment * alignment
            + 0.6 * self.cohesion * cohesion
        )
        steer += self.wall_avoidance(p)
        hawk = self.hawk()
        if hawk is not None:
            away = p - hawk
            d = np.linalg.norm(away, axis=1)
            flee = 40.0 * np.clip(1.0 - d / HAWK_RADIUS, 0.0, 1.0) / np.maximum(d, 1e-6)
            steer += flee[:, None] * away
        # keep the cruising speed: speed up / slow down along the heading
        speed = np.linalg.norm(v, axis=1)
        heading = v / np.maximum(speed, 1e-6)[:, None]
        steer += (SPEED - speed)[:, None] * heading

        self.bodies.apply_force_to_center(2.0 * self.bodies.mass[:, None] * steer)

    def wall_avoidance(self, p):
        """soft walls: push back, the deeper into the margin the stronger"""
        lower = np.array([-HX, -HY]) + WALL_MARGIN
        upper = np.array([HX, HY]) - WALL_MARGIN
        return np.clip(lower - p, 0, None) - np.clip(p - upper, 0, None)

    def post_update(self, dt):
        """count the flocks: groups of >= 5 boids connected by neighbor pairs"""
        if self.world_iteration % 15:
            return
        i, j = self.pairs
        # every boid starts with its own label, then takes the smallest label of its
        # neighbors until nothing changes: connected boids end with the same label
        label = np.arange(len(self.bodies))
        for _ in range(30):
            low = np.minimum(label[i], label[j])
            new = label.copy()
            np.minimum.at(new, i, low)
            np.minimum.at(new, j, low)
            new = new[new]  # jump ahead: take the label of the label
            if np.array_equal(new, label):
                break
            label = new
        self.flock_count = np.count_nonzero(np.bincount(label) >= 5)

    def post_debug_draw(self):
        dd = self.debug_draw
        hawk = self.hawk()
        if hawk is not None:
            dd.draw_circle(tuple(hawk), HAWK_RADIUS, b2d.HexColor.OrangeRed)
            dd.draw_point(tuple(hawk), 10.0, b2d.HexColor.OrangeRed)
        # local alignment: mean cos of the angle between neighbors (1: a flock flies as one)
        v = self.bodies.linear_velocity
        heading = v / np.maximum(np.linalg.norm(v, axis=1), 1e-6)[:, None]
        i, j = self.pairs
        aligned = np.sum(heading[i] * heading[j], axis=1).mean() if len(i) else 0.0
        text = (
            f"{len(self.bodies)} boids  {self.flock_count} flocks  {len(i)} neighbor pairs  "
            f"neighbor alignment {aligned:.2f}"
        )
        dd.draw_string((-HX, HY + 1.0), text, b2d.HexColor.White)
