"""Ports of box2d's samples/sample_robustness.cpp."""

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample, widgets

from ._common import Box2dSample
from ._continuous_helpers import attr_slider


def _create_ground_box(world):
    ground = world.create_static_body()
    ground.create_shape(b2d.shape_def(), b2d.box(50.0, 1.0, center=(0, -1)))


def _create_two_small_one_big(world, small_shape, big_y, extent=1.0):
    """Two small shapes carrying a big heavy box."""
    for x in (-9.0 * extent, 9.0 * extent):
        body = world.create_dynamic_body(position=(x, 0.5 * extent))
        body.create_shape(b2d.shape_def(), small_shape)
    body = world.create_dynamic_body(position=(0, big_y))
    body.create_shape(b2d.shape_def(), b2d.box(10.0 * extent, 10.0 * extent))


@register_sample("Robustness", "HighMassRatio1")
class HighMassRatio1(Box2dSample):
    """Pyramids with a heavy box on top."""

    camera_center = (3.0, 14.0)
    camera_zoom = 25.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        extent = 1.0
        _create_ground_box(self.world)

        box = b2d.box(extent, extent)
        for j in range(3):
            count = 10
            offset = -20.0 * extent + 2.0 * (count + 1.0) * extent * j
            y = extent
            while count > 0:
                for i in range(count):
                    coeff = i - 0.5 * count
                    yy = y + 2.0 if count == 1 else y
                    body = self.world.create_dynamic_body(position=(2.0 * coeff * extent + offset, yy))
                    density = (j + 1.0) * 100.0 if count == 1 else 1.0
                    body.create_shape(b2d.shape_def(density=density), box)
                count -= 1
                y += 2.0 * extent


@register_sample("Robustness", "HighMassRatio2")
class HighMassRatio2(Box2dSample):
    """Big box on small boxes."""

    camera_center = (0.0, 16.5)
    camera_zoom = 25.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        _create_ground_box(self.world)
        _create_two_small_one_big(self.world, b2d.box(0.5, 0.5), big_y=10.0 + 16.0)


@register_sample("Robustness", "HighMassRatio3")
class HighMassRatio3(Box2dSample):
    """Big box on small triangles."""

    camera_center = (0.0, 16.5)
    camera_zoom = 25.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        _create_ground_box(self.world)
        triangle = b2d.polygon([(-0.5, 0.0), (0.5, 0.0), (0.0, 1.0)])
        _create_two_small_one_big(self.world, triangle, big_y=10.0 + 4.0)


@register_sample("Robustness", "Overlap Recovery")
class OverlapRecovery(Box2dSample):
    """A pyramid of overlapping boxes pushing itself apart, tuned by the contact softness."""

    camera_center = (0.0, 2.5)
    camera_zoom = 3.75

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.bodies = []
        self.base_count = 4
        self.overlap = 0.25
        self.extent = 0.5
        self.speed = 3.0
        self.hertz = 30.0
        self.damping_ratio = 10.0

        self.create_ground_segment(-40.0, 40.0)
        self.create_scene()

        add = self.frontend.add_widget
        add(attr_slider(self, "Extent", "extent", 0.1, 1.0, 0.1, on_change=self.create_scene))
        add(attr_slider(self, "Base Count", "base_count", 1, 10, 1, on_change=self.create_scene, cls=widgets.IntSlider))
        add(attr_slider(self, "Overlap", "overlap", 0.0, 1.0, 0.01, on_change=self.create_scene))
        add(attr_slider(self, "Speed", "speed", 0.0, 10.0, 0.1, on_change=self.create_scene))
        add(attr_slider(self, "Hertz", "hertz", 0.0, 240.0, 1.0, on_change=self.create_scene))
        add(attr_slider(self, "Damping Ratio", "damping_ratio", 0.0, 20.0, 0.1, on_change=self.create_scene))
        add(widgets.Button(label="Reset Scene", callback=self.create_scene))

    def create_scene(self):
        for body in self.bodies:
            body.destroy()
        self.bodies = []

        self.world.set_contact_tuning(self.hertz, self.damping_ratio, self.speed)

        box = b2d.box(self.extent, self.extent)
        shape_def = b2d.shape_def(density=1.0)
        fraction = 1.0 - self.overlap
        y = self.extent
        for i in range(self.base_count):
            x = fraction * self.extent * (i - self.base_count)
            for _ in range(i, self.base_count):
                body = self.world.create_dynamic_body(position=(x, y))
                body.create_shape(shape_def, box)
                self.bodies.append(body)
                x += 2.0 * fraction * self.extent
            y += 2.0 * fraction * self.extent


@register_sample("Robustness", "Tiny Pyramid")
class TinyPyramid(Box2dSample):
    """A pyramid of 5cm squares: tiny objects are hard to stack since the AABB margin and linear slop are close to
    the shape size."""

    camera_center = (0.0, 0.8)
    camera_zoom = 1.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        ground.create_shape(b2d.shape_def(), b2d.box(5.0, 1.0, center=(0, -1)))

        extent = 0.025
        base_count = 30
        box = b2d.box(extent, extent)
        for i in range(base_count):
            y = (2.0 * i + 1.0) * extent
            for j in range(i, base_count):
                x = (i + 1.0) * extent + 2.0 * (j - i) * extent - base_count * extent
                body = self.world.create_dynamic_body(position=(x, y))
                body.create_shape(b2d.shape_def(), box)


@register_sample("Robustness", "Cart")
class Cart(Box2dSample):
    """High gravity and a high mass ratio: tuning contact and joint stiffness at a high sub-step count."""

    camera_center = (0.0, 1.0)
    camera_zoom = 1.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.frontend.settings.substeps = 12

        ground = self.world.create_static_body(position=(0, -1))
        ground.create_shape(b2d.shape_def(), b2d.box(20.0, 1.0))

        self.world.gravity = (0, -22.0)

        self.contact_hertz = 240.0
        self.contact_damping_ratio = 10.0
        self.contact_speed = 0.5
        self.constraint_hertz = 240.0
        self.constraint_damping_ratio = 0.0
        self.bodies = []

        self.apply_contact_tuning()
        self.create_scene()

        add = self.frontend.add_widget
        on_contact = self.on_contact_changed
        add(attr_slider(self, "Contact Hertz", "contact_hertz", 0.0, 240.0, 1.0, on_change=on_contact))
        add(attr_slider(self, "Contact Damping Ratio", "contact_damping_ratio", 0.0, 100.0, 1.0, on_change=on_contact))
        add(attr_slider(self, "Contact Speed", "contact_speed", 0.0, 5.0, 0.1, on_change=on_contact))
        add(attr_slider(self, "Joint Hertz", "constraint_hertz", 0.0, 240.0, 1.0, on_change=self.create_scene))
        add(
            attr_slider(
                self, "Joint Damping Ratio", "constraint_damping_ratio", 0.0, 20.0, 1.0, on_change=self.create_scene
            )
        )
        add(widgets.Button(label="Reset Scene", callback=self.create_scene))

    def apply_contact_tuning(self):
        self.world.set_contact_tuning(self.contact_hertz, self.contact_damping_ratio, self.contact_speed)

    def on_contact_changed(self):
        self.apply_contact_tuning()
        self.create_scene()

    def create_scene(self):
        for body in self.bodies:
            body.destroy()

        y_base = 2.0
        chassis = self.world.create_dynamic_body(position=(0, y_base))
        chassis.create_shape(b2d.shape_def(density=1000.0), b2d.box(1.0, 0.25, center=(0, 0.25)))
        self.bodies = [chassis]

        wheel_def = b2d.shape_def(density=50.0, material=b2d.surface_material(rolling_resistance=0.02))
        for x in (-0.9, 0.9):
            wheel = self.world.create_dynamic_body(position=(x, y_base - 0.15))
            wheel.create_shape(wheel_def, b2d.circle(radius=0.1))
            self.bodies.append(wheel)

            joint = self.world.create_revolute_joint(
                body_a=chassis,
                body_b=wheel,
                local_anchor_a=(x, -0.15),
                local_anchor_b=(0, 0),
                constraint_hertz=120.0,
                constraint_damping_ratio=0.0,
            )
            joint.set_constraint_tuning(self.constraint_hertz, self.constraint_damping_ratio)


@register_sample("Robustness", "Multiple Prismatic")
class MultiplePrismatic(Box2dSample):
    """A chain of prismatic joints that must stay stable when highly distorted."""

    camera_center = (0.0, 8.0)
    camera_zoom = 25.0 * 0.5

    COUNT = 6

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()

        joint_def = b2d.prismatic_joint_def(
            body_a=ground,
            local_anchor_a=(0, 0),
            local_anchor_b=(0, -0.6),
            draw_scale=1.0,
            lower_translation=-6.0,
            upper_translation=6.0,
            enable_limit=True,
        )
        self.hertz = joint_def.constraint_hertz
        self.damping_ratio = joint_def.constraint_damping_ratio

        self.joints = []
        for i in range(self.COUNT):
            body = self.world.create_dynamic_body(position=(0, 0.6 + 1.2 * i))
            body.create_shape(b2d.shape_def(), b2d.box(0.5, 0.5))

            joint_def.body_b = body
            self.joints.append(self.world.create_prismatic_joint(joint_def))

            joint_def.body_a = body
            joint_def.local_anchor_a = (0, 0.6)

        # increase the mouse force
        self.mouse_joint_force_multiplier = 100000.0

        add = self.frontend.add_widget
        add(attr_slider(self, "Hertz", "hertz", 0.0, 480.0, 1.0, on_change=self.apply_tuning))
        add(attr_slider(self, "Damping Ratio", "damping_ratio", 0.0, 100.0, 1.0, on_change=self.apply_tuning))

    def apply_tuning(self):
        for joint in self.joints:
            joint.set_constraint_tuning(self.hertz, self.damping_ratio)
