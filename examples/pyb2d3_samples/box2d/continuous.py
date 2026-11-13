"""Ports of box2d's samples/sample_continuous.cpp."""

import math
import random

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample, widgets

from ._common import Box2dSample
from ._continuous_helpers import attr_slider, create_box_walls, create_human, destroy_human

SHAPE_TYPES = ["Circle", "Capsule", "Box"]


def _destroy(*bodies):
    for body in bodies:
        if body is not None and body.is_valid:
            body.destroy()


@register_sample("Continuous", "Bounce House")
class BounceHouse(Box2dSample):
    """A fast bullet bouncing in a box without friction, showing hit events."""

    camera_center = (0.0, 0.0)
    camera_zoom = 25.0 * 0.45

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        create_box_walls(ground, b2d.shape_def())

        self.shape_type = "Circle"
        self.enable_hit_events = True
        self.body = None
        # the 4 most recent hits: [point, approach speed, step index]
        self.hits = [[(0.0, 0.0), 0.0, 0] for _ in range(4)]
        self.launch()

        self.frontend.add_widget(
            widgets.Dropdown(label="Shape", options=SHAPE_TYPES, value=self.shape_type, callback=self.set_shape_type)
        )
        self.frontend.add_widget(
            widgets.Checkbox(label="hit events", value=self.enable_hit_events, callback=self.set_hit_events)
        )

    def launch(self):
        _destroy(self.body)
        self.body = self.world.create_dynamic_body(
            position=(0, 0),
            linear_velocity=(10, 20),
            gravity_scale=0.0,
            is_bullet=True,
            # circle shapes centered on the body can spin fast without risk of tunnelling
            allow_fast_rotation=self.shape_type == "Circle",
        )
        shape_def = b2d.shape_def(
            density=1.0,
            material=b2d.surface_material(restitution=1.0, friction=0.0),
            enable_hit_events=self.enable_hit_events,
        )
        if self.shape_type == "Circle":
            shape = b2d.circle(radius=0.5)
        elif self.shape_type == "Capsule":
            shape = b2d.capsule((-0.5, 0), (0.5, 0), 0.25)
        else:
            shape = b2d.box(20.0 * 0.1, 0.1)
        self.body.create_shape(shape_def, shape)

    def set_shape_type(self, shape_type):
        self.shape_type = shape_type
        self.launch()

    def set_hit_events(self, flag):
        self.enable_hit_events = flag
        self.body.enable_hit_events(flag)

    def post_update(self, dt):
        for event in self.world.get_contact_events().hit_events():
            oldest = min(self.hits, key=lambda hit: hit[2])
            oldest[:] = [event.point, event.approach_speed, self.world_iteration]

    def post_debug_draw(self):
        for point, speed, step in self.hits:
            if step > 0 and self.world_iteration <= step + 30:
                self.debug_draw.draw_circle(point, 0.1, b2d.HexColor.OrangeRed.value)
                self.debug_draw.draw_string(point, f"{speed:.1f}", b2d.HexColor.White.value)


@register_sample("Continuous", "Bounce Humans")
class BounceHumans(Box2dSample):
    """Ragdolls bouncing in a box with very bouncy walls and a rotating gravity."""

    camera_center = (0.0, 0.0)
    camera_zoom = 12.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        shape_def = b2d.shape_def(material=b2d.surface_material(restitution=1.3, friction=0.1))
        create_box_walls(ground, shape_def)
        shape_def.material.restitution = 2.0
        ground.create_shape(shape_def, b2d.circle(radius=2.0))

        self.humans = []
        self.count_down = 0.0
        self.time = 0.0

    def gravity_direction(self):
        return (math.sin(0.5 * self.time), math.cos(self.time))

    def pre_update(self, dt):
        if len(self.humans) < 5 and self.count_down <= 0.0:
            self.humans.append(create_human(self.world, (0, 5), 1.0, 0.0, 1.0, 0.1))
            self.count_down = 2.0

        self.time += dt
        self.count_down -= dt
        gx, gy = self.gravity_direction()
        self.world.gravity = (10.0 * gx, 10.0 * gy)

    def post_debug_draw(self):
        gx, gy = self.gravity_direction()
        self.debug_draw.draw_segment((0, 0), (3.0 * gx, 3.0 * gy), b2d.HexColor.White.value)


@register_sample("Continuous", "Chain Drop")
class ChainDrop(Box2dSample):
    """A fast ball dropped onto a looped chain."""

    camera_center = (0.0, 0.0)
    camera_zoom = 25.0 * 0.35

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body(position=(0, -6))
        ground.create_chain(b2d.chain_def([(-10, -2), (10, -2), (10, 1), (-10, 1)], is_loop=True))

        self.body = None
        self.y_offset = -0.1
        self.speed = -42.0
        self.launch()

        self.frontend.add_widget(attr_slider(self, "Speed", "speed", -100.0, 0.0, 1.0))
        self.frontend.add_widget(attr_slider(self, "Y Offset", "y_offset", -1.0, 1.0, 0.1))
        self.frontend.add_widget(widgets.Button(label="Launch", callback=self.launch))

    def launch(self):
        _destroy(self.body)
        self.body = self.world.create_dynamic_body(
            linear_velocity=(0, self.speed),
            position=(0, 10 + self.y_offset),
            rotation=0.5 * math.pi,
            motion_locks=b2d.MotionLocks(angular_z=True),
        )
        self.body.create_shape(b2d.shape_def(), b2d.circle(radius=0.5))


def _create_ball(world, position, friction=None):
    """A ball shot to the right at 100 m/s."""
    body = world.create_dynamic_body(position=position, linear_velocity=(100, 0))
    shape_def = b2d.shape_def()
    if friction is not None:
        shape_def.material.friction = friction
    body.create_shape(shape_def, b2d.circle(radius=0.5))
    return body


@register_sample("Continuous", "Chain Slide")
class ChainSlide(Box2dSample):
    """A fast ball sliding along the inside of a looped chain."""

    camera_center = (0.0, 10.0)
    camera_zoom = 15.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        w, h = 2.0, 1.0
        x, y = 20.0, 0.0
        points = []
        for dx, dy in ((-w, 0), (0, h), (w, 0), (0, -h)):
            for _ in range(20):
                points.append((x, y))
                x += dx
                y += dy

        ground = self.world.create_static_body()
        ground.create_chain(b2d.chain_def(points, is_loop=True))

        _create_ball(self.world, (-19.5, 0.5), friction=0.0)


@register_sample("Continuous", "Segment Slide")
class SegmentSlide(Box2dSample):
    """A fast ball sliding along a segment into a wall."""

    camera_center = (0.0, 10.0)
    camera_zoom = 15.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        ground.create_shape(b2d.shape_def(), b2d.segment((-40, 0), (40, 0)))
        ground.create_shape(b2d.shape_def(), b2d.segment((40, 0), (40, 10)))

        _create_ball(self.world, (-20.0, 0.7))


@register_sample("Continuous", "Skinny Box")
class SkinnyBox(Box2dSample):
    """A fast, spinning skinny box (or capsule) dropped onto a thin static box."""

    camera_center = (1.0, 5.0)
    camera_zoom = 25.0 * 0.25

    # box2d's sample has this switched off and offers no control for it
    bullet = False

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        shape_def = b2d.shape_def(material=b2d.surface_material(friction=0.9))
        ground.create_shape(shape_def, b2d.segment((-10, 0), (10, 0)))
        ground.create_shape(shape_def, b2d.box(0.1, 1.0, center=(0, 1)))

        self.auto_test = False
        self.capsule = False
        self.body = None
        self.bullet_body = None
        self.launch()

        self.frontend.add_widget(widgets.Checkbox(label="Capsule", value=self.capsule, callback=self.set_capsule))
        self.frontend.add_widget(widgets.Button(label="Launch", callback=self.launch))
        self.frontend.add_widget(widgets.Checkbox(label="Auto Test", value=self.auto_test, callback=self.set_auto_test))

    def set_capsule(self, flag):
        self.capsule = flag

    def set_auto_test(self, flag):
        self.auto_test = flag

    def launch(self):
        _destroy(self.body, self.bullet_body)
        self.bullet_body = None

        shape_def = b2d.shape_def(density=1.0, material=b2d.surface_material(friction=0.9))
        self.body = self.world.create_dynamic_body(
            position=(0, 8),
            angular_velocity=random.uniform(-50.0, 50.0),
            linear_velocity=(0, -100),
        )
        if self.capsule:
            self.body.create_shape(shape_def, b2d.capsule((0, -1), (0, 1), 0.1))
        else:
            self.body.create_shape(shape_def, b2d.box(2.0, 0.05))

        if self.bullet:
            self.bullet_body = self.world.create_dynamic_body(
                position=(random.uniform(-1.0, 1.0), 10.0),
                angular_velocity=self.body.angular_velocity,
                linear_velocity=(0, -50),
            )
            self.bullet_body.create_shape(shape_def, b2d.box(0.25, 0.25))

    def post_update(self, dt):
        if self.auto_test and self.world_iteration % 60 == 0:
            self.launch()


@register_sample("Continuous", "Ghost Bumps")
class GhostBumps(Box2dSample):
    """Ghost bumps: a shape sliding over a smooth chain versus over separate polygons."""

    camera_center = (1.5, 16.0)
    camera_zoom = 25.0 * 0.8

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.ground = None
        self.body = None
        self.shape = None
        self.shape_type = "Circle"
        self.round = 0.0
        self.friction = 0.2
        self.bevel = 0.0
        self.use_chain = True

        self.create_scene()
        self.launch()

        add = self.frontend.add_widget
        add(widgets.Checkbox(label="Chain", value=self.use_chain, callback=self.set_use_chain))
        add(attr_slider(self, "Bevel", "bevel", 0.0, 1.0, 0.01, on_change=self.on_bevel_changed))
        add(widgets.Dropdown(label="Shape", options=SHAPE_TYPES, value=self.shape_type, callback=self.set_shape_type))
        add(attr_slider(self, "Round", "round", 0.0, 0.4, 0.1))
        add(attr_slider(self, "Friction", "friction", 0.0, 1.0, 0.1, on_change=self.on_friction_changed))
        add(widgets.Button(label="Launch", callback=self.launch))

    def set_use_chain(self, flag):
        self.use_chain = flag
        self.create_scene()

    def set_shape_type(self, shape_type):
        self.shape_type = shape_type

    def on_bevel_changed(self):
        # box2d only shows the bevel slider for the polygon ground
        if not self.use_chain:
            self.create_scene()

    def on_friction_changed(self):
        if self.shape is not None and self.shape.is_valid:
            self.shape.friction = self.friction
        self.create_scene()

    def create_scene(self):
        _destroy(self.ground)
        self.ground = self.world.create_static_body()

        m = 1.0 / math.sqrt(2.0)
        mm = 2.0 * (math.sqrt(2.0) - 1.0)
        hx, hy = 4.0, 0.25

        if self.use_chain:
            slope = 2.0 * hx * m
            corner = 2.0 * hx * m + 2.0 * hy * (1.0 - m)
            steps = (
                [(-slope, slope)] * 3
                + [(-2.0 * hy * m, -2.0 * hy * m)]
                + [(slope, -slope)] * 2
                + [(corner, -corner), (2.0 * hx + hy * mm, 0.0), (2.0 * hx, 0.0), (2.0 * hx + hy * mm, 0.0)]
                + [(corner, corner)]
                + [(slope, slope)] * 2
                + [(-2.0 * hy * m, 2.0 * hy * m)]
                + [(-slope, -slope)] * 3
                + [(-2.0 * hx, 0.0)] * 2
            )
            points = [(-3.0 * hx, hy)]
            for dx, dy in steps:
                x, y = points[-1]
                points.append((x + dx, y + dy))

            material = b2d.surface_material(friction=self.friction)
            self.ground.create_chain(b2d.chain_def(points, material=material, is_loop=True))
            return

        shape_def = b2d.shape_def(material=b2d.surface_material(friction=self.friction))
        if self.bevel > 0.0:
            hb = self.bevel
            vs = [
                (hx + hb, hy - 0.05), (hx, hy), (-hx, hy), (-hx - hb, hy - 0.05),
                (-hx - hb, -hy + 0.05), (-hx, -hy), (hx, -hy), (hx + hb, -hy + 0.05),
            ]  # fmt: skip
        else:
            vs = [(hx, hy), (-hx, hy), (-hx, -hy), (hx, -hy)]
        hull = b2d.compute_hull(vs)

        x_slope = 3.0 * hx + m * hx + m * hy
        y_slope = hy + m * hx - m * hy
        step = 2.0 * m * hx
        rows = (
            ((-x_slope, y_slope), -0.25 * math.pi, (-step, step)),  # left slope
            ((-2.0 * hx, 0.0), 0.0, (2.0 * hx, 0.0)),  # flat
            ((x_slope, y_slope), 0.25 * math.pi, (step, step)),  # right slope
        )
        for (x, y), angle, (dx, dy) in rows:
            for i in range(3):
                polygon = b2d.polygon(hull=hull, position=(x + i * dx, y + i * dy), rotation=angle)
                self.ground.create_shape(shape_def, polygon)

    def launch(self):
        _destroy(self.body)
        self.body = self.world.create_dynamic_body(position=(-28, 18), linear_velocity=(0, 0))

        shape_def = b2d.shape_def(density=1.0, material=b2d.surface_material(friction=self.friction))
        if self.shape_type == "Circle":
            shape = b2d.circle(radius=0.5)
        elif self.shape_type == "Capsule":
            shape = b2d.capsule((-0.5, 0), (0.5, 0), 0.25)
        else:
            h = 0.5 - self.round
            shape = b2d.box(h, 2.0 * h, radius=self.round)
        self.shape = self.body.create_shape(shape_def, shape)


@register_sample("Continuous", "Speculative Fallback")
class SpeculativeFallback(Box2dSample):
    """Speculative collision failure case suggested by Dirk Gregorius, handled by a fallback to prevent tunneling."""

    camera_center = (1.0, 5.0)
    camera_zoom = 25.0 * 0.25

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        ground.create_shape(b2d.shape_def(), b2d.segment((-10, 0), (10, 0)))
        ground.create_shape(b2d.shape_def(), b2d.polygon([(-2, 4), (2, 4), (2, 4.1), (-0.5, 4.2), (-2, 4.2)]))

        # fast moving skinny box, also testing a large shape offset
        offset = 8.0
        body = self.world.create_dynamic_body(position=(offset, 12), linear_velocity=(0, -100))
        body.create_shape(b2d.shape_def(), b2d.box(2.0, 0.05, center=(-offset, 0), rotation=math.pi))


@register_sample("Continuous", "Speculative Sliver")
class SpeculativeSliver(Box2dSample):
    """A fast sliver shaped triangle dropped onto the ground."""

    camera_center = (0.0, 1.75)
    camera_zoom = 2.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment(-10.0, 10.0)

        body = self.world.create_dynamic_body(position=(0, 12), linear_velocity=(0, -100))
        body.create_shape(b2d.shape_def(), b2d.polygon([(-2, 0), (-1, 0), (2, 0.5)]))


@register_sample("Continuous", "Speculative Ghost")
class SpeculativeGhost(Box2dSample):
    """Speculative collision does not lead to speculative ghost collisions at small distances."""

    camera_center = (0.0, 1.75)
    camera_zoom = 2.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.create_ground_segment(-10.0, 10.0)
        ground.create_shape(b2d.shape_def(), b2d.box(1.0, 0.1, center=(0, 0.9)))

        # the speculative distance is 0.02 meters, so this avoids it
        speed = 0.1 * 1.25 * self.frontend.settings.hertz
        body = self.world.create_dynamic_body(
            position=(0.015, 2.515), linear_velocity=(speed, -speed), gravity_scale=0.0
        )
        body.create_shape(b2d.shape_def(), b2d.box(0.25, 0.25))


PIXELS_PER_METER = 30.0


@register_sample("Continuous", "Pixel Imperfect")
class PixelImperfect(Box2dSample):
    """Box2D does not have pixel perfect collision."""

    camera_center = (7.0, 5.0)
    camera_zoom = 6.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ppm = PIXELS_PER_METER
        block = self.world.create_static_body(position=(175.0 / ppm, 150.0 / ppm))
        block.create_shape(b2d.shape_def(material=b2d.surface_material(friction=0.0)), b2d.box(20.0 / ppm, 10.0 / ppm))

        ball = self.world.create_dynamic_body(position=(200.0 / ppm, 275.0 / ppm), gravity_scale=0.0)
        ball.create_shape(
            b2d.shape_def(material=b2d.surface_material(friction=0.0)),
            b2d.box(4.0 / ppm, 4.0 / ppm, radius=0.9 / ppm),
        )
        ball.linear_velocity = (0, -5)
        ball.motion_locks = b2d.MotionLocks(angular_z=True)


@register_sample("Continuous", "Restitution Threshold")
class RestitutionThreshold(Box2dSample):
    """A slow ball bouncing off a slope: with the default restitution threshold it would not bounce."""

    camera_center = (7.0, 5.0)
    camera_zoom = 6.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ppm = PIXELS_PER_METER
        self.world.restitution_threshold = 0.1

        block = self.world.create_static_body(
            position=(205.0 / ppm, 120.0 / ppm), rotation=70.0 * 3.14 / 180.0
        )
        block.create_shape(b2d.shape_def(material=b2d.surface_material(friction=0.0)), b2d.box(50.0 / ppm, 5.0 / ppm))

        ball = self.world.create_dynamic_body(position=(200.0 / ppm, 250.0 / ppm))
        ball.create_shape(
            b2d.shape_def(material=b2d.surface_material(friction=0.0, restitution=1.0)),
            b2d.circle(radius=5.0 / ppm),
        )
        ball.linear_velocity = (0, -2.9)
        ball.motion_locks = b2d.MotionLocks(angular_z=True)


@register_sample("Continuous", "Drop")
class Drop(Box2dSample):
    """Fast objects dropped with and without continuous collision.

    Keys: 1-4 select the scene (ball, ruler, ragdoll, bullet into a stack),
    c toggles continuous collision, s toggles slow motion.
    """

    camera_center = (0.0, 1.5)
    camera_zoom = 3.0

    COUNT = 40
    WIDTH = 0.25

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.world.sleeping_enabled = False
        self.debug_draw.draw_joints = False

        self.ground = None
        self.bodies = []
        self.human = None
        self.frame_skip = 0
        self.frame_count = 0
        self.continuous = True

        self.scene1()

    def clear(self):
        _destroy(*self.bodies)
        self.bodies = []
        if self.human is not None:
            destroy_human(self.human)
            self.human = None

    def create_ground(self, *shapes):
        _destroy(self.ground)
        self.ground = self.world.create_static_body()
        self.ground.create_shapes(b2d.shape_def(), shapes)

    def flat_ground(self):
        half = 0.5 * self.COUNT * self.WIDTH
        return b2d.segment((-half, 0), (half, 0))

    def tiled_ground(self):
        x0 = -0.5 * self.COUNT * self.WIDTH
        return [b2d.box(0.5 * self.WIDTH, 0.05, center=(x0 + j * self.WIDTH, 0)) for j in range(self.COUNT + 1)]

    def scene1(self):
        """ball"""
        self.clear()
        self.create_ground(*self.tiled_ground())
        body = self.world.create_dynamic_body(position=(0, 4), linear_velocity=(0, -100))
        body.create_shape(b2d.shape_def(), b2d.circle(radius=0.125))
        self.bodies.append(body)
        self.frame_count = 1

    def scene2(self):
        """ruler"""
        self.clear()
        self.create_ground(self.flat_ground())
        body = self.world.create_dynamic_body(
            position=(0, 4), rotation=0.5 * math.pi, linear_velocity=(0, 0), angular_velocity=-0.5
        )
        body.create_shape(b2d.shape_def(), b2d.box(0.75, 0.01))
        self.bodies.append(body)
        self.frame_count = 1

    def scene3(self):
        """ragdoll"""
        self.clear()
        self.create_ground(*self.tiled_ground())
        self.human = create_human(self.world, (0, 40), 1.0, 0.03, 1.0, 0.5)
        self.frame_count = 1

    def scene4(self):
        """bullet into a stack"""
        self.clear()
        self.create_ground(self.flat_ground(), b2d.segment((3, 0), (3, 8)))

        a = 0.25
        offset = 0.01
        for i in range(5):
            shift = -offset if i % 2 == 0 else offset
            body = self.world.create_dynamic_body(position=(2.5 + shift, a + 2.0 * a * i))
            body.create_shape(b2d.shape_def(), b2d.box(a, a))
            self.bodies.append(body)

        body = self.world.create_dynamic_body(position=(-7.7, 1.9), linear_velocity=(200, 0), is_bullet=True)
        body.create_shape(b2d.shape_def(density=4.0), b2d.circle(radius=0.125))
        self.bodies.append(body)
        self.frame_count = 1

    def on_key_down(self, event):
        scenes = {"1": self.scene1, "2": self.scene2, "3": self.scene3, "4": self.scene4}
        if event.key in scenes:
            scenes[event.key]()
        elif event.key == "c":
            self.clear()
            self.continuous = not self.continuous
        elif event.key == "s":
            self.frame_skip = 0 if self.frame_skip > 0 else 60

    def pre_update(self, dt):
        self.world.continuous_enabled = self.continuous

    def update(self, dt):
        # in slow motion only every frame_skip-th frame advances time
        stepping = self.frame_skip == 0 or self.frame_count % self.frame_skip == 0
        super().update(dt if stepping else 0.0)
        self.frame_count += 1


@register_sample("Continuous", "Pinball")
class Pinball(Box2dSample):
    """A fast bullet ball using continuous collision against static and dynamic bodies. Press A for the flippers."""

    camera_center = (0.0, 9.0)
    camera_zoom = 25.0 * 0.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        self.debug_draw.draw_joints = False

        ground = world.create_static_body()
        ground.create_chain(b2d.chain_def([(-8, 6), (-8, 20), (8, 20), (8, 6), (0, -2)], is_loop=True))

        # flippers
        self.flipper_joints = []
        for pivot, lower, upper in (((-2, 0), -30.0, 5.0), ((2, 0), -5.0, 30.0)):
            flipper = world.create_dynamic_body(position=pivot, enable_sleep=False)
            flipper.create_shape(b2d.shape_def(), b2d.box(1.75, 0.2))
            joint = world.create_revolute_joint(
                body_a=ground,
                body_b=flipper,
                local_anchor_a=pivot,
                local_anchor_b=(0, 0),
                enable_motor=True,
                max_motor_torque=1000.0,
                enable_limit=True,
                motor_speed=0.0,
                lower_angle=math.radians(lower),
                upper_angle=math.radians(upper),
            )
            self.flipper_joints.append(joint)

        # spinners
        for position in ((-4, 17), (4, 8)):
            spinner = world.create_dynamic_body(position=position)
            spinner.create_shapes(b2d.shape_def(), [b2d.box(1.5, 0.125), b2d.box(0.125, 1.5)])
            world.create_revolute_joint(
                body_a=ground,
                body_b=spinner,
                local_anchor_a=position,
                local_anchor_b=(0, 0),
                enable_motor=True,
                max_motor_torque=0.1,
            )

        # bumpers
        bumper_def = b2d.shape_def(material=b2d.surface_material(restitution=1.5))
        for position in ((-4, 8), (4, 17)):
            bumper = world.create_static_body(position=position)
            bumper.create_shape(bumper_def, b2d.circle(radius=1.0))

        # ball
        self.ball = world.create_dynamic_body(position=(1, 15), is_bullet=True)
        self.ball.create_shape(b2d.shape_def(), b2d.circle(radius=0.2))

    def post_update(self, dt):
        left, right = self.flipper_joints
        if self.is_key_pressed("a"):
            left.target_motor_speed, right.target_motor_speed = 20.0, -20.0
        else:
            left.target_motor_speed, right.target_motor_speed = -10.0, 10.0


@register_sample("Continuous", "Wedge")
class Wedge(Box2dSample):
    """The importance of secondary collisions in continuous physics, and an acute angle that is hard for the solver."""

    camera_center = (0.0, 5.5)
    camera_zoom = 6.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        ground.create_shape(b2d.shape_def(), b2d.segment((-4, 8), (0, 0)))
        ground.create_shape(b2d.shape_def(), b2d.segment((0, 0), (0, 8)))

        body = self.world.create_dynamic_body(position=(-0.45, 10.75), linear_velocity=(0, -200))
        body.create_shape(b2d.shape_def(material=b2d.surface_material(friction=0.2)), b2d.circle(radius=0.3))


@register_sample("Continuous", "Safety Factor")
class SafetyFactor(Box2dSample):
    """A larger CCD safety factor engages continuous collision at lower speeds, avoiding the slight overlap of
    discrete collision. The red line shows the deepest overlap."""

    camera_center = (0.0, 3.0)
    camera_zoom = 6.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body(position=(0, -1))
        ground.create_shape(b2d.shape_def(), b2d.box(20.0, 1.0))

        self.body = None
        self.extent = 0.5
        self.height = 0.3
        self.safety_factor = 0.1
        self.overlap = 0.0
        self.launch()

        self.frontend.add_widget(attr_slider(self, "Height", "height", 0.0, 2.0, 0.01, on_change=self.launch))
        self.frontend.add_widget(attr_slider(self, "Safety", "safety_factor", 0.0, 1.0, 0.01, on_change=self.launch))
        self.frontend.add_widget(widgets.Button(label="Drop", callback=self.launch))

    def launch(self):
        _destroy(self.body)
        self.body = self.world.create_dynamic_body(
            position=(0, self.height + self.extent), safety_factor=self.safety_factor
        )
        self.body.create_shape(b2d.shape_def(), b2d.box(self.extent, self.extent))
        self.overlap = 0.0

    def post_update(self, dt):
        # contacts are computed at the beginning of the step, so the manifold holds the initial separation
        contacts = self.body.contact_data
        if contacts:
            for point in contacts[0].manifold.points:
                self.overlap = max(self.overlap, -point.separation)

    def post_debug_draw(self):
        self.debug_draw.draw_segment((-3, -self.overlap), (3, -self.overlap), b2d.HexColor.Red.value)
