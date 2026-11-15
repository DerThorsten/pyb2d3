"""Ports of box2d's samples/sample_restitution.cpp."""

import math

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample, widgets

from ._common import Box2dSample
from ._shapes_helpers import WHITE, EnergyMeter, compute_energy, draw_text_lines

RED = b2d.HexColor.Red.value
GREEN = b2d.HexColor.Green.value
YELLOW = b2d.HexColor.Yellow.value


def restitution_slider(value, callback, step=0.01):
    return widgets.FloatSlider(
        label="Restitution", min_value=0.0, max_value=1.0, step=step, value=value, callback=callback
    )


def create_ground_box(world, friction=0.0, restitution=0.0):
    """A static box with its top at y = 0."""
    ground = world.create_static_body(position=(0.0, -1.0))
    material = b2d.surface_material(friction=friction, restitution=restitution)
    ground.create_shape(b2d.shape_def(material=material), b2d.box(40.0, 1.0))
    return ground


def destroy_bodies(bodies):
    for body in bodies:
        body.destroy()
    bodies.clear()


@register_sample("Restitution", "Varying")
class Varying(Box2dSample):
    """Restitution is approximate since Box2D uses speculative collision."""

    camera_center = (4.0, 17.0)
    camera_zoom = 27.5

    count = 40

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        h = 1.0 * self.count
        self.create_ground_segment(-h, h)

        self.shape_type = "Circle"
        self.bodies = []
        self.create_bodies()

        self.frontend.add_widget(
            widgets.Dropdown(label="Shape", options=["Circle", "Box"], value="Circle", callback=self.set_shape_type)
        )
        self.frontend.add_widget(widgets.Button(label="Reset", callback=self.create_bodies))

    def create_bodies(self):
        destroy_bodies(self.bodies)
        geometry = b2d.circle(radius=0.5) if self.shape_type == "Circle" else b2d.box(0.5, 0.5)
        dr = 1.0 / (self.count - 1 if self.count > 1 else 1)
        for i in range(self.count):
            restitution = i * dr
            x = -1.0 * (self.count - 1) + 2.0 * i
            body = self.world.create_dynamic_body(position=(x, 40.0), name=f"{restitution:.2f}")
            material = b2d.surface_material(restitution=restitution, friction=0.0)
            body.create_shape(b2d.shape_def(density=1.0, material=material), geometry)
            self.bodies.append(body)

    def set_shape_type(self, shape_type):
        self.shape_type = shape_type
        self.create_bodies()

    def post_debug_draw(self):
        h = 1.0 * self.count
        self.debug_draw.draw_segment((-h, 40.5), (h, 40.5), RED)


class SingleBounce(Box2dSample):
    """A single body with full restitution bouncing on the ground."""

    camera_center = (0.0, 5.0)
    camera_zoom = 8.0

    height = 5.0
    geometry = None

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment(-4.0, 4.0)

        self.max_y = self.height
        self.body = self.world.create_dynamic_body(position=(0.0, self.height), safety_factor=0.01)
        material = b2d.surface_material(restitution=1.0, friction=0.0)
        self.body.create_shape(b2d.shape_def(density=1.0, material=material, enable_hit_events=True), self.geometry)
        self.energy = EnergyMeter(self.world, [self.body])

    def post_update(self, dt):
        y = self.body.position.y
        if self.world.get_contact_events().hit_count == 1:
            self.max_y = y
        else:
            self.max_y = max(self.max_y, y)
        self.energy.update()

    def post_debug_draw(self):
        self.debug_draw.draw_segment((-4.0, self.height + 0.5), (4.0, self.height + 0.5), RED)
        draw_text_lines(self, [f"maxY = {self.max_y:.2f}"] + self.energy.lines())


@register_sample("Restitution", "Single Box Restitution")
class SingleBoxRestitution(SingleBounce):
    """Tests how a single bouncing box behaves."""

    height = 5.0
    geometry = b2d.box(0.5, 0.5)


@register_sample("Restitution", "Single Circle Restitution")
class SingleCircleRestitution(SingleBounce):
    """Tests how a single bouncing circle behaves."""

    height = 10.0
    geometry = b2d.circle(radius=0.5)


class ReboundSample(Box2dSample):
    """Measures the restitution coefficient of an impactor at its first rebound."""

    impact_speed = 5.0

    def reset_rebound(self):
        self.coefficient = 0.0
        self.latched = False
        self.hit = False

    def update_rebound(self, vy):
        if self.world.get_contact_events().hit_count > 0:
            self.hit = True
        # the rebound only means something once the impact has happened and the impactor is leaving
        if not self.latched and self.hit and vy > 0.0:
            self.coefficient = vy / self.impact_speed
            self.latched = True

    def rebound_lines(self, vy):
        lines = [f"coefficient = {vy / self.impact_speed:.4f} live (target {self.restitution:.2f})"]
        if self.latched:
            lines.append(f"coefficient = {self.coefficient:.4f} at first rebound")
        return lines


@register_sample("Restitution", "Circle Stack Restitution")
class CircleStackRestitution(ReboundSample):
    """A ball hitting a stack of resting balls. Similar to the MeasureSupportedBounce unit test."""

    camera_center = (0.0, 2.5)
    camera_zoom = 6.0

    max_stack_count = 3

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        create_ground_box(self.world)

        self.stack_count = 2
        self.restitution = 1.0
        self.gravity = False
        self.bodies = []
        self.create_scene()

        self.frontend.add_widget(restitution_slider(self.restitution, self.set_restitution))
        self.frontend.add_widget(
            widgets.IntSlider(
                label="Stack",
                min_value=0,
                max_value=self.max_stack_count,
                step=1,
                value=self.stack_count,
                callback=self.set_stack_count,
            )
        )
        self.frontend.add_widget(widgets.Checkbox(label="Gravity", value=self.gravity, callback=self.set_gravity))
        self.frontend.add_widget(widgets.Button(label="Reset", callback=self.create_scene))

    def create_ball(self, y, velocity_y, restitution, hit_events):
        body = self.world.create_dynamic_body(position=(0.0, y), linear_velocity=(0.0, velocity_y), enable_sleep=False)
        material = b2d.surface_material(friction=0.0, restitution=restitution)
        body.create_shape(b2d.shape_def(material=material, enable_hit_events=hit_events), b2d.circle(radius=0.5))
        self.bodies.append(body)
        return body

    def create_scene(self):
        destroy_bodies(self.bodies)
        self.world.gravity = (0.0, -10.0) if self.gravity else (0.0, 0.0)

        for i in range(self.stack_count):
            self.create_ball(0.5 + 1.0 * i, 0.0, 0.0, False)

        # start half a step of travel above contact so the impact lands mid step, matching the test
        self.start_height = 0.5 + 1.0 * self.stack_count + 0.5 * self.impact_speed * (1.0 / 60.0)
        self.impactor = self.create_ball(self.start_height, -self.impact_speed, self.restitution, True)

        self.energy = EnergyMeter(self.world, self.bodies)
        self.reset_rebound()
        self.vy = 0.0
        self.support_speed = 0.0

    def set_restitution(self, restitution):
        self.restitution = restitution
        self.create_scene()

    def set_stack_count(self, count):
        self.stack_count = int(count)
        self.create_scene()

    def set_gravity(self, flag):
        self.gravity = flag
        self.create_scene()

    def post_update(self, dt):
        self.vy = self.impactor.linear_velocity.y
        self.update_rebound(self.vy)
        self.support_speed = max((body.speed for body in self.bodies[: self.stack_count]), default=0.0)
        self.energy.update()

    def post_debug_draw(self):
        self.debug_draw.draw_segment((-2.0, self.start_height), (2.0, self.start_height), RED)
        draw_text_lines(
            self,
            [f"impactor vy = {self.vy:.3f} m/s"]
            + self.rebound_lines(self.vy)
            + [f"support speed = {self.support_speed:.4f} m/s"]
            + self.energy.lines(),
        )


@register_sample("Restitution", "Restitution Propagation")
class RestitutionPropagation(Box2dSample):
    """A bouncy ball landing on a resting body.

    Three balls fall together from the same height onto bare ground, one crate and two crates. Without
    restitution propagation the restitution stage only visits the ball's own contact, so the rebound is
    shared with the crate, which is driven into the ground and pushed back the next step. With propagation
    the ground contact under the crate can react in the restitution solver.
    """

    camera_center = (0.0, 4.0)
    camera_zoom = 10.0

    column_count = 3
    drop_height = 5.0
    labels = ("ground", "one crate", "two crates")

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        create_ground_box(self.world, friction=0.6)

        self.restitution = 0.9
        self.bodies = []
        self.create_scene()

        self.frontend.add_widget(restitution_slider(self.restitution, self.set_restitution))
        self.frontend.add_widget(widgets.Button(label="Reset", callback=self.create_scene))

    def create_scene(self):
        destroy_bodies(self.bodies)
        self.crates = []
        self.balls = []
        self.kick = 0.0
        n = self.column_count
        self.rest_height = [0.5 + 1.0 * column for column in range(n)]
        self.apex = [0.0] * n
        self.rebounding = [False] * n
        self.done = [False] * n

        for column in range(n):
            x = self.column_x(column)
            for k in range(column):
                crate = self.world.create_dynamic_body(position=(x, 0.5 + 1.0 * k), enable_sleep=False)
                crate.create_shape(b2d.shape_def(), b2d.box(0.5, 0.5))
                self.crates.append(crate)

            ball = self.world.create_dynamic_body(
                position=(x, self.rest_height[column] + self.drop_height), enable_sleep=False
            )
            material = b2d.surface_material(restitution=self.restitution)
            ball.create_shape(b2d.shape_def(material=material), b2d.circle(radius=0.5))
            self.balls.append(ball)
        self.bodies += self.crates + self.balls

    @staticmethod
    def column_x(column):
        return 4.0 * (column - 1)

    def set_restitution(self, restitution):
        self.restitution = restitution
        self.create_scene()

    def post_update(self, dt):
        for column, ball in enumerate(self.balls):
            vy = ball.linear_velocity.y
            height = ball.position.y - self.rest_height[column]

            # the first rebound apex: the ball starts at rest and falls, so upward velocity means it bounced
            if not self.rebounding[column] and vy > 0.0:
                self.rebounding[column] = True

            if self.rebounding[column] and not self.done[column]:
                self.apex[column] = max(self.apex[column], height)
                if vy < 0.0:
                    self.done[column] = True

        self.kick = max([self.kick] + [crate.speed for crate in self.crates])

    def post_debug_draw(self):
        lines = []
        for column, label in enumerate(self.labels):
            x = self.column_x(column)
            rest = self.rest_height[column]
            apex = self.apex[column]
            self.debug_draw.draw_segment((x - 1.0, rest + self.drop_height), (x + 1.0, rest + self.drop_height), RED)
            if apex > 0.0:
                self.debug_draw.draw_segment((x - 1.0, rest + apex), (x + 1.0, rest + apex), GREEN)
            lines.append(f"{label}: apex {apex:.2f} m ({100.0 * apex / self.drop_height:.0f}% of drop)")
        lines.append(f"peak crate speed {self.kick:.2f} m/s")
        draw_text_lines(self, lines)


@register_sample("Restitution", "Box Restitution")
class BoxRestitution(ReboundSample):
    """A flat box hitting the ground, optionally spinning. Similar to the MeasureFlatBounce and SpinTest unit tests."""

    camera_center = (0.0, 8.0)
    camera_zoom = 10.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        # gravity would bias the measured coefficient
        self.world.gravity = (0.0, 0.0)
        create_ground_box(self.world)

        self.restitution = 0.9
        self.spin = 0.0
        self.box = None
        self.create_scene()

        self.frontend.add_widget(restitution_slider(self.restitution, self.set_restitution))
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Spin", min_value=0.0, max_value=2.0, step=0.01, value=self.spin, callback=self.set_spin
            )
        )
        self.frontend.add_widget(widgets.Button(label="Reset", callback=self.create_scene))

    def create_scene(self):
        if self.box is not None:
            self.box.destroy()
        self.box = self.world.create_dynamic_body(
            position=(0.0, 0.25 + 0.5 * self.impact_speed * (1.0 / 60.0)),
            linear_velocity=(0.0, -self.impact_speed),
            angular_velocity=self.spin,
            enable_sleep=False,
        )
        material = b2d.surface_material(friction=0.0, restitution=self.restitution)
        self.box.create_shape(
            b2d.shape_def(density=1.0, material=material, enable_hit_events=True), b2d.box(1.0, 0.25)
        )
        self.energy = EnergyMeter(self.world, [self.box])
        self.reset_rebound()
        self.vy = 0.0

    def set_restitution(self, restitution):
        self.restitution = restitution
        self.create_scene()

    def set_spin(self, spin):
        self.spin = spin
        self.create_scene()

    def post_update(self, dt):
        self.vy = self.box.linear_velocity.y
        self.update_rebound(self.vy)
        self.energy.update()

    def post_debug_draw(self):
        for corner in ((-1.0, -0.25), (1.0, -0.25)):
            self.debug_draw.draw_point(self.box.world_point(corner), 8.0, YELLOW)
        w = self.box.angular_velocity
        draw_text_lines(
            self,
            [f"vy = {self.vy:.3f} m/s"]
            + self.rebound_lines(self.vy)
            + [f"spin in = {self.spin:.2f}, spin out = {w:.4f} (ideal {-self.spin:.2f} at e = 1)"]
            + self.energy.lines(),
        )


@register_sample("Restitution", "Rotated Box Restitution")
class RotatedBoxRestitution(Box2dSample):
    """Boxes dropped at different angles: how much energy survives the bounce."""

    camera_center = (0.0, 4.0)
    camera_zoom = 14.0

    count = 12
    drop_height = 10.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        h = 2.0 * self.count + 1.0
        self.create_ground_segment(-h, h)

        self.restitution = 0.9
        self.friction = 0.0
        self.safety_factor = 0.5
        self.bodies = []
        self.create_scene()

        for label, attr, lo, hi, step in (
            ("Restitution", "restitution", 0.0, 1.0, 0.1),
            ("Friction", "friction", 0.0, 1.0, 0.1),
            ("Safety Factor", "safety_factor", 0.01, 0.5, 0.01),
        ):
            self.frontend.add_widget(
                widgets.FloatSlider(
                    label=label,
                    min_value=lo,
                    max_value=hi,
                    step=step,
                    value=getattr(self, attr),
                    callback=lambda value, attr=attr: self.set_parameter(attr, value),
                )
            )
        self.frontend.add_widget(widgets.Button(label="Reset", callback=self.create_scene))

    def set_parameter(self, attr, value):
        setattr(self, attr, value)
        self.create_scene()

    def body_x(self, i):
        return -1.0 * (self.count - 1) + 2.0 * i

    def create_scene(self):
        destroy_bodies(self.bodies)
        material = b2d.surface_material(friction=self.friction, restitution=self.restitution)
        # boxes in a negative group never collide with each other
        shape_def = b2d.shape_def(material=material, filter=b2d.make_filter(group_index=-1))

        # a square repeats every quarter turn
        dq = 0.5 * math.pi / self.count
        for i in range(self.count):
            body = self.world.create_dynamic_body(
                position=(self.body_x(i), self.drop_height),
                rotation=b2d.make_rot(i * dq),
                safety_factor=self.safety_factor,
            )
            body.create_shape(shape_def, b2d.box(0.5, 0.5))
            self.bodies.append(body)
        self.start_energy = [sum(compute_energy(self.world, [body])) for body in self.bodies]

    def post_debug_draw(self):
        h = 1.0 * self.count
        self.debug_draw.draw_segment((-h, self.drop_height + 0.5), (h, self.drop_height + 0.5), RED)

        percents = []
        for i, (body, start) in enumerate(zip(self.bodies, self.start_energy)):
            total = sum(compute_energy(self.world, [body]))
            percent = 100.0 * total / start if start != 0.0 else 0.0
            percents.append(percent)
            self.debug_draw.draw_string((self.body_x(i) - 0.5, self.drop_height + 1.5), f"{percent:.1f}%", WHITE)
        draw_text_lines(self, [f"energy: min {min(percents):.2f}%, max {max(percents):.2f}% of start"])


@register_sample("Restitution", "Two Box Restitution")
class TwoBoxRestitution(Box2dSample):
    """A bouncy box falling onto a resting one. Based on https://github.com/erincatto/box2d/discussions/957"""

    camera_center = (0.0, 3.0)
    camera_zoom = 5.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment(-10.0, 10.0)

        shape_def = b2d.shape_def(material=b2d.surface_material(restitution=0.9))
        bodies = []
        for position in ((0.0, 0.5), (0.1, 6.0)):
            body = self.world.create_dynamic_body(position=position)
            body.create_shape(shape_def, b2d.make_square(0.5))
            bodies.append(body)
        self.energy = EnergyMeter(self.world, bodies)

    def post_update(self, dt):
        self.energy.update()

    def post_debug_draw(self):
        draw_text_lines(self, self.energy.lines())


@register_sample("Restitution", "Circle Restitution")
class CircleRestitution(Box2dSample):
    """Two rows of circles with increasing restitution."""

    camera_center = (0.0, 5.0)
    camera_zoom = 10.0

    count = 10

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        h = 2.0 * self.count
        self.create_ground_segment(-h, h)

        dr = 1.0 / (self.count - 1 if self.count > 1 else 1)
        for i in range(self.count):
            restitution = i * dr
            shape_def = b2d.shape_def(density=1.0, material=b2d.surface_material(restitution=restitution))
            x = -1.0 * (self.count - 1) + 2.0 * i
            for y in (1.0, 4.0):
                body = self.world.create_dynamic_body(position=(x, y), name=f"{restitution:.2f}")
                body.create_shape(shape_def, b2d.circle(radius=0.5))
