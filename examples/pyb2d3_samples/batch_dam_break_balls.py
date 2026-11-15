"""Dam break with plain rigid balls: a column of circle bodies behind a gate floods a
tank with an obstacle; only box2d's contacts, no fluid forces."""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import create_circles, destroy_bodies, hsv_colors


class BatchDamBreakBalls(SampleBase):
    """A dam break with ordinary bodies: every water "particle" is a rigid ball, the
    gate opens after a second and the column floods the tank over an obstacle.

    Keys: space opens / closes the gate, r resets.
    Mouse: drag the obstacle (or any ball).
    Sliders: number of balls, ball friction.
    Hint: with low friction the balls flow almost like a liquid; raise it and the
    column collapses like sand (a slope that stays). Compare with the SPH "Dam Break".
    """

    tank = (24.0, 12.0)
    radius = 0.12
    open_after = 1.0  # seconds
    max_column_height = 0.85  # of the tank height: the column gets wider instead
    obstacle_x = 0.75  # of the tank width (right of the widest column)

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.count = 1500
        self.friction = 0.05
        self.balls = b2d.Bodies()
        self.gate = None
        self.column_width = 6.0  # set by reset: the water column behind the gate
        self.create_tank()
        self.reset()
        for widget in (
            widgets.Button("open / close the gate (space)", self.toggle_gate),
            widgets.IntSlider("balls", 300, 2500, 100, self.count, self.set_count),
            widgets.FloatSlider("friction", 0.0, 1.0, 0.05, self.friction, self.set_friction),
            widgets.Button("reset (r)", self.reset),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        w, h = self.tank
        return b2d.aabb(lower_bound=(-1.0, -1.0), upper_bound=(w + 1.0, h + 1.5))

    def create_tank(self):
        """the tank walls and a heavy dynamic obstacle block on its floor (drag it; the
        water pushes it)"""
        w, h = self.tank
        tank = self.world.create_static_body()
        wall_def = b2d.shape_def(
            material=b2d.surface_material(friction=0.2, custom_color=b2d.HexColor.SlateGray)
        )
        tank.create_shape(wall_def, b2d.box(w / 2 + 1.0, 0.5, center=(w / 2, -0.5)))
        tank.create_shape(wall_def, b2d.box(0.5, h, center=(-0.5, h)))
        tank.create_shape(wall_def, b2d.box(0.5, h, center=(w + 0.5, h)))
        self.obstacle = self.world.create_dynamic_body(position=(self.obstacle_x * w, 1.2))
        obstacle_def = b2d.shape_def(
            density=3.0, material=b2d.surface_material(friction=0.6, custom_color=b2d.HexColor.Peru)
        )
        self.obstacle.create_shape(obstacle_def, b2d.box(0.8, 1.2))

    def close_gate(self):
        """the gate: a thin static wall at the right edge of the column"""
        if self.gate is None:
            self.gate = self.world.create_static_body(
                position=(self.column_width + 0.1, self.tank[1] / 2)
            )
            gate_def = b2d.shape_def(
                material=b2d.surface_material(friction=0.0, custom_color=b2d.HexColor.LightGray)
            )
            self.gate.create_shape(gate_def, b2d.box(0.1, self.tank[1] / 2))

    def open_gate(self):
        """remove the gate: the column collapses"""
        if self.gate is not None:
            self.gate.destroy()
            self.gate = None

    def toggle_gate(self):
        """button / space"""
        if self.gate is None:
            self.close_gate()
        else:
            self.open_gate()

    def reset(self):
        """a fresh column of balls behind a closed gate"""
        destroy_bodies(self, self.balls)
        # a slightly jittered square grid, filled from the bottom; as many columns as
        # needed to stay below max_column_height (the gate follows the column)
        spacing = 2.05 * self.radius
        max_rows = int(self.max_column_height * self.tank[1] / spacing)
        columns = max(8, int(np.ceil(self.count / max_rows)))
        rows = int(np.ceil(self.count / columns))
        self.column_width = (columns + 1) * spacing
        self.open_gate()  # (a new column: the gate moves with its width)
        self.close_gate()
        self.opened = False
        self.time = 0.0
        gx, gy = np.meshgrid(np.arange(columns), np.arange(rows))
        positions = np.stack([gx.ravel(), gy.ravel()], axis=1)[: self.count] * spacing + spacing
        positions[:, 0] += np.random.default_rng(1).uniform(-0.01, 0.01, len(positions))
        colors = hsv_colors(
            0.55 + 0.06 * positions[:, 1] / max(positions[:, 1].max(), 1.0), 0.7, 0.95
        )
        self.balls = create_circles(
            self.world,
            positions,
            self.radius,
            colors=colors,
            density=1.0,
            friction=self.friction,
            restitution=0.0,
        )

    def set_count(self, value):
        """slider: number of balls (starts over)"""
        self.count = int(value)
        self.reset()

    def set_friction(self, value):
        """slider: friction of the balls (also for the running ones)"""
        self.friction = value
        for body in self.balls:
            for shape in body.shapes:
                shape.friction = value

    def on_key_down(self, event):
        """space: gate, r: reset"""
        if event.key == "space":
            self.toggle_gate()
        elif event.key == "r":
            self.reset()

    def pre_update(self, dt):
        """open the gate once, after `open_after` seconds"""
        self.time += dt
        if not self.opened and self.time >= self.open_after:
            self.opened = True
            self.open_gate()

    def post_debug_draw(self):
        """the state: how far the water got (right-most ball)"""
        front = float(self.balls.position[:, 0].max()) if len(self.balls) else 0.0
        gate = "closed" if self.gate is not None else "open"
        text = f"{len(self.balls)} balls, gate {gate}, front at x = {front:.1f}"
        self.debug_draw.draw_string((0.0, self.tank[1] + 1.0), text, b2d.HexColor.White)
