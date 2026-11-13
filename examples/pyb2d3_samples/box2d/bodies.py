"""Ports of box2d's samples/sample_bodies.cpp."""

import math

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample, widgets

from ._common import Box2dSample


@register_sample("Bodies", "Body Type")
class BodyType(Box2dSample):
    camera_center = (0.8, 6.4)
    camera_zoom = 25.0 * 0.4

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        self.type = b2d.BodyType.STATIC
        self.speed = 3.0

        ground = self.create_ground_segment()

        # attachment
        self.attachment = world.create_dynamic_body(position=(-2, 3), name="attach1")
        self.attachment.create_shape(b2d.shape_def(density=1), b2d.box(0.5, 2.0))

        # second attachment
        self.second_attachment = world.create_body(
            type=self.type, position=(3, 3), name="attach2"
        )
        self.second_attachment.create_shape(b2d.shape_def(density=1), b2d.box(0.5, 2.0))

        # platform
        self.platform = world.create_body(type=self.type, position=(-4, 5), name="platform")
        self.platform.create_shape(
            b2d.shape_def(density=2),
            b2d.box(0.5, 4.0, center=(4, 0), rotation=0.5 * math.pi),
        )

        for attachment, pivot in ((self.attachment, (-2, 5)), (self.second_attachment, (3, 5))):
            world.create_revolute_joint(
                body_a=attachment,
                body_b=self.platform,
                local_anchor_a=attachment.local_point(pivot),
                local_anchor_b=self.platform.local_point(pivot),
                max_motor_torque=50.0,
                enable_motor=True,
            )

        anchor = (0, 5)
        world.create_prismatic_joint(
            body_a=ground,
            body_b=self.platform,
            local_anchor_a=ground.local_point(anchor),
            local_anchor_b=self.platform.local_point(anchor),
            max_motor_force=1000.0,
            motor_speed=0.0,
            enable_motor=True,
            lower_translation=-10.0,
            upper_translation=10.0,
            enable_limit=True,
        )

        # payloads
        crate = world.create_dynamic_body(position=(-3, 8), name="crate1")
        crate.create_shape(b2d.shape_def(density=2), b2d.box(0.75, 0.75))

        self.second_payload = world.create_body(type=self.type, position=(2, 8), name="crate2")
        self.second_payload.create_shape(b2d.shape_def(density=2), b2d.box(0.75, 0.75))

        # separate bodies on the ground
        self.touching = world.create_body(type=self.type, position=(8, 0.2), name="debris")
        self.touching.create_shape(b2d.shape_def(density=2), b2d.capsule((0, 0), (1, 0), 0.25))

        debris = world.create_static_body(position=(8.5, 0.2), name="debris")
        debris.create_shape(b2d.shape_def(), b2d.capsule((0, 0), (1, 0), 0.5))

        # floating body
        self.floating = world.create_body(
            type=self.type, position=(-8, 12), gravity_scale=0.0, name="floater"
        )
        self.floating.create_shape(b2d.shape_def(density=2), b2d.circle(center=(0, 0.5), radius=0.25))

        self.frontend.add_widget(
            widgets.RadioButtons(
                label="Type",
                options=["Static", "Kinematic", "Dynamic"],
                value="Static",
                callback=self.set_type,
            )
        )
        self.frontend.add_widget(widgets.Checkbox(label="Enable", value=True, callback=self.set_enabled))

    @property
    def switched_bodies(self):
        return (
            self.platform,
            self.second_attachment,
            self.second_payload,
            self.touching,
            self.floating,
        )

    def set_type(self, name):
        self.type = getattr(b2d.BodyType, name.upper())
        for body in self.switched_bodies:
            body.type = self.type
        if self.type == b2d.BodyType.KINEMATIC:
            self.platform.linear_velocity = (-self.speed, 0)
            self.platform.angular_velocity = 0
            self.second_attachment.linear_velocity = (0, 0)
            self.second_attachment.angular_velocity = 0

    def set_enabled(self, enabled):
        for body in (self.attachment, self.second_payload, self.floating):
            body.enabled = enabled

    def pre_update(self, dt):
        # drive the kinematic platform back and forth
        if self.type == b2d.BodyType.KINEMATIC:
            p = self.platform.position
            v = self.platform.linear_velocity
            if (p.x < -14 and v.x < 0) or (p.x > 6 and v.x > 0):
                self.platform.linear_velocity = (-v.x, v.y)


@register_sample("Bodies", "Weeble")
class Weeble(Box2dSample):
    """A capsule with a lowered center of mass that rights itself; also tests friction and restitution callbacks."""

    camera_center = (2.3, 10.0)
    camera_zoom = 25.0 * 0.5

    explosion_position = (0.0, 0.0)
    explosion_radius = 2.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.explosion_magnitude = 8.0

        self.world.set_friction_callback(lambda friction_a, material_a, friction_b, material_b: 0.1)
        self.world.set_restitution_callback(lambda restitution_a, material_a, restitution_b, material_b: 1.0)

        self.create_ground_segment()

        self.weeble = self.world.create_dynamic_body(position=(0, 3), rotation=b2d.make_rot(0.25 * math.pi))
        self.weeble.create_shape(b2d.shape_def(), b2d.capsule((0, -1), (0, 1), 1.0))

        # lower the center of mass, see https://en.wikipedia.org/wiki/Parallel_axis_theorem
        offset = 1.5
        mass_data = self.weeble.mass_data
        mass_data.center = (0, -offset)
        mass_data.rotational_inertia = self.weeble.rotational_inertia + mass_data.mass * offset * offset
        self.weeble.mass_data = mass_data

        self.frontend.add_widget(widgets.Button(label="Teleport", callback=self.teleport))
        self.frontend.add_widget(widgets.Button(label="Explode", callback=self.explode))
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="Magnitude",
                min_value=-100.0,
                max_value=100.0,
                step=0.1,
                value=self.explosion_magnitude,
                callback=self.set_magnitude,
            )
        )

    def post_run(self):
        # the mixing callbacks are global in pyb2d3, don't leak them into the next sample
        self.world.set_friction_callback(None)
        self.world.set_restitution_callback(None)

    def teleport(self):
        self.weeble.set_transform((0, 5), b2d.make_rot(0.95 * math.pi))

    def explode(self):
        self.world.explode(
            position=self.explosion_position,
            radius=self.explosion_radius,
            falloff=0.1,
            impulse_per_length=self.explosion_magnitude,
        )

    def set_magnitude(self, value):
        self.explosion_magnitude = value

    def post_debug_draw(self):
        self.debug_draw.draw_circle(self.explosion_position, self.explosion_radius, b2d.HexColor.Azure.value)

        # the velocity of a point on a body, computed from a local and from a world point
        local_point = (0, 2)
        world_point = self.weeble.world_point(local_point)
        v1 = self.weeble.local_point_velocity(local_point)
        v2 = self.weeble.world_point_velocity(world_point)
        offset = b2d.Vec2(0.05, 0)
        self.debug_draw.draw_segment(world_point, world_point + v1, b2d.HexColor.Red.value)
        self.debug_draw.draw_segment(world_point + offset, world_point + v2 + offset, b2d.HexColor.Green.value)


@register_sample("Bodies", "Sleep")
class Sleep(Box2dSample):
    """Sleeping bodies with sensors, disabled sleep, a slow pendulum and waking by contact creation / destruction."""

    camera_center = (3.0, 50.0)
    camera_zoom = 25.0 * 2.2

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        self.ground_shape = ground.create_shape(
            b2d.shape_def(enable_sensor_events=True), b2d.segment((-40, 0), (40, 0))
        )

        # sleeping bodies with sensors
        self.sensors = []
        self.sensor_touching = {}
        for i in range(2):
            body = world.create_dynamic_body(position=(-4, 3 + 2 * i), is_awake=False, enable_sleep=True)
            body.create_shape(b2d.shape_def(), b2d.capsule((0, 1), (1, 1), 0.75))
            sensor = body.create_shape(
                b2d.shape_def(is_sensor=True, enable_sensor_events=True), b2d.capsule((0, 1), (1, 1), 1.0)
            )
            self.sensors.append((sensor, body))
            self.sensor_touching[sensor] = False

        # sleeping body but sleep is disabled
        body = world.create_dynamic_body(position=(0, 3), is_awake=False, enable_sleep=False)
        body.create_shape(b2d.shape_def(), b2d.circle(center=(1, 1), radius=1.0))

        # awake body and sleep is disabled
        body = world.create_dynamic_body(position=(5, 3), is_awake=True, enable_sleep=False)
        body.create_shape(b2d.shape_def(), b2d.box(1.0, 1.0, center=(0, 1), rotation=0.25 * math.pi))

        # sleeping bodies to test waking on contact creation (x=5) and destruction (x=-10)
        for x in (5.0, -10.0):
            body = world.create_dynamic_body(position=(x, 1), is_awake=False, enable_sleep=True)
            body.create_shape(b2d.shape_def(), b2d.box(1.0, 1.0))

        # a long pendulum
        pivot = (0, 100)
        self.pendulum = world.create_dynamic_body(position=pivot, angular_damping=0.5, sleep_threshold=0.05)
        self.pendulum.create_shape(b2d.shape_def(), b2d.capsule((0, 0), (90, 0), 0.25))
        world.create_revolute_joint(
            body_a=ground,
            body_b=self.pendulum,
            local_anchor_a=ground.local_point(pivot),
            local_anchor_b=self.pendulum.local_point(pivot),
        )

        self.static_body = None

        self.frontend.add_widget(
            widgets.FloatSlider(
                label="sleep velocity",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                value=self.pendulum.sleep_threshold,
                callback=self.set_sleep_velocity,
            )
        )
        self.frontend.add_widget(
            widgets.FloatSlider(
                label="angular damping",
                min_value=0.0,
                max_value=2.0,
                step=0.01,
                value=self.pendulum.angular_damping,
                callback=self.set_angular_damping,
            )
        )
        self.frontend.add_widget(widgets.Button(label="Create / Destroy", callback=self.toggle_invoker))

    def set_sleep_velocity(self, value):
        self.pendulum.sleep_threshold = value
        self.pendulum.awake = True

    def set_angular_damping(self, value):
        self.pendulum.angular_damping = value

    def toggle_invoker(self):
        if self.static_body is None:
            self.static_body = self.world.create_static_body(position=(-10.5, 3))
            self.static_body.create_shape(
                b2d.shape_def(invoke_contact_creation=True),
                b2d.box(2.0, 0.1, center=(0, 0), rotation=0.25 * math.pi),
            )
        else:
            self.static_body.destroy()
            self.static_body = None

    def post_update(self, dt):
        # detect sensors touching the ground
        events = self.world.get_sensor_events()
        for touching, sensor_events in ((True, events.begin_events()), (False, events.end_events())):
            for event in sensor_events:
                if event.visitor_shape == self.ground_shape and event.sensor_shape in self.sensor_touching:
                    self.sensor_touching[event.sensor_shape] = touching

    def post_debug_draw(self):
        for i, (sensor, body) in enumerate(self.sensors):
            self.debug_draw.draw_string(
                body.world_point((0, 1)),
                f"sensor touch {i} = {self.sensor_touching[sensor]}",
                b2d.HexColor.White.value,
            )


@register_sample("Bodies", "Bad")
class BadBody(Box2dSample):
    """A bad body is a dynamic body with no mass and behaves like a kinematic body (an invalid user setup)."""

    camera_center = (2.3, 10.0)
    camera_zoom = 25.0 * 0.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment()

        capsule = b2d.capsule((0, -1), (0, 1), 1.0)
        rotation = b2d.make_rot(0.25 * math.pi)

        self.bad_body = self.world.create_dynamic_body(position=(0, 3), angular_velocity=0.5, rotation=rotation)
        # density set to zero intentionally to create a bad body
        self.bad_body.create_shape(b2d.shape_def(density=0.0), capsule)

        body = self.world.create_dynamic_body(position=(2, 3), rotation=rotation)
        body.create_shape(b2d.shape_def(), capsule)

    def post_update(self, dt):
        # for science
        self.bad_body.apply_force_to_center((0, 10), True)


@register_sample("Bodies", "Pivot")
class Pivot(Box2dSample):
    """How to set the initial angular velocity to get a specific movement (the lower end stays at rest)."""

    camera_center = (0.8, 6.4)
    camera_zoom = 25.0 * 0.4

    lever = 3.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment()

        v = (5.0, 0.0)
        self.body = self.world.create_dynamic_body(position=(0, 3), gravity_scale=1.0, linear_velocity=v)
        r = (0.0, -self.lever)
        self.body.angular_velocity = b2d.cross(v, r) / b2d.dot(r, r)
        self.body.create_shape(b2d.shape_def(), b2d.box(0.1, self.lever))

    def post_debug_draw(self):
        r = self.body.world_vector((0, -self.lever))
        vp = self.body.linear_velocity + b2d.cross_sv(self.body.angular_velocity, r)
        self.debug_draw.draw_string(
            self.body.position + r, f"pivot velocity = ({vp.x:g}, {vp.y:g})", b2d.HexColor.White.value
        )


@register_sample("Bodies", "Kinematic")
class Kinematic(Box2dSample):
    """How to drive a kinematic body to reach a target transform."""

    camera_center = (0.0, 0.0)
    camera_zoom = 4.0

    amplitude = 2.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.time = 0.0
        self.target = None

        self.body = self.world.create_kinematic_body(position=(2.0 * self.amplitude, 0))
        self.body.create_shape(b2d.shape_def(), b2d.box(0.1, 1.0))

    def pre_update(self, dt):
        if dt <= 0.0:
            return
        point = (2.0 * self.amplitude * math.cos(self.time), self.amplitude * math.sin(2.0 * self.time))
        self.target = b2d.transform(p=point, q=b2d.make_rot(2.0 * self.time))
        self.body.set_target_transform(self.target, dt, wake=True)

    def post_update(self, dt):
        self.time += dt

    def post_debug_draw(self):
        if self.target is None:
            return
        point = self.target.p
        axis = b2d.rotate_vector(self.target.q, (0, 0.5))
        color = b2d.HexColor.Plum.value
        self.debug_draw.draw_segment(point - axis, point + axis, color)
        self.debug_draw.draw_point(point, 10.0, color)


@register_sample("Bodies", "Mixed Locks")
class MixedLocks(Box2dSample):
    """Bodies with different combinations of motion locks. Motion locking can be a bit squishy."""

    camera_center = (0.0, 2.5)
    camera_zoom = 3.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment(-40.0, 40.0)

        box = b2d.box(0.5, 0.5)
        shape_def = b2d.shape_def()

        self.world.create_static_body(position=(2, 1), name="static").create_shape(shape_def, box)

        for position, locks, name in (
            ((1, 1), {}, "free"),
            ((1, 3), {}, "free"),
            ((-1, 1), dict(angular_z=True), "angular z"),
            ((-2, 2), dict(linear_x=True), "linear x"),
            ((-1, 2.5), dict(linear_y=True, angular_z=True), "lin y ang z"),
            ((0, 1), dict(linear_x=True, linear_y=True, angular_z=True), "full"),
        ):
            body = self.world.create_dynamic_body(position=position, motion_locks=b2d.MotionLocks(**locks), name=name)
            body.create_shape(shape_def, box)


@register_sample("Bodies", "Set Velocity")
class SetVelocity(Box2dSample):
    """Setting the velocity of a box resting on the ground every step."""

    camera_center = (0.0, 2.5)
    camera_zoom = 3.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body(position=(0, -0.25))
        ground.create_shape(b2d.shape_def(), b2d.box(20.0, 0.25))

        self.body = self.world.create_dynamic_body(position=(0, 0.5))
        self.body.create_shape(b2d.shape_def(), b2d.box(0.5, 0.5))

    def post_update(self, dt):
        self.body.linear_velocity = (0, -20)


@register_sample("Bodies", "Wake Touching")
class WakeTouching(Box2dSample):
    """Waking all bodies touching the ground with a single call."""

    camera_center = (0.0, 4.0)
    camera_zoom = 8.0

    count = 10

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.ground = self.create_ground_segment()

        box = b2d.box(0.5, 0.5)
        shape_def = b2d.shape_def(density=1.0)
        for i in range(self.count):
            body = self.world.create_dynamic_body(position=(-1.0 * (self.count - 1) + 2.0 * i, 4.0))
            body.create_shape(shape_def, box)

        self.frontend.add_widget(widgets.Button(label="Wake Touching", callback=self.ground.wake_touching))
