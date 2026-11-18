"""An hourglass on a pivot: grains flow through a narrow neck; turn it with the
mouse (or flip it) and watch them run again."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import create_circles, hsv_colors


def wrap(angle):
    """angle in [-pi, pi)"""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


@register_sample("Granular", "Hourglass", video=True)
class BatchHourglass(SampleBase):
    """An hourglass on a pivot: grains pile up, arch over the neck and trickle
    through.
    Keys: space flips the glass.
    Mouse: grab the glass and turn it.
    Hint: a narrow neck jams (arching).
    """

    half_height = 8.0
    half_width = 4.5
    grain_radius = 0.075
    # glass and grains are both dynamic: their contacts are softer than contacts with a
    # kinematic body and there is no continuous collision between them. Thick capsule
    # walls and a motor with a speed limit (the glass ends move max_spin * 8.6 m/s) keep
    # the grains in (2 rad/s lets some out)
    wall_radius = 0.2
    max_spin = 1.0  # rad / s
    friction_torque = 3000.0  # the pivot holds the glass when nobody turns it

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.count = 1500
        self.neck = 0.9  # neck width
        self.glass = None
        self.grains = b2d.Bodies()
        self.target_angle = None  # the motor turns the glass there (flip / mouse)
        self.grab = None  # (mouse angle, glass angle) when the glass was grabbed
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

    def wall_capsules(self, points, side):
        """thick walls along a polyline: capsules on the outline moved outwards by their
        radius (the glass gets no smaller). Capsules overlap at the corners: a grain
        wedged into a corner is pushed back in (polygons meeting at a corner leave a
        seam along which the pile squeezes grains out)"""
        direction = np.diff(points, axis=0)
        direction /= np.linalg.norm(direction, axis=1)[:, None]
        normal = np.stack([-direction[:, 1], direction[:, 0]], axis=1) * side  # outwards
        # vertex offsets: the segment normal at both ends, the miter in between
        offset = np.concatenate([normal[:1], normal[:-1] + normal[1:], normal[-1:]])
        inner = 1.0 + np.einsum("ij,ij->i", normal[:-1], normal[1:])
        offset[1:-1] /= inner[:, None]
        axis = points + self.wall_radius * offset
        return [
            b2d.capsule(tuple(p), tuple(q), self.wall_radius) for p, q in zip(axis[:-1], axis[1:])
        ]

    def build(self):
        self.grains.destroy()
        if self.glass is not None:
            self.glass.destroy()  # destroys the pivot joint too
        self.target_angle = None
        self.grab = None
        self.glass = self.world.create_dynamic_body(position=(0.0, 0.0), enable_sleep=False)
        glass_def = b2d.shape_def(
            density=5.0,
            material=b2d.surface_material(friction=0.5, custom_color=b2d.HexColor.LightSkyBlue),
        )
        right = np.array(self.outline())
        for side in (1.0, -1.0):
            for capsule in self.wall_capsules(right * (side, 1.0), side):
                self.glass.create_shape(glass_def, capsule)
        # the pivot: its motor turns the glass; at rest (target speed 0, small torque) it
        # is friction that holds the glass
        self.pivot = self.world.create_revolute_joint(
            body_a=self.anchor_body,
            body_b=self.glass,
            enable_motor=True,
            motor_speed=0.0,
            max_motor_torque=self.friction_torque,
        )

        # grains on a grid in the upper bulb, from the top down
        step = 2.15 * self.grain_radius
        xs = np.arange(-self.half_width, self.half_width, step)
        ys = np.arange(self.half_height, 0.0, -step)
        gx, gy = np.meshgrid(xs, ys)
        gx, gy = gx.ravel(), gy.ravel()
        inside = self.inside_top_bulb(gx, gy)
        local = np.stack([gx[inside], gy[inside]], axis=1)[: self.count]
        colors = hsv_colors(
            0.08 + 0.06 * (local[:, 1] / self.half_height), saturation=0.55, value=0.95
        )
        self.grains = create_circles(
            self.world, local, self.grain_radius, colors=colors, friction=0.4, density=2.0
        )
        self.previous_top = len(self.grains)

    def set_count(self, value):
        self.count = int(value)
        self.build()

    def set_neck(self, value):
        self.neck = value
        self.build()

    # ---- turning --------------------------------------------------------------------------

    def angle(self):
        return self.pivot.current_angle  # in [-pi, pi)

    def flip(self):
        """half a turn, to the next upright pose"""
        self.grab = None
        self.target_angle = round(self.angle() / math.pi) * math.pi + math.pi

    def on_key_down(self, event):
        if event.key == "space":
            self.flip()

    def on_mouse_down(self, event):
        """a click inside the glass grabs the glass (not a grain): it follows the mouse
        around the pivot"""
        x, y = event.world_position
        if math.hypot(x, y) < self.half_height + 2.0 * self.wall_radius:
            self.grab = (math.atan2(y, x), self.angle())
            self.target_angle = self.angle()
        else:
            super().on_mouse_down(event)

    def on_mouse_move(self, event):
        if self.grab is not None:
            x, y = event.world_position
            mouse_angle, glass_angle = self.grab
            self.target_angle = glass_angle + wrap(math.atan2(y, x) - mouse_angle)
        else:
            super().on_mouse_move(event)

    def release(self):
        if self.grab is not None:
            self.grab = None
            self.target_angle = None

    def on_mouse_up(self, event):
        self.release()
        super().on_mouse_up(event)

    def on_mouse_leave(self, event):
        self.release()
        super().on_mouse_leave(event)

    # ---- simulation -----------------------------------------------------------------------

    def pre_update(self, dt):
        """the motor turns the glass to the target angle (speed limited), without a target
        it holds the glass by friction"""
        speed = 0.0
        if self.target_angle is not None:
            remaining = wrap(self.target_angle - self.angle())
            if self.grab is None and abs(remaining) < 0.01:
                self.target_angle = None  # flip done
            else:
                speed = float(np.clip(4.0 * remaining, -self.max_spin, self.max_spin))
        turning = self.target_angle is not None
        self.pivot.target_motor_speed = speed
        self.pivot.max_motor_torque = (20.0 if turning else 1.0) * self.friction_torque

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
            (-self.half_width, self.half_height + 1.0), text, b2d.HexColor.White
        )
