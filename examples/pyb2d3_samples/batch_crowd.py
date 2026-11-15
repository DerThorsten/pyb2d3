"""Crowd evacuation with the social force model: clogging at the exit, and a
(draggable) pillar that helps when placed off the door's axis."""

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import ParticlePool, neighbor_pairs, pair_sum, unit_and_length


class BatchCrowd(SampleBase):
    """A crowd leaves a room through one narrow exit. Everyone pushes towards
    the door: arches of people jam it until the jostling breaks them, so the
    flow comes in bursts (clogging). Evacuated people come back in on the left,
    so the flow is measured continuously.

    Sliders: how hard people push (desired speed), crowd size.
    Checkbox: a pillar in front of the exit. Mouse: drag the pillar around.
    Hint: placed a bit off the door's axis the pillar shields the door from the
    crowd's pressure, the jams break sooner: about 40 % more people get out and
    long jams get rare (the flow is noisy: watch it for a minute). Right in front
    of the door it is just one more bottleneck. Push forces: one neighbor search,
    one force call.
    """

    room = (-20.0, 20.0, -12.0, 12.0)  # x0, x1, y0, y1
    door = 0.8  # half width of the exit (~2.5 people wide)
    radius = 0.3
    # the default pillar: in front of the door and off its axis; 18 seeds x 90 s: 186
    # instead of 129 people out, and no long jams. Sensitive to the position
    # (1.5 / 0.6 / 0.5: worse).
    pillar_offset = 1.8  # pillar center in front of the door (inside the room)
    pillar_y = 0.8  # pillar center beside the door's axis
    pillar_radius = 0.6
    pillar_speed = 8.0  # m/s: how fast a dragged pillar follows the mouse
    FRICTION = 0.5  # between people: what makes the arches at the door hold
    NOISE = 2.0  # random push (m/s^2): jostling
    SOCIAL = 4.0  # repulsion between people at contact (m/s^2)
    WALL_FRICTION = 0.05
    MAX_IMPATIENCE = 8.0  # jostling grows with the time stuck, up to (1 + this) x NOISE

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.count = 500
        self.desired_speed = 3.0
        self.pillar_on = False
        self.pillar = None
        self.pillar_pos = np.array([self.room[1] - self.pillar_offset, self.pillar_y])
        self.pillar_target = self.pillar_pos.copy()  # where a dragged pillar goes
        self.dragging_pillar = False
        self.rng = np.random.default_rng(21)
        self.build_room()
        self.pool = None
        self.reset()
        for widget in (
            widgets.FloatSlider("desired speed", 0.5, 6.0, 0.25, self.desired_speed, self.setter("desired_speed")),
            widgets.IntSlider("people", 100, 800, 50, self.count, self.set_count),
            widgets.Checkbox("pillar in front of the exit", self.pillar_on, self.set_pillar),
            widgets.Button("reset", self.reset),
        ):
            self.frontend.add_widget(widget)

    def setter(self, name):
        """a widget callback setting attribute `name`"""
        return lambda value: setattr(self, name, value)

    def aabb(self):
        x0, x1, y0, y1 = self.room
        return b2d.aabb(lower_bound=(x0 - 1.0, y0 - 2.0), upper_bound=(x1 + 6.0, y1 + 3.0))

    def build_room(self):
        """walls with a door in the middle of the right wall"""
        x0, x1, y0, y1 = self.room
        walls = self.world.create_static_body()
        # little wall friction: arches anchored at the door posts slip now and then
        wall_def = b2d.shape_def(material=b2d.surface_material(friction=self.WALL_FRICTION,
                                                                custom_color=b2d.HexColor.SlateGray))
        t = 0.3
        walls.create_shape(wall_def, b2d.box(0.5 * (x1 - x0) + t, t, center=(0.5 * (x0 + x1), y1 + t)))
        walls.create_shape(wall_def, b2d.box(0.5 * (x1 - x0) + t, t, center=(0.5 * (x0 + x1), y0 - t)))
        walls.create_shape(wall_def, b2d.box(t, 0.5 * (y1 - y0), center=(x0 - t, 0.5 * (y0 + y1))))
        upper = 0.5 * (y1 - self.door)
        walls.create_shape(wall_def, b2d.box(t, 0.5 * (y1 - self.door), center=(x1 + t, self.door + upper)))
        walls.create_shape(wall_def, b2d.box(t, 0.5 * (-self.door - y0), center=(x1 + t, -self.door - 0.5 * (-self.door - y0))))

    def set_pillar(self, value):
        """checkbox: the pillar (a static circle, draggable) in front of the exit"""
        self.pillar_on = bool(value)
        self.dragging_pillar = False
        if self.pillar is not None:
            self.pillar.destroy()
            self.pillar = None
        if self.pillar_on:
            self.pillar_target = self.pillar_pos.copy()
            # static (contacts with a kinematic pillar gave a measurably worse flow)
            self.pillar = self.world.create_static_body(position=tuple(self.pillar_pos))
            pillar_def = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.Gold))
            self.pillar.create_shape(pillar_def, b2d.circle(radius=self.pillar_radius))
        self.restart_count()

    def clamp_to_room(self, point):
        """`point` moved inside the room (the pillar stays inside, off the walls)"""
        x0, x1, y0, y1 = self.room
        m = self.pillar_radius + 0.1
        return np.clip(np.asarray(point, dtype=np.float64), (x0 + m, y0 + m), (x1 - m, y1 - m))

    def move_pillar(self, dt):
        """the static pillar towards its target in small steps (at most
        pillar_speed): box2d pushes the people it overlaps out of the way"""
        step = self.pillar_target - self.pillar_pos
        distance = float(np.hypot(*step))
        if distance < 1e-6:
            return
        if distance > self.pillar_speed * dt:
            step *= self.pillar_speed * dt / distance
        self.pillar_pos = self.pillar_pos + step
        self.pillar.set_transform(tuple(self.pillar_pos), b2d.make_rot(0.0))

    # ---- mouse: drag the pillar (elsewhere: the usual body / camera dragging) ----------

    def on_mouse_down(self, event):
        """a press on the pillar grabs it"""
        p = np.array([event.world_position[0], event.world_position[1]])
        if self.pillar is not None and np.hypot(*(p - self.pillar_pos)) < self.pillar_radius + 0.3:
            self.dragging_pillar = True
            self.pillar_target = self.clamp_to_room(p)
            return
        super().on_mouse_down(event)

    def on_mouse_move(self, event):
        """a grabbed pillar follows the mouse"""
        if self.dragging_pillar:
            self.pillar_target = self.clamp_to_room((event.world_position[0], event.world_position[1]))
            return
        super().on_mouse_move(event)

    def on_mouse_up(self, event):
        """release the pillar"""
        if self.dragging_pillar:
            self.dragging_pillar = False
            self.restart_count()  # measure the flow at the new place
        super().on_mouse_up(event)

    def on_mouse_leave(self, event):
        """the mouse left the canvas: release the pillar"""
        self.dragging_pillar = False
        super().on_mouse_leave(event)

    def set_count(self, value):
        """slider: crowd size"""
        self.count = int(value)
        self.reset()

    def reset(self):
        """a new crowd filling the left part of the room"""
        if self.pool is not None:
            self.pool.destroy(self)
        self.pool = ParticlePool(self.world, self.count, self.radius, int(b2d.HexColor.Tan.value),
                                 friction=self.FRICTION, restitution=0.0,
                                 enable_sleep=False)  # a jammed arch must not fall asleep
        self.pool.emit(self.free_spots(self.count, 0.75), np.zeros((self.count, 2)))
        self.stuck = np.zeros(self.count)  # seconds each person has been stuck
        self.restart_count()

    def restart_count(self):
        """start measuring the flow again"""
        self.evacuated = 0
        self.exit_times = []

    def free_spots(self, count, depth):
        """random positions in the left `depth` share of the room"""
        x0, x1, y0, y1 = self.room
        m = 0.5
        right = x0 + depth * (x1 - x0)
        return self.rng.uniform((x0 + m, y0 + m), (right, y1 - m), (count, 2))

    # ---- social force ---------------------------------------------------------------------------

    def pre_update(self, dt):
        """drive towards the door + repulsion between people (one force call)"""
        bodies = self.pool.bodies
        p = bodies.position
        v = bodies.linear_velocity
        n = len(p)
        x1 = self.room[1]

        # aim: in line with the opening straight through, beside it at the opening
        # itself (sideways first close to the wall: sliding along it to the door)
        opening = self.door - self.radius
        in_line = np.abs(p[:, 1]) < opening
        aim = np.empty_like(p)
        aim[:, 0] = np.where(in_line, x1 + 3.0 - p[:, 0], np.maximum(x1 - 0.6 - p[:, 0], 0.05))
        aim[:, 1] = np.clip(p[:, 1], -opening, opening) - p[:, 1]
        direction, _ = unit_and_length(aim)
        drive = 2.0 * (self.desired_speed * direction - v)  # relaxation time 0.5 s
        # impatience: who is stuck jostles harder the longer it takes; this
        # breaks the arches at the door after a while (bursts of flow)
        speed = np.sqrt(np.einsum("ij,ij->i", v, v))
        self.stuck = np.where(speed < 0.25 * self.desired_speed, self.stuck + dt, 0.0)
        jostle = self.NOISE * (1.0 + np.minimum(self.stuck, self.MAX_IMPATIENCE))
        drive += jostle[:, None] * self.rng.normal(size=drive.shape)

        # repulsion: a soft exponential social force between close people (weaker
        # than the drive: box2d's contacts already keep them apart, a strong
        # repulsion would freeze the crowd in front of the door)
        i, j, delta, dist = neighbor_pairs(p, 4.0 * self.radius)
        push = self.SOCIAL * np.exp(-(dist - 2.0 * self.radius) / 0.2)
        away = -pair_sum(n, i, j, delta / np.maximum(dist, 1e-3)[:, None] * push[:, None])
        if self.pillar is not None:
            self.move_pillar(dt)
            # the pillar is an obstacle: pushed away from it + steered around it
            # (towards the side they are already on)
            center = self.pillar_pos
            off, d = unit_and_length(p - center)
            near = np.exp(-(d - self.pillar_radius - self.radius) / 0.2)  # short range, like people
            side = np.where(off[:, 1] >= 0.0, 1.0, -1.0)
            around = np.stack([np.zeros(n), side], axis=1)
            behind = p[:, 0] < center[0]
            away += (2.0 * self.SOCIAL * near)[:, None] * off + (behind * self.SOCIAL * near)[:, None] * around
        bodies.apply_force_to_center(bodies.mass[:, None] * (drive + away))

        # out of the door: count, park and let them come back in on the left
        out = self.pool.active & (p[:, 0] > x1 + 2.0)
        k = int(np.count_nonzero(out))
        if k:
            self.evacuated += k
            self.exit_times.extend([self.world_time] * k)
            self.pool.park(out)
            self.pool.emit(self.free_spots(k, 0.15), np.zeros((k, 2)))

    def flow(self, window=10.0):
        """people per second through the door, over the last `window` seconds"""
        recent = [t for t in self.exit_times if t > self.world_time - window]
        del self.exit_times[: len(self.exit_times) - len(recent)]
        span = min(window, self.world_time) or 1.0
        return len(recent) / span

    # ---- drawing ----------------------------------------------------------------------------

    def post_debug_draw(self):
        """counters"""
        x0, _, _, y1 = self.room
        pillar = "with pillar (drag it)" if self.pillar_on else "no pillar"
        text = f"{pillar}: evacuated {self.evacuated}   flow {self.flow():.2f} / s (last 10 s)"
        self.debug_draw.draw_string((x0, y1 + 1.6), text, b2d.HexColor.White)


if __name__ == "__main__":
    BatchCrowd.run()
