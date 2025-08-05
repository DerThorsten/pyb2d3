# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase
import random

try:
    import examples_common  # noqa: F401, E402
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import examples_common  # noqa: F401, E402


class Ragdoll(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)

        self.outer_box_radius = 30
        self.box_body = self.world.create_static_body(position=(0, 0))
        self.box_body.create_chain(
            b2d.chain_box(center=(0, 0), hx=self.outer_box_radius, hy=self.outer_box_radius)
        )

        def rand_pos():
            margin = 2
            r = self.outer_box_radius - margin
            return (random.uniform(-r, r), random.uniform(-r, 0))

        num_bodies = 15
        for _ in range(num_bodies):
            # ragdoll at the center
            self.ragdoll = examples_common.Ragdoll(
                scale=7.0,
                world=self.world,
                position=rand_pos(),
                colorize=True,
                hertz=0.1,
            )

        # only relevant for a headless ui
        self._exploded = False

    def pre_update(self, dt):
        if self.frontend.settings.headless and self.world_time > 2 and not self._exploded:
            self._exploded = True
            self.world.explode(
                position=(0, -self.outer_box_radius), radius=20, impulse_per_length=30
            )

    def on_double_click(self, event):
        self.world.explode(position=event.world_position, radius=20, impulse_per_length=30)

    def on_triple_click(self, event):
        self.world.explode(position=event.world_position, radius=20, impulse_per_length=-30)

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.outer_box_radius, -self.outer_box_radius),
            upper_bound=(self.outer_box_radius, self.outer_box_radius),
        )


if __name__ == "__main__":
    Ragdoll.run()
