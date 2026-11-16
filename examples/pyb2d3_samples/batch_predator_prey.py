"""Predators and prey: chasing, fleeing, eating, starving and breeding, all with numpy masks."""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .batch_common import ParticlePool, draw_plot, unit_and_length


def nearest_per_group(group, other, dist):
    """for pairs (group[k], other[k], dist[k]): the nearest `other` of every group
    member -> (members, their nearest other, the distance)"""
    order = np.lexsort((dist, group))
    group, other, dist = group[order], other[order], dist[order]
    members, first = np.unique(group, return_index=True)
    return members, other[first], dist[first]


@register_sample("Agents", "Predator & Prey")
class BatchPredatorPrey(SampleBase):
    """Predators (red) hunt prey (green); prey breed, predators breed when fed and
    starve otherwise: the populations rise and fall in turns (plot).
    Mouse: hold for a safe zone.
    Sliders: prey birth rate, predator hunger.
    """

    hx, hy = 40.0, 25.0  # arena half size
    prey_radius = 0.25
    predator_radius = 0.4
    prey_capacity = 700
    predator_capacity = 400
    sight = 8.0  # predators see prey, prey see predators within this distance
    prey_speed = 5.5
    predator_speed = 6.3
    meal = 4.0  # energy of one prey
    breed_energy = 16.0  # a predator with more splits in two

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.prey_birth = 0.35  # per prey and second (at low density)
        self.hunger = 1.4  # energy loss of predators per second
        self.rng = np.random.default_rng(9)
        self.safe = None  # the mouse: a zone predators avoid
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=self.hx, hy=self.hy))
        self.prey = None
        self.predators = None
        self.reset()
        for widget in (
            widgets.FloatSlider(
                "prey birth rate", 0.05, 1.0, 0.05, self.prey_birth, self.setter("prey_birth")
            ),
            widgets.FloatSlider(
                "predator hunger", 0.2, 2.0, 0.1, self.hunger, self.setter("hunger")
            ),
            widgets.Button("reset", self.reset),
        ):
            self.frontend.add_widget(widget)

    def setter(self, name):
        """a widget callback setting attribute `name`"""
        return lambda value: setattr(self, name, value)

    def aabb(self):
        return b2d.aabb(lower_bound=(-self.hx, -self.hy), upper_bound=(self.hx + 22.0, self.hy))

    def reset(self):
        """fresh pools: 250 prey, 12 predators"""
        for pool in (self.prey, self.predators):
            if pool is not None:
                pool.destroy(self)
        self.prey = ParticlePool(
            self.world,
            self.prey_capacity,
            self.prey_radius,
            int(b2d.HexColor.LimeGreen.value),
            friction=0.0,
            restitution=0.2,
        )
        self.predators = ParticlePool(
            self.world,
            self.predator_capacity,
            self.predator_radius,
            int(b2d.HexColor.OrangeRed.value),
            friction=0.0,
            restitution=0.2,
        )
        self.energy = np.zeros(self.predator_capacity)
        self.spawn(self.prey, 250)
        born = self.spawn(self.predators, 12)
        self.energy[born] = 10.0
        self.history = [[], []]  # prey, predators
        self.eaten = 0

    def spawn(self, pool, count, near=None):
        """`count` new members at random places (or next to the positions `near`)"""
        free = int(np.count_nonzero(~pool.active))
        count = min(count, free)
        if count <= 0:
            return np.zeros(0, dtype=np.int64)
        m = 1.0
        if near is None:
            positions = self.rng.uniform(
                (-self.hx + m, -self.hy + m), (self.hx - m, self.hy - m), (count, 2)
            )
        else:
            positions = np.clip(
                near[:count] + self.rng.normal(scale=0.8, size=(count, 2)),
                (-self.hx + m, -self.hy + m),
                (self.hx - m, self.hy - m),
            )
        angle = self.rng.uniform(0, 2 * np.pi, count)
        velocities = 2.0 * np.stack([np.cos(angle), np.sin(angle)], axis=1)
        return pool.emit(positions, velocities)

    # ---- one step: perception, steering, eating, births, deaths ------------------------------------

    def pre_update(self, dt):
        """steering forces for both species (one call per species), eating, breeding, starving"""
        prey_idx = np.flatnonzero(self.prey.active)
        pred_idx = np.flatnonzero(self.predators.active)
        prey_p = self.prey.bodies.position[prey_idx]
        pred_p = self.predators.bodies.position[pred_idx]
        n_prey = len(prey_idx)

        # all predator-prey distances at once (few predators: a dense array is
        # cheaper than a neighbor search), pairs within sight: prey a, predator b
        to_pred_all = pred_p[None, :, :] - prey_p[:, None, :]  # (prey, predators, 2)
        dist_all = np.sqrt(np.einsum("abk,abk->ab", to_pred_all, to_pred_all))
        a, b = np.nonzero(dist_all < self.sight)
        to_pred, dist = to_pred_all[a, b], dist_all[a, b]

        # predators: chase the nearest prey, else wander
        pred_desired = self.wander(self.predators, pred_idx, self.predator_speed * 0.5)
        hunters, target, target_dist = nearest_per_group(b, a, dist)
        if len(hunters):
            chase, _ = unit_and_length(prey_p[target] - pred_p[hunters])
            pred_desired[hunters] = self.predator_speed * chase
        if self.safe is not None and len(pred_idx):
            away, d = unit_and_length(pred_p - self.safe)
            inside = d < 10.0
            pred_desired[inside] = self.predator_speed * away[inside]

        # prey: flee from all predators in sight (closer ones count more), else wander
        prey_desired = self.wander(self.prey, prey_idx, self.prey_speed * 0.4)
        weight = (1.0 - dist / self.sight) ** 2
        flee = np.zeros((n_prey, 2))
        for axis in range(2):
            flee[:, axis] = -np.bincount(
                a, to_pred[:, axis] / np.maximum(dist, 1e-3) * weight, n_prey
            )
        scared = np.bincount(a, minlength=n_prey) > 0
        direction, _ = unit_and_length(flee[scared])
        prey_desired[scared] = self.prey_speed * direction

        self.steer(self.prey, prey_idx, prey_desired)
        self.steer(self.predators, pred_idx, pred_desired)

        # eating: a predator touching its nearest prey (each prey once)
        bite = target_dist < self.prey_radius + self.predator_radius + 0.15
        eaters, meals = hunters[bite], target[bite]
        meals, first = np.unique(meals, return_index=True)
        eaters = eaters[first]
        eaten = np.zeros(self.prey_capacity, dtype=bool)
        eaten[prey_idx[meals]] = True
        self.prey.park(eaten)
        self.energy[pred_idx[eaters]] += self.meal
        self.eaten += len(meals)

        # predators: hunger, starving, breeding when well fed
        self.energy[pred_idx] -= self.hunger * dt
        starved = np.zeros(self.predator_capacity, dtype=bool)
        starved[pred_idx[self.energy[pred_idx] <= 0.0]] = True
        self.predators.park(starved)
        fed = pred_idx[self.energy[pred_idx] > self.breed_energy]
        if len(fed):
            kids = self.spawn(self.predators, len(fed), near=self.predators.bodies.position[fed])
            self.energy[fed[: len(kids)]] -= 0.5 * self.breed_energy
            self.energy[kids] = 0.5 * self.breed_energy

        # prey: logistic births next to their parents
        n_prey = int(np.count_nonzero(self.prey.active))
        rate = self.prey_birth * n_prey * max(0.0, 1.0 - n_prey / (0.9 * self.prey_capacity)) * dt
        births = self.rng.poisson(rate)
        if births and n_prey:
            parents = self.rng.choice(np.flatnonzero(self.prey.active), births)
            self.spawn(self.prey, births, near=self.prey.bodies.position[parents])

        # extinction: a few newcomers wander in after a while
        if n_prey == 0:
            self.spawn(self.prey, 20)
        if not self.predators.active.any() and self.world_iteration % 300 == 0:
            self.energy[self.spawn(self.predators, 3)] = 10.0

    def wander(self, pool, idx, speed):
        """desired velocities: keep the current heading at `speed`, turning slowly"""
        v = pool.bodies.linear_velocity[idx]
        heading, _ = unit_and_length(v + self.rng.normal(scale=0.6, size=v.shape))
        return speed * heading

    def steer(self, pool, idx, desired):
        """one force call towards the desired velocities"""
        if len(idx) == 0:
            return
        bodies = pool.bodies[idx]
        bodies.apply_force_to_center(
            4.0 * bodies.mass[:, None] * (desired - bodies.linear_velocity)
        )

    def post_update(self, dt):
        """population history (4 samples per second)"""
        if self.world_iteration % 15 == 0:
            self.history[0].append(int(np.count_nonzero(self.prey.active)))
            self.history[1].append(int(np.count_nonzero(self.predators.active)))
            for series in self.history:
                del series[:-600]

    # ---- mouse: a safe zone -----------------------------------------------------------------

    def on_mouse_down(self, event):
        """safe zone at the cursor while the button is held"""
        self.mouse_pos = event.world_position
        self.safe = np.array(self.mouse_pos, dtype=np.float64)

    def on_mouse_move(self, event):
        """move the safe zone"""
        self.mouse_pos = event.world_position
        if self.safe is not None:
            self.safe = np.array(self.mouse_pos, dtype=np.float64)

    def on_mouse_up(self, event):
        """safe zone gone"""
        super().on_mouse_up(event)
        self.safe = None

    def on_mouse_leave(self, event):
        """safe zone gone"""
        super().on_mouse_leave(event)
        self.safe = None

    # ---- drawing ----------------------------------------------------------------------------

    def post_debug_draw(self):
        """populations as numbers + curves (prey scaled down 5x)"""
        dd = self.debug_draw
        if self.safe is not None:
            dd.draw_circle(tuple(self.safe), 10.0, b2d.HexColor.LightSkyBlue)
        prey = int(np.count_nonzero(self.prey.active))
        predators = int(np.count_nonzero(self.predators.active))
        dd.draw_string(
            (-self.hx, self.hy + 1.0),
            f"prey {prey}  predators {predators}  eaten {self.eaten}",
            b2d.HexColor.White,
        )
        origin, size = (self.hx + 2.0, -10.0), (18.0, 20.0)
        prey_curve = [v / 5.0 for v in self.history[0]]
        top = max([1.0] + prey_curve + self.history[1])
        draw_plot(
            dd,
            origin,
            size,
            [prey_curve, self.history[1]],
            [b2d.HexColor.LimeGreen, b2d.HexColor.OrangeRed],
            y_max=top,
        )
        dd.draw_string(
            (origin[0], origin[1] + size[1] + 0.8),
            "prey / 5 (green), predators (red)",
            b2d.HexColor.White,
        )
