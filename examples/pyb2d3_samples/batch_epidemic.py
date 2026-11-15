"""An epidemic (SIR model) spreading by proximity between random-walking agents."""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import create_circles, destroy_bodies, draw_plot, neighbor_pairs, unit_and_length

SUSCEPTIBLE, INFECTED, RECOVERED = 0, 1, 2
STATE_COLORS = [int(b2d.HexColor.LightSkyBlue.value), int(b2d.HexColor.OrangeRed.value), int(b2d.HexColor.DimGray.value)]
STATE_NAMES = ["susceptible", "infected", "recovered"]


class BatchEpidemic(SampleBase):
    """An epidemic: infected agents (red) infect susceptible ones (blue) nearby,
    recover after a while (gray) and are immune. The curves show the classic
    rise and fall of the SIR model.

    Sliders: infection radius and probability (per second of contact), the share
    of agents that stay at home (do not move).
    Hint: more agents at home, a smaller radius or a lower rate flatten the red
    curve (a lower peak, spread over a longer time). Contacts: one numpy
    neighbor search per step.
    """

    hx, hy = 40.0, 25.0  # arena half size
    radius = 0.3
    speed = 4.0
    recovery_time = 9.0  # seconds, +- 30 %

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 900
        self.infection_radius = 1.0
        self.infection_rate = 0.8  # per second of contact
        self.at_home = 0.0  # share of agents that do not move
        self.rng = np.random.default_rng(13)
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=self.hx, hy=self.hy))
        self.bodies = b2d.Bodies()
        self.reset()
        for widget in (
            widgets.FloatSlider("infection radius", 0.65, 3.0, 0.05, self.infection_radius,
                                self.setter("infection_radius")),
            widgets.FloatSlider("infection rate", 0.1, 5.0, 0.1, self.infection_rate, self.setter("infection_rate")),
            widgets.FloatSlider("at home", 0.0, 0.9, 0.05, self.at_home, self.set_at_home),
            widgets.Button("reset", self.reset),
        ):
            self.frontend.add_widget(widget)

    def setter(self, name):
        """a widget callback setting attribute `name`"""
        return lambda value: setattr(self, name, value)

    def aabb(self):
        return b2d.aabb(lower_bound=(-self.hx, -self.hy), upper_bound=(self.hx + 22.0, self.hy))

    def reset(self):
        """new agents, five of them infected"""
        destroy_bodies(self, self.bodies)
        n = self.count
        m = 1.0
        positions = self.rng.uniform((-self.hx + m, -self.hy + m), (self.hx - m, self.hy - m), (n, 2))
        self.state = np.full(n, SUSCEPTIBLE)
        self.state[:5] = INFECTED
        self.bodies = create_circles(self.world, positions, self.radius, colors=[STATE_COLORS[s] for s in self.state],
                                     friction=0.0, restitution=0.6)
        self.shape_list = [body.shapes[0] for body in self.bodies]  # for the per-agent recolor
        self.shown = self.state.copy()  # the state each shape is colored with
        self.infected_time = np.zeros(n)
        self.duration = self.recovery_time * self.rng.uniform(0.7, 1.3, n)
        angle = self.rng.uniform(0, 2 * np.pi, n)
        self.heading = np.stack([np.cos(angle), np.sin(angle)], axis=1)
        self.rank = self.rng.permutation(n)  # who stays home first (random, fixed per run)
        self.set_at_home(self.at_home)
        self.history = [[], [], []]

    def set_at_home(self, value):
        """slider: who stays at home (the same agents first, so raising it adds more)"""
        self.at_home = value
        self.home = self.rank < value * len(self.state)

    # ---- one step: walking, infection, recovery ---------------------------------------------------

    def pre_update(self, dt):
        """random walk (one force call), infections from the contacts, recoveries"""
        bodies = self.bodies
        p = bodies.position
        v = bodies.linear_velocity

        # random walk: the heading turns a little each step
        self.heading, _ = unit_and_length(self.heading + self.rng.normal(scale=0.15, size=self.heading.shape))
        desired = self.speed * self.heading
        desired[self.home] = 0.0
        bodies.apply_force_to_center(3.0 * bodies.mass[:, None] * (desired - v))

        # infection: contacts between an infected and a susceptible agent
        i, j, _, _ = neighbor_pairs(p, self.infection_radius)
        si, sj = self.state[i], self.state[j]
        risky = (si == INFECTED) & (sj == SUSCEPTIBLE) | (si == SUSCEPTIBLE) & (sj == INFECTED)
        victims = np.where(si[risky] == SUSCEPTIBLE, i[risky], j[risky])
        caught = victims[self.rng.random(len(victims)) < self.infection_rate * dt]
        self.state[caught] = INFECTED
        self.infected_time[caught] = 0.0

        # recovery
        sick = self.state == INFECTED
        self.infected_time[sick] += dt
        self.state[sick & (self.infected_time > self.duration)] = RECOVERED

    def post_update(self, dt):
        """recolor the agents whose state changed, record the curves"""
        changed = np.flatnonzero(self.state != self.shown)
        for k in changed:
            shape = self.shape_list[k]
            material = shape.surface_material
            material.custom_color = STATE_COLORS[self.state[k]]
            shape.surface_material = material
        self.shown[changed] = self.state[changed]
        if self.world_iteration % 15 == 0:
            counts = np.bincount(self.state, minlength=3)
            for series, value in zip(self.history, counts):
                series.append(int(value))
                del series[:-1200]

    # ---- drawing ----------------------------------------------------------------------------

    def post_debug_draw(self):
        """counts + S / I / R curves"""
        dd = self.debug_draw
        counts = np.bincount(self.state, minlength=3)
        text = "  ".join(f"{name} {c}" for name, c in zip(STATE_NAMES, counts))
        peak = max(self.history[1]) if self.history[1] else 0
        dd.draw_string((-self.hx, self.hy + 1.0), f"{text}   peak infected {peak}", b2d.HexColor.White)
        origin, size = (self.hx + 2.0, -10.0), (18.0, 20.0)
        draw_plot(dd, origin, size, self.history, STATE_COLORS, y_max=len(self.state))
        dd.draw_string((origin[0], origin[1] + size[1] + 0.8), "S (blue)  I (red)  R (gray)", b2d.HexColor.White)


if __name__ == "__main__":
    BatchEpidemic.run()
