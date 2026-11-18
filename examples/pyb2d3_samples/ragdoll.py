"""Fifteen colorful ragdolls in a box (the ragdoll itself is in examples_common/ragdoll.py)."""

import random

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample

from .examples_common.ragdoll import Ragdoll as RagdollBody

BOX = 30  # half size of the box (m)
N_RAGDOLLS = 15
SCALE = 7.0  # the ragdolls are about 1.6 * SCALE m tall


@register_sample("Demos", "Ragdoll", video=True)
class Ragdoll(SampleBase):
    """Fifteen colorful jointed ragdolls in a box.

    Mouse: drag a limb, double click for an explosion, triple click to pull bodies in.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=BOX, hy=BOX))
        r = BOX - 2
        for _ in range(N_RAGDOLLS):
            # the feet at a random point in the lower half; weak joint springs: floppy
            position = (random.uniform(-r, r), random.uniform(-r, 0))
            RagdollBody(self.world, position=position, scale=SCALE, colorize=True, hertz=0.1)
        self.exploded = False

    def pre_update(self, dt):
        # no mouse when rendering the docs video: one explosion from the floor after 2 s
        if self.frontend.settings.headless and self.world_time > 2 and not self.exploded:
            self.exploded = True
            self.world.explode(position=(0, -BOX), radius=20, impulse_per_length=30)

    def on_double_click(self, event):
        self.world.explode(position=event.world_position, radius=20, impulse_per_length=30)

    def on_triple_click(self, event):
        self.world.explode(position=event.world_position, radius=20, impulse_per_length=-30)

    def aabb(self):
        return b2d.aabb(lower_bound=(-BOX, -BOX), upper_bound=(BOX, BOX))
