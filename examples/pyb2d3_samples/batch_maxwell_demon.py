"""Maxwell's demon: a gate that sorts gas molecules by speed, heating one chamber and cooling the other."""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import create_circles, destroy_bodies, draw_histogram, hsv_colors


class BatchMaxwellDemon(SampleBase):
    """Maxwell's demon: an ideal gas in two chambers with a gate between them.
    The demon lets only fast molecules pass from left to right and only slow
    ones from right to left: the right chamber heats up, the left one cools
    down, without any work (that is the paradox).

    Sliders: the demon's speed threshold.
    Checkbox: demon on / off (off: an open gate, the temperatures even out).
    Hint: molecules are colored by speed; the histograms show the speeds of each
    chamber. The gate decision is one numpy mask over all molecules per step.
    """

    hx, hy = 24.0, 14.0  # box half size; the wall is at x = 0
    gate = 2.0  # half height of the gate
    radius = 0.18
    zone = 1.0  # the demon watches molecules this close to the gate

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 700
        self.demon_on = True
        self.rng = np.random.default_rng(17)
        self.world.restitution_threshold = 0.01  # elastic down to (almost) zero speed
        self.build_box()
        self.bodies = b2d.Bodies()
        self.reset()
        self.threshold = self.mean_speed  # fast / slow: the initial mean speed
        for widget in (
            widgets.Checkbox("demon on", self.demon_on, self.setter("demon_on")),
            widgets.FloatSlider("speed threshold", 1.0, 12.0, 0.25, self.threshold, self.setter("threshold")),
            widgets.Button("mix again", self.reset),
        ):
            self.frontend.add_widget(widget)

    def setter(self, name):
        """a widget callback setting attribute `name`"""
        return lambda value: setattr(self, name, value)

    def aabb(self):
        return b2d.aabb(lower_bound=(-self.hx, -self.hy - 10.0), upper_bound=(self.hx, self.hy + 2.0))

    def build_box(self):
        """the box and the wall with the gate in the middle"""
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=self.hx, hy=self.hy))
        wall_def = b2d.shape_def(material=b2d.surface_material(friction=0.0, restitution=1.0,
                                                                custom_color=b2d.HexColor.SlateGray))
        length = 0.5 * (self.hy - self.gate)
        for side in (1.0, -1.0):
            self.anchor_body.create_shape(wall_def, b2d.box(0.15, length, center=(0.0, side * (self.gate + length))))

    def reset(self):
        """molecules spread over both chambers with random (2d Maxwell) velocities"""
        destroy_bodies(self, self.bodies)
        n = self.count
        m = 0.5
        positions = self.rng.uniform((-self.hx + m, -self.hy + m), (self.hx - m, self.hy - m), (n, 2))
        positions[np.abs(positions[:, 0]) < 0.5, 0] += 1.0  # not inside the wall
        velocities = self.rng.normal(scale=4.0, size=(n, 2))
        self.bodies = create_circles(self.world, positions, self.radius, colors=self.speed_colors(velocities),
                                     friction=0.0, restitution=1.0, linear_damping=0.0, enable_sleep=False)
        self.bodies.linear_velocity = velocities
        self.mean_speed = float(np.linalg.norm(velocities, axis=1).mean())
        self.energy = float(np.einsum("ij,ij->", velocities, velocities))  # sum of v^2, kept constant
        self.shape_list = [body.shapes[0] for body in self.bodies]
        self.band = np.full(n, -1)

    def speed_colors(self, velocities):
        """slow: blue ... fast: red"""
        speed = np.linalg.norm(velocities, axis=1)
        return hsv_colors(0.66 * (1.0 - np.clip(speed / 12.0, 0.0, 1.0)), 0.8)

    # ---- the demon ----------------------------------------------------------------------------

    def pre_update(self, dt):
        """keep the total energy constant, reflect the molecules the demon does
        not let through (a velocity flip: no energy is added or removed)"""
        bodies = self.bodies
        p = bodies.position
        v = bodies.linear_velocity
        # box2d's contacts lose a little energy per collision (the gas would cool
        # down): put it back with one common factor, which keeps the differences
        # the demon creates
        energy = float(np.einsum("ij,ij->", v, v))
        if energy > 0.0:
            v *= np.sqrt(self.energy / energy)
            bodies.linear_velocity = v
        if not self.demon_on:
            return
        speed = np.sqrt(np.einsum("ij,ij->i", v, v))
        at_gate = (np.abs(p[:, 1]) < self.gate) & (np.abs(p[:, 0]) < self.zone + self.radius)
        rightwards = at_gate & (p[:, 0] < 0.0) & (v[:, 0] > 0.0)
        leftwards = at_gate & (p[:, 0] > 0.0) & (v[:, 0] < 0.0)
        # left -> right only if fast, right -> left only if slow
        reject = rightwards & (speed < self.threshold) | leftwards & (speed >= self.threshold)
        if reject.any():
            flipped = v[reject]
            flipped[:, 0] = -flipped[:, 0]
            bodies[reject].linear_velocity = flipped

    def post_update(self, dt):
        """recolor molecules whose speed band changed (only those)"""
        v = self.bodies.linear_velocity
        band = np.minimum((np.linalg.norm(v, axis=1) / 1.5).astype(int), 8)
        changed = np.flatnonzero(band != self.band)
        if len(changed):
            colors = self.speed_colors(v[changed])
            for k, color in zip(changed, colors):
                shape = self.shape_list[k]
                material = shape.surface_material
                material.custom_color = int(color)
                shape.surface_material = material
            self.band[changed] = band[changed]

    def chambers(self):
        """(left mask, right mask, speeds)"""
        p = self.bodies.position
        v = self.bodies.linear_velocity
        speed = np.sqrt(np.einsum("ij,ij->i", v, v))
        return p[:, 0] < 0.0, p[:, 0] >= 0.0, speed

    def temperatures(self):
        """mean kinetic energy per molecule (m = 1 units) of left / right chamber"""
        left, right, speed = self.chambers()
        ke = 0.5 * speed**2
        return (float(ke[left].mean()) if left.any() else 0.0, float(ke[right].mean()) if right.any() else 0.0)

    # ---- drawing -----------------------------------------------------------------------------

    def post_debug_draw(self):
        """gate, temperatures, a speed histogram per chamber"""
        dd = self.debug_draw
        gate_color = b2d.HexColor.Gold if self.demon_on else b2d.HexColor.DimGray
        dd.draw_segment((0.0, -self.gate), (0.0, self.gate), gate_color)
        left, right, speed = self.chambers()
        t_left, t_right = self.temperatures()
        text = (f"left: {int(left.sum())} molecules, T {t_left:.1f}    "
                f"right: {int(right.sum())} molecules, T {t_right:.1f}    "
                f"total energy {0.5 * float((speed**2).sum()):.0f}")
        dd.draw_string((-self.hx, self.hy + 1.0), text, b2d.HexColor.White)
        bins = np.linspace(0.0, 15.0, 16)
        for mask, x0 in ((left, -self.hx), (right, 1.0)):
            counts, _ = np.histogram(speed[mask], bins=bins)
            draw_histogram(dd, (x0, -self.hy - 9.0), (self.hx - 1.0, 7.5), counts, b2d.HexColor.Orange)
        dd.draw_string((-self.hx, -self.hy - 1.0), "speeds left chamber (0 .. 15)", b2d.HexColor.White)
        dd.draw_string((1.0, -self.hy - 1.0), "speeds right chamber (0 .. 15)", b2d.HexColor.White)


if __name__ == "__main__":
    BatchMaxwellDemon.run()
