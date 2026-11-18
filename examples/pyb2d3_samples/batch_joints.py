"""Every joint type driven each frame, with the typed joint batches and with a python loop.

One tile per joint type, a grid of small mechanisms in each. Every frame each type gets a new
setting (motor speeds, rest lengths, spring stiffness, velocities) and its state is read back,
both with one call per joint type (RevoluteJoints, PrismaticJoints, ...) and joint by joint:
the two write the same values, each is timed, both times are shown.
"""

import math
import time

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

from .examples_common.batch import Ema

BATCH, LOOP = "batch API", "python loop"
TYPES = ["revolute", "prismatic", "wheel", "distance", "pogo", "motor", "mover", "weld"]
SPACING = 1.6  # between the mechanisms of a tile
VERTICAL = b2d.make_rot(0.5 * math.pi)  # a joint frame whose x axis points up


@register_sample("Batch API", "Joint Batches", video=True)
class JointBatches(SampleBase):
    """Every joint type driven each frame, twice: one batch call per type (RevoluteJoints, ...)
    and a python loop over the joints. Both write the same values; the times of both are shown.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        # hundreds of joint drawings would hide the bodies (debug draw panel: back on)
        self.debug_draw.draw_joints = False
        self.side = 8  # mechanisms per tile: side x side
        self.timings = {BATCH: Ema(), LOOP: Ema()}
        self.t = 0.0
        self.bodies = b2d.Bodies()
        self.build()
        self.frontend.add_widget(
            widgets.IntSlider("grid per type", 2, 20, 1, self.side, self.set_side)
        )

    # ---- building ---------------------------------------------------------------------------

    def tile_size(self):
        """the distance between neighboring tiles (with room for the frames and labels)"""
        return (self.side + 1.5) * SPACING

    def tile_origin(self, index):
        """top left corner of the tile of joint type `index` (4 x 2 tiles)"""
        size = self.tile_size()
        return np.array([(index % 4) * size, -(index // 4) * size])

    def anchors(self, index):
        """the anchor points of one tile"""
        origin = self.tile_origin(index)
        k = np.arange(self.side * self.side)
        return origin + SPACING * np.stack([k % self.side + 0.5, -(k // self.side) - 0.5], axis=1)

    def build(self):
        self.bodies.destroy()  # with their joints
        self.bodies = b2d.Bodies()
        world, anchor = self.world, self.anchor_body
        joints = {name: [] for name in TYPES + ["filter"]}
        box_def = b2d.shape_def(density=1.0)

        def body(position, geometry):
            # no sleeping: setting a motor speed / rest length does not wake a body
            b = world.create_dynamic_body(position=tuple(position), enable_sleep=False)
            b.create_shape(box_def, geometry)
            self.bodies.append(b)
            return b

        arms = []
        for i, name in enumerate(TYPES):
            for a in self.anchors(i):
                a = tuple(a)
                if name == "revolute":  # a motor arm
                    arm = body((a[0] + 0.5, a[1]), b2d.box(0.55, 0.15))
                    j = world.create_revolute_joint(
                        anchor,
                        arm,
                        local_anchor_a=a,
                        local_anchor_b=(-0.5, 0),
                        enable_motor=True,
                        max_motor_torque=20.0,
                    )
                    arms.append(arm)
                elif name == "prismatic":  # a piston moving up and down
                    piston = body(a, b2d.box(0.25, 0.25))
                    j = world.create_prismatic_joint(
                        anchor,
                        piston,
                        local_frame_a=b2d.transform(a, VERTICAL),
                        local_frame_b=b2d.transform((0, 0), VERTICAL),
                        enable_limit=True,
                        lower_translation=-0.5,
                        upper_translation=0.5,
                        enable_motor=True,
                        max_motor_force=200.0,
                    )
                elif name == "wheel":  # a sprung wheel spinning back and forth
                    wheel = body(a, b2d.circle(radius=0.3))
                    j = world.create_wheel_joint(
                        anchor,
                        wheel,
                        local_frame_a=b2d.transform(a, VERTICAL),
                        local_frame_b=b2d.transform((0, 0), VERTICAL),
                        enable_spring=True,
                        hertz=3.0,
                        damping_ratio=0.5,
                        enable_motor=True,
                        max_motor_torque=10.0,
                    )
                elif name == "distance":  # a ball on a spring
                    ball = body((a[0], a[1] - 0.6), b2d.circle(radius=0.2))
                    j = world.create_distance_joint(
                        anchor,
                        ball,
                        local_anchor_a=a,
                        length=0.6,
                        enable_spring=True,
                        hertz=4.0,
                        damping_ratio=0.3,
                    )
                elif name == "pogo":  # a box on a pogo spring (pushes / pulls along the normal)
                    box = body((a[0], a[1] + 0.4), b2d.box(0.3, 0.3))
                    j = world.create_pogo_joint(
                        anchor,
                        box,
                        local_anchor_a=a,
                        normal=(0, 1),
                        rest_length=0.4,
                        hertz=4.0,
                        damping_ratio=0.3,
                        max_compression_force=200.0,
                        max_tension_force=200.0,
                    )
                elif name == "motor":  # a box spun in place by a motor joint
                    box = body(a, b2d.box(0.4, 0.15))
                    j = world.create_motor_joint(
                        anchor,
                        box,
                        local_anchor_a=a,
                        linear_hertz=5.0,
                        max_spring_force=500.0,
                        max_velocity_torque=50.0,
                    )
                elif name == "mover":  # a box moved with a velocity
                    box = body(a, b2d.box(0.25, 0.25))
                    j = world.create_mover_joint(
                        anchor,
                        box,
                        local_anchor_a=a,
                        max_velocity_force=(500.0, 500.0),
                    )
                else:  # weld: a beam whose angular stiffness changes
                    beam = body((a[0] + 0.5, a[1]), b2d.box(0.55, 0.06))
                    j = world.create_weld_joint(
                        anchor,
                        beam,
                        local_anchor_a=a,
                        local_anchor_b=(-0.5, 0),
                        angular_damping_ratio=0.5,
                    )
                joints[name].append(j)

        # neighboring arms of a row pass through each other: filter joints (no own api)
        for left, right in zip(arms[:-1], arms[1:]):
            joints["filter"].append(world.create_filter_joint(left, right))

        # the typed batches (each checks that its joints are of its type) and plain lists
        self.batches = {
            "revolute": b2d.RevoluteJoints(joints["revolute"]),
            "prismatic": b2d.PrismaticJoints(joints["prismatic"]),
            "wheel": b2d.WheelJoints(joints["wheel"]),
            "distance": b2d.DistanceJoints(joints["distance"]),
            "pogo": b2d.PogoJoints(joints["pogo"]),
            "motor": b2d.MotorJoints(joints["motor"]),
            "mover": b2d.MoverJoints(joints["mover"]),
            "weld": b2d.WeldJoints(joints["weld"]),
            "filter": b2d.FilterJoints(joints["filter"]),
        }
        self.lists = {name: [j.cast() for j in joints[name]] for name in joints}
        n = self.side * self.side
        self.phase = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False, dtype=np.float32)
        self.observed = 0.0
        for ema in self.timings.values():
            ema.value = None

    def set_side(self, value):
        self.side = int(value)
        self.build()

    def aabb(self):
        size = self.tile_size()
        return b2d.aabb(lower_bound=(-1.0, -2.0 * size - 5.0), upper_bound=(4.0 * size + 1.0, 2.0))

    # ---- driving: the same settings, twice -----------------------------------------------

    def drive_batch(self, t):
        s = np.sin(t + self.phase)
        b = self.batches
        b["revolute"].target_motor_speed = 4.0 * s
        b["prismatic"].target_motor_speed = 2.0 * s
        b["wheel"].target_motor_speed = 15.0 * s
        b["distance"].rest_length = 0.6 + 0.3 * s
        b["pogo"].rest_length = 0.4 + 0.2 * s
        b["motor"].angular_velocity = 3.0 * s
        b["mover"].linear_velocity = np.stack(
            [np.zeros_like(s), 0.5 * np.cos(t + self.phase)], axis=1
        )
        b["weld"].angular_hertz = 1.0 + 4.0 * (1.0 + s)
        # read the state back (an agent's observation)
        return float(
            b["revolute"].current_angle.sum()
            + b["prismatic"].current_translation.sum()
            + b["wheel"].current_motor_torque.sum()
            + b["distance"].current_length.sum()
            + b["pogo"].current_length.sum()
        )

    def drive_loop(self, t):
        lists = self.lists
        observed = 0.0
        for j, p in zip(lists["revolute"], self.phase):
            j.target_motor_speed = 4.0 * math.sin(t + p)
            observed += j.current_angle
        for j, p in zip(lists["prismatic"], self.phase):
            j.target_motor_speed = 2.0 * math.sin(t + p)
            observed += j.current_translation
        for j, p in zip(lists["wheel"], self.phase):
            j.target_motor_speed = 15.0 * math.sin(t + p)
            observed += j.current_motor_torque
        for j, p in zip(lists["distance"], self.phase):
            j.rest_length = 0.6 + 0.3 * math.sin(t + p)
            observed += j.current_length
        for j, p in zip(lists["pogo"], self.phase):
            j.rest_length = 0.4 + 0.2 * math.sin(t + p)
            observed += j.current_length
        for j, p in zip(lists["motor"], self.phase):
            j.angular_velocity = 3.0 * math.sin(t + p)
        for j, p in zip(lists["mover"], self.phase):
            j.linear_velocity = (0.0, 0.5 * math.cos(t + p))
        for j, p in zip(lists["weld"], self.phase):
            j.angular_hertz = 1.0 + 4.0 * (1.0 + math.sin(t + p))
        return observed

    def pre_update(self, dt):
        self.t += dt
        # both write the same values (the batch last), each one timed
        for mode, drive in ((LOOP, self.drive_loop), (BATCH, self.drive_batch)):
            t0 = time.perf_counter()
            self.observed = drive(self.t)
            self.timings[mode](1000.0 * (time.perf_counter() - t0))

    # ---- drawing ------------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        for i, name in enumerate(TYPES):
            # a frame around each tile, its label inside at the top
            x0, y0 = self.tile_origin(i)
            x1, y1 = x0 + self.side * SPACING + 0.9, y0 - self.side * SPACING - 0.6
            frame = [(x0, y0 + 1.4), (x1, y0 + 1.4), (x1, y1), (x0, y1)]
            dd.draw_polygon(frame, b2d.HexColor.DimGray)
            label = f"{name} ({len(self.batches[name])})"
            if name == "revolute":
                label += f" + {len(self.batches['filter'])} filter"
            dd.draw_string((x0 + 0.3, y0 + 0.7), label, b2d.HexColor.White)

        lines = [f"{sum(len(b) for b in self.batches.values())} joints, driven every step"]
        for mode, ema in self.timings.items():
            value = "-" if ema.value is None else f"{ema.value:.3f} ms"
            lines.append(f"{mode}: {value} per step")
        batch, loop = self.timings[BATCH].value, self.timings[LOOP].value
        if batch and loop:
            lines.append(f"batch is {loop / batch:.1f}x faster")
        y = -2.0 * self.tile_size() + 1.0  # below the tiles
        for k, line in enumerate(lines):
            dd.draw_string((0.3, y - 0.5 - 1.2 * k), line, b2d.HexColor.White)
