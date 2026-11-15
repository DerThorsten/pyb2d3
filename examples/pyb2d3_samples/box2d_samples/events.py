"""Ports of box2d's samples/sample_events.cpp."""

import math
import random

import pyb2d3 as b2d
from pyb2d3_sandbox import register_sample, widgets

from ._common import Box2dSample
from ._stacking_helpers import (
    ROUNDED_BOX,
    Donut,
    Human,
    create_column,
    launch_body,
    random_polygon,
)

WHITE = b2d.HexColor.White.value


def _sensor_def(**kwargs):
    return b2d.shape_def(is_sensor=True, enable_sensor_events=True, **kwargs)


class _SpawnTimer:
    """Fires every `interval` seconds of simulated time (box2d's m_wait countdown)."""

    def __init__(self, wait=0.5, interval=0.5):
        self.wait = wait
        self.interval = interval

    def __call__(self, dt):
        self.wait -= dt
        if self.wait < 0.0:
            self.wait += self.interval
            return True
        return False


@register_sample("Events", "Sensor Funnel")
class SensorFunnel(Box2dSample):
    """Donuts or humans fall through a funnel and are destroyed by a sensor at the bottom."""

    camera_center = (0.0, 0.0)
    camera_zoom = 25.0 * 1.333
    count = 32

    points = [
        (-16.8672504, 31.088623), (16.8672485, 31.088623), (16.8672485, 17.1978741),
        (8.26824951, 11.906374), (16.8672485, 11.906374), (16.8672485, -0.661376953),
        (8.26824951, -5.953125), (16.8672485, -5.953125), (16.8672485, -13.229126),
        (3.63799858, -23.151123), (3.63799858, -31.088623), (-3.63800049, -31.088623),
        (-3.63800049, -23.151123), (-16.8672504, -13.229126), (-16.8672504, -5.953125),
        (-8.26825142, -5.953125), (-16.8672504, -0.661376953), (-16.8672504, 11.906374),
        (-8.26825142, 11.906374), (-16.8672504, 17.1978741),
    ]  # fmt: skip

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        ground.create_chain(
            b2d.chain_def(self.points, material=b2d.surface_material(friction=0.2), is_loop=True)
        )

        paddle_def = b2d.shape_def(density=1.0, material=b2d.surface_material(friction=0.1, restitution=1.0))
        sign = 1.0
        y = 14.0
        for _ in range(3):
            paddle = world.create_dynamic_body(position=(0.0, y))
            paddle.create_shape(paddle_def, b2d.box(6.0, 0.5))
            world.create_revolute_joint(
                body_a=ground,
                body_b=paddle,
                local_anchor_a=(0.0, y),
                max_motor_torque=200.0,
                motor_speed=2.0 * sign,
                enable_motor=True,
            )
            y -= 14.0
            sign = -sign

        ground.create_shape(_sensor_def(), b2d.box(4.0, 1.0, center=(0.0, -30.5)))

        self.timer = _SpawnTimer()
        self.side = -15.0
        self.type = "human"
        self.elements = [None] * self.count  # Donut / Ragdoll per slot
        self.create_element()

        self.frontend.add_widget(
            widgets.RadioButtons(label="Type", options=["donut", "human"], value=self.type, callback=self.set_type)
        )

    def set_type(self, element_type):
        self.clear()
        self.type = element_type

    def create_element(self):
        index = next((i for i, e in enumerate(self.elements) if e is None), None)
        if index is None:
            return
        center = (self.side, 29.5)
        # body user data: slot index + 1 (0 means "not an element")
        if self.type == "donut":
            element = Donut(self.world, center, 1.0, 0, True, user_data=index + 1)
        else:
            element = Human(self.world, center, 2.0, 0.05, 6.0, 0.5, index + 1, index + 1, True)
            element.enable_sensor_events()
        self.elements[index] = element
        self.side = -self.side

    def destroy_element(self, index):
        self.elements[index].destroy()
        self.elements[index] = None

    def clear(self):
        for index, element in enumerate(self.elements):
            if element is not None:
                self.destroy_element(index)

    def post_update(self, dt):
        # Defer destruction to avoid double destruction and event invalidation (orphaned shape ids)
        deferred = set()
        for event in self.world.get_sensor_events().begin_events():
            visitor = event.visitor_shape
            if visitor.is_valid and visitor.body.user_data > 0:
                deferred.add(visitor.body.user_data - 1)

        for index in deferred:
            if self.elements[index] is not None:
                self.destroy_element(index)

        if self.timer(dt):
            self.create_element()


@register_sample("Events", "Sensor Bookend")
class SensorBookend(Box2dSample):
    """Sensor begin / end events while creating, destroying, enabling and disabling sensors and visitors."""

    camera_center = (0.0, 6.0)
    camera_zoom = 7.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        for p1, p2 in [((-10.0, 0.0), (10.0, 0.0)), ((-10.0, 0.0), (-10.0, 10.0)), ((10.0, 0.0), (10.0, 10.0))]:
            ground.create_shape(b2d.shape_def(), b2d.segment(p1, p2))

        self.is_visiting1 = False
        self.is_visiting2 = False
        self.sensors_overlap_count = 0

        # name -> (create function, body, shape); the shape is kept after the body is destroyed for the end events
        self.creators = {"visitor": self.create_visitor, "sensor1": self.create_sensor1, "sensor2": self.create_sensor2}
        self.bodies = {}
        self.shapes = {}
        for name in self.creators:
            self.create(name)

        add = self.frontend.add_widget
        for name, label in [("visitor", "visitor"), ("sensor1", "sensor 1"), ("sensor2", "sensor 2")]:
            add(widgets.Button(label=f"create / destroy {label}", callback=lambda n=name: self.toggle(n)))
            add(widgets.Checkbox(label=f"{label} events", value=True,
                                 callback=lambda flag, n=name: self.enable_events(n, flag)))
            add(widgets.Checkbox(label=f"enable {label} body", value=True,
                                 callback=lambda flag, n=name: self.enable_body(n, flag)))

    def create(self, name):
        self.bodies[name], self.shapes[name] = self.creators[name]()

    def create_sensor1(self):
        body = self.world.create_static_body(position=(-2.0, 1.0))
        return body, body.create_shape(_sensor_def(), b2d.make_square(1.0))

    def create_sensor2(self):
        body = self.world.create_dynamic_body(position=(2.0, 1.0))
        shape = body.create_shape(_sensor_def(), b2d.box(0.5, 0.5, radius=0.5))
        # solid middle
        body.create_shape(b2d.shape_def(), b2d.make_square(0.5))
        return body, shape

    def create_visitor(self):
        body = self.world.create_dynamic_body(position=(-4.0, 1.0))
        return body, body.create_shape(b2d.shape_def(enable_sensor_events=True), b2d.circle(radius=0.5))

    def toggle(self, name):
        body = self.bodies.get(name)
        if body is None:
            self.create(name)
        else:
            body.destroy()
            self.bodies[name] = None

    def enable_events(self, name, flag):
        if self.bodies[name] is not None:
            self.shapes[name].sensor_events_enabled = flag

    def enable_body(self, name, flag):
        if self.bodies[name] is not None:
            self.bodies[name].enabled = flag

    def post_update(self, dt):
        visitor, sensor1, sensor2 = self.shapes["visitor"], self.shapes["sensor1"], self.shapes["sensor2"]
        events = self.world.get_sensor_events()
        for delta, event_list in ((1, events.begin_events()), (-1, events.end_events())):
            for event in event_list:
                if event.sensor_shape == sensor1:
                    if event.visitor_shape == visitor:
                        self.is_visiting1 = delta > 0
                    else:
                        self.sensors_overlap_count += delta
                elif event.sensor_shape == sensor2:
                    if event.visitor_shape == visitor:
                        self.is_visiting2 = delta > 0
                    else:
                        self.sensors_overlap_count += delta

        # Forget invalid shape ids after the end events are processed.
        for name, shape in self.shapes.items():
            if shape is not None and not shape.is_valid:
                self.shapes[name] = None

    def post_debug_draw(self):
        lines = [
            f"visiting 1 == {self.is_visiting1}",
            f"visiting 2 == {self.is_visiting2}",
            f"sensors overlap count == {self.sensors_overlap_count}",
        ]
        for i, line in enumerate(lines):
            self.debug_draw.draw_string((0.0, 9.0 - 0.6 * i), line, WHITE)


@register_sample("Events", "Foot Sensor")
class FootSensor(Box2dSample):
    """A foot sensor that counts the ground segments below the player. Move with 'a' and 'd'."""

    camera_center = (0.0, 6.0)
    camera_zoom = 7.5

    GROUND = 0x00000001
    PLAYER = 0x00000002
    FOOT = 0x00000004

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        chain = b2d.chain_def(
            [(9.0 - i, 0.0) for i in range(18)],
            filter=b2d.make_filter(category_bits=self.GROUND, mask_bits=self.FOOT | self.PLAYER),
        )
        chain.ghost1 = (10.0, 0.0)
        chain.ghost2 = (-9.0, 0.0)
        chain.enable_sensor_events = True
        ground.create_chain(chain)

        self.player = world.create_dynamic_body(position=(0.0, 1.0), motion_locks=b2d.MotionLocks(angular_z=True))
        material = b2d.surface_material(friction=0.3)
        self.player.create_shape(
            b2d.shape_def(filter=b2d.make_filter(category_bits=self.PLAYER, mask_bits=self.GROUND), material=material),
            b2d.capsule((0.0, -0.5), (0.0, 0.5), 0.5),
        )
        self.sensor = self.player.create_shape(
            _sensor_def(filter=b2d.make_filter(category_bits=self.FOOT, mask_bits=self.GROUND), material=material),
            b2d.box(0.5, 0.25, center=(0.0, -1.0)),
        )
        self.overlap_count = 0
        self.visitor_points = []

    def pre_update(self, dt):
        if self.is_key_pressed("a"):
            self.player.apply_force_to_center((-50.0, 0.0), True)
        if self.is_key_pressed("d"):
            self.player.apply_force_to_center((50.0, 0.0), True)

    def post_update(self, dt):
        events = self.world.get_sensor_events()
        self.overlap_count += sum(e.sensor_shape == self.sensor for e in events.begin_events())
        self.overlap_count -= sum(e.sensor_shape == self.sensor for e in events.end_events())
        self.visitor_points = [shape.bounds.center() for shape in self.sensor.sensor_overlaps]

    def post_debug_draw(self):
        for point in self.visitor_points:
            self.debug_draw.draw_point(point, 10.0, WHITE)
        self.debug_draw.draw_string(self.player.position + (0.0, 2.0), f"count == {self.overlap_count}", WHITE)


@register_sample("Events", "Contact")
class ContactEvent(Box2dSample):
    """Contact begin events: the player collects debris and loses it again on the walls. Move with WASD."""

    camera_center = (0.0, 0.0)
    camera_zoom = 25.0 * 1.75
    count = 20

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body()
        ground.create_chain(b2d.chain_def([(40.0, -40.0), (-40.0, -40.0), (-40.0, 40.0), (40.0, 40.0)], is_loop=True))

        self.player = world.create_dynamic_body(
            gravity_scale=0.0, linear_damping=0.5, angular_damping=0.5, is_bullet=True
        )
        # Enable contact events for the player shape
        self.core_shape = self.player.create_shape(b2d.shape_def(enable_contact_events=True), b2d.circle(radius=1.0))

        self.debris = [None] * self.count
        self.timer = _SpawnTimer()
        self.force = 200.0
        self.lines = []  # (p1, p2, color) of the contact impulses of this step

        self.frontend.add_widget(
            widgets.FloatSlider(label="force", min_value=100.0, max_value=500.0, step=1.0, value=self.force,
                                callback=lambda v: setattr(self, "force", v))
        )

    def spawn_debris(self):
        index = next((i for i, body in enumerate(self.debris) if body is None), None)
        if index is None:
            return

        body = self.world.create_dynamic_body(
            position=(random.uniform(-38.0, 38.0), random.uniform(-38.0, 38.0)),
            rotation=random.uniform(-math.pi, math.pi),
            linear_velocity=(random.uniform(-5.0, 5.0), random.uniform(-5.0, 5.0)),
            angular_velocity=random.uniform(-1.0, 1.0),
            gravity_scale=0.0,
            user_data=index + 1,  # 0 means "not debris"
        )
        # No events when debris hits debris
        shape_def = b2d.shape_def(material=b2d.surface_material(restitution=0.8), enable_contact_events=False)
        if (index + 1) % 3 == 0:
            geometry = b2d.circle(radius=0.5)
        elif (index + 1) % 2 == 0:
            geometry = b2d.capsule((0.0, -0.25), (0.0, 0.25), 0.25)
        else:
            geometry = b2d.box(0.4, 0.6)
        body.create_shape(shape_def, geometry)
        self.debris[index] = body

    def pre_update(self, dt):
        position = self.player.position
        for key, force in (("a", (-1, 0)), ("d", (1, 0)), ("w", (0, 1)), ("s", (0, -1))):
            if self.is_key_pressed(key):
                self.player.apply_force((self.force * force[0], self.force * force[1]), position, True)

    def contact_lines(self, shape, other, color):
        """The impulses of the contact between `shape` and `other`, read from the shape's contact data."""
        for data in shape.contact_data:
            if other not in (data.shape_a, data.shape_b):
                continue
            manifold = data.manifold
            center = data.shape_a.body.world_center
            for point in manifold.points:
                p1 = center + point.anchor_a
                self.lines.append((p1, p1 + point.total_normal_impulse * manifold.normal, color))

    def post_update(self, dt):
        self.lines = []
        debris_to_attach = []
        shapes_to_destroy = []

        for event in self.world.get_contact_events().begin_events():
            shape_a, shape_b = event.shape_a, event.shape_b

            # The begin touch events have the contact manifolds, but the impulses are zero. This is because the
            # manifolds are gathered before the contact solver is run. We can get the final contact data from the
            # shapes. The manifold is shared by the two shapes, so we just need the contact data from one of the
            # shapes. Choose the one with the smallest number of contacts.
            if shape_a.contact_capacity < shape_b.contact_capacity:
                self.contact_lines(shape_a, shape_b, b2d.HexColor.BlueViolet.value)
            else:
                self.contact_lines(shape_b, shape_a, b2d.HexColor.YellowGreen.value)

            if shape_a.body == self.player:
                player_shape, other_body = shape_a, shape_b.body
            elif shape_b.body == self.player:
                player_shape, other_body = shape_b, shape_a.body
            else:
                continue

            if other_body.user_data == 0:
                # player non-core shape hit the wall (avoid double deletion)
                if player_shape != self.core_shape and player_shape not in shapes_to_destroy:
                    shapes_to_destroy.append(player_shape)
            else:
                debris_to_attach.append(other_body.user_data - 1)

        # Attach debris to player body
        for index in debris_to_attach:
            debris = self.debris[index]
            if debris is None or not debris.is_valid or debris.shape_count == 0:
                continue
            relative = b2d.inv_mul_transforms(self.player.transform, debris.transform)
            shape = debris.shapes[0]
            if shape.type == b2d.ShapeType.circle:
                circle = shape.circle
                geometry = b2d.circle(center=b2d.transform_point(relative, circle.center), radius=circle.radius)
            elif shape.type == b2d.ShapeType.capsule:
                capsule = shape.capsule
                geometry = b2d.capsule(
                    b2d.transform_point(relative, capsule.center1),
                    b2d.transform_point(relative, capsule.center2),
                    capsule.radius,
                )
            else:
                geometry = b2d.transform_polygon(relative, shape.polygon)
            self.player.create_shape(b2d.shape_def(enable_contact_events=True), geometry)
            debris.destroy()
            self.debris[index] = None

        for shape in shapes_to_destroy:
            shape.destroy(update_body_mass=False)
        if shapes_to_destroy:
            # Update mass just once
            self.player.update_mass_from_shapes()

        if self.timer(dt):
            self.spawn_debris()

    def post_debug_draw(self):
        for p1, p2, color in self.lines:
            self.debug_draw.draw_segment(p1, p2, color)
            self.debug_draw.draw_point(p1, 10.0, WHITE)


@register_sample("Events", "Body Move")
class BodyMove(Box2dSample):
    """Body move events: draw the moving bodies and track which ones fell asleep."""

    camera_center = (2.0, 8.0)
    camera_zoom = 25.0 * 0.55
    count = 50

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        material = b2d.surface_material(friction=0.1)
        for hx, hy, center, angle in [(12.0, 0.1, (-10.0, -0.1), -0.15 * math.pi), (12.0, 0.1, (10.0, -0.1), 0.15 * math.pi)]:
            ground.create_shape(b2d.shape_def(material=material), b2d.box(hx, hy, center=center, rotation=angle))

        bouncy = b2d.shape_def(material=b2d.surface_material(friction=0.1, restitution=0.8))
        for hx, hy, center in [(0.1, 10.0, (19.9, 10.0)), (0.1, 10.0, (-19.9, 10.0)), (20.0, 0.1, (0.0, 20.1))]:
            ground.create_shape(bouncy, b2d.box(hx, hy, center=center))

        self.bodies = []
        self.sleeping = []
        self.sleep_count = 0
        self.moved_transforms = []

        self.explosion_position = (0.0, -5.0)
        self.explosion_radius = 10.0
        self.explosion_magnitude = 10.0

        self.frontend.add_widget(widgets.Button(label="Explode", callback=self.explode))
        self.frontend.add_widget(
            widgets.FloatSlider(label="Magnitude", min_value=-20.0, max_value=20.0, step=0.1,
                                value=self.explosion_magnitude,
                                callback=lambda v: setattr(self, "explosion_magnitude", v))
        )

    def explode(self):
        self.world.explode(
            position=self.explosion_position,
            radius=self.explosion_radius,
            falloff=0.1,
            impulse_per_length=self.explosion_magnitude,
        )

    def create_bodies(self):
        capsule = b2d.capsule((-0.25, 0.0), (0.25, 0.0), 0.25)
        circle = b2d.circle(radius=0.35)
        square = b2d.make_square(0.35)
        shape_def = b2d.shape_def()

        x, y = -5.0, 10.0
        for _ in range(10):
            n = len(self.bodies)
            if n >= self.count:
                break
            body = self.world.create_dynamic_body(position=(x, y), is_bullet=(n % 12 == 0), user_data=n + 1)
            remainder = n % 4
            if remainder == 0:
                geometry = capsule
            elif remainder == 1:
                geometry = circle
            elif remainder == 2:
                geometry = square
            else:
                geometry = random_polygon(0.75)
                geometry.radius = 0.1
            body.create_shape(shape_def, geometry)
            self.bodies.append(body)
            self.sleeping.append(False)
            x += 1.0

    def pre_update(self, dt):
        if (self.world_iteration & 15) == 15 and len(self.bodies) < self.count:
            self.create_bodies()

    def post_update(self, dt):
        self.moved_transforms = []
        for event in self.world.get_body_events().move_events():
            # The mouse drag body has no user data
            if event.user_data == 0:
                continue
            # draw the transform of every body that moved (not sleeping)
            self.moved_transforms.append(event.transform)

            # this shows a somewhat contrived way to track body sleeping
            index = event.user_data - 1
            if event.fell_asleep:
                self.sleeping[index] = True
                self.sleep_count += 1
            elif self.sleeping[index]:
                self.sleeping[index] = False
                self.sleep_count -= 1

    def post_debug_draw(self):
        for transform in self.moved_transforms:
            self.debug_draw.draw_transform(transform)
        self.debug_draw.draw_circle(self.explosion_position, self.explosion_radius, b2d.HexColor.Azure.value)


@register_sample("Events", "Sensor Types")
class SensorTypes(Box2dSample):
    """Static, kinematic and dynamic sensors and the shapes overlapping them."""

    camera_center = (0.0, 3.0)
    camera_zoom = 4.5

    GROUND = 0x00000001
    SENSOR = 0x00000002
    DEFAULT = 0x00000004

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body(name="ground")
        # Enable sensor events, but filter them out as a test
        ground_def = b2d.shape_def(
            filter=b2d.make_filter(category_bits=self.GROUND, mask_bits=self.DEFAULT), enable_sensor_events=True
        )
        for p1, p2 in [((-6.0, 0.0), (6.0, 0.0)), ((-6.0, 0.0), (-6.0, 4.0)), ((6.0, 0.0), (6.0, 4.0))]:
            ground.create_shape(ground_def, b2d.segment(p1, p2))

        sensor_def = _sensor_def(filter=b2d.make_filter(category_bits=self.SENSOR))
        square = b2d.make_square(1.0)

        static_body = world.create_static_body(name="static sensor", position=(-3.0, 0.8))
        self.static_sensor = static_body.create_shape(sensor_def, square)

        self.kinematic_body = world.create_kinematic_body(
            name="kinematic sensor", position=(0.0, 0.0), linear_velocity=(0.0, 1.0)
        )
        self.kinematic_sensor = self.kinematic_body.create_shape(sensor_def, square)

        dynamic_body = world.create_dynamic_body(name="dynamic sensor", position=(3.0, 1.0))
        self.dynamic_sensor = dynamic_body.create_shape(sensor_def, square)
        # Add some real collision so the dynamic body is valid
        dynamic_body.create_shape(
            b2d.shape_def(filter=b2d.make_filter(category_bits=self.DEFAULT)), b2d.make_square(0.8)
        )

        ball = world.create_dynamic_body(name="ball_01", position=(-5.0, 1.0))
        ball.create_shape(
            b2d.shape_def(
                filter=b2d.make_filter(
                    category_bits=self.DEFAULT, mask_bits=self.GROUND | self.DEFAULT | self.SENSOR
                ),
                enable_sensor_events=True,
            ),
            b2d.circle(radius=0.5),
        )

        self.ray_origin = (5.0, 1.0)
        self.ray_translation = (-10.0, 0.0)
        self.ray_hit = None

    def pre_update(self, dt):
        y = self.kinematic_body.position.y
        if y < 0.0:
            self.kinematic_body.linear_velocity = (0.0, 1.0)
        elif y > 3.0:
            self.kinematic_body.linear_velocity = (0.0, -1.0)

    def post_update(self, dt):
        result = self.world.cast_ray_closest(self.ray_origin, self.ray_translation)
        self.ray_hit = result.point if result.hit else None

    @staticmethod
    def overlap_names(sensor):
        names = (visitor.body.name for visitor in sensor.sensor_overlaps if visitor.is_valid)
        return ", ".join(name for name in names if name)

    def post_debug_draw(self):
        draw = self.debug_draw
        for sensor, prefix in [
            (self.static_sensor, "static"),
            (self.kinematic_sensor, "kinematic"),
            (self.dynamic_sensor, "dynamic"),
        ]:
            text = f"{prefix}: {self.overlap_names(sensor)}"
            draw.draw_string(sensor.body.position + (0.0, 1.5), text, WHITE)

        ox, oy = self.ray_origin
        tx, ty = self.ray_translation
        draw.draw_segment(self.ray_origin, (ox + tx, oy + ty), b2d.HexColor.DimGray.value)
        if self.ray_hit is not None:
            draw.draw_point(self.ray_hit, 10.0, b2d.HexColor.Cyan.value)


@register_sample("Events", "Joint")
class JointEvent(Box2dSample):
    """Break joints when the internal reaction force becomes large, using joint events instead of polling."""

    camera_center = (0.0, 8.0)
    camera_zoom = 25.0 * 0.7

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world
        ground = self.create_ground_segment(-40.0, 40.0)

        box = b2d.box(1.0, 1.0)
        common = dict(force_threshold=20000.0, torque_threshold=10000.0, collide_connected=True)

        def box_body(position):
            body = world.create_dynamic_body(position=position, enable_sleep=False)
            body.create_shape(b2d.shape_def(), box)
            return body

        def anchors(body, pivot):
            return dict(local_anchor_a=ground.local_point(pivot), local_anchor_b=body.local_point(pivot))

        self.joints = []
        x, y = -12.5, 10.0

        # distance joint
        body = box_body((x, y))
        length = 2.0
        self.joints.append(
            world.create_distance_joint(
                body_a=ground,
                body_b=body,
                local_anchor_a=ground.local_point((x, y + 1.0 + length)),
                local_anchor_b=body.local_point((x, y + 1.0)),
                length=length,
                **common,
            )
        )
        x += 5.0

        # motor joint
        body = box_body((x, y))
        self.joints.append(
            world.create_motor_joint(
                body_a=ground,
                body_b=body,
                local_anchor_a=(x, y),
                max_velocity_force=1000.0,
                max_velocity_torque=20.0,
                **common,
            )
        )
        x += 5.0

        # prismatic joint
        body = box_body((x, y))
        self.joints.append(world.create_prismatic_joint(body_a=ground, body_b=body, **anchors(body, (x - 1.0, y)), **common))
        x += 5.0

        # revolute joint
        body = box_body((x, y))
        self.joints.append(world.create_revolute_joint(body_a=ground, body_b=body, **anchors(body, (x - 1.0, y)), **common))
        x += 5.0

        # weld joint
        body = box_body((x, y))
        self.joints.append(
            world.create_weld_joint(
                body_a=ground,
                body_b=body,
                **anchors(body, (x - 1.0, y)),
                angular_hertz=2.0,
                angular_damping_ratio=0.5,
                **common,
            )
        )
        x += 5.0

        # wheel joint
        body = box_body((x, y))
        self.joints.append(
            world.create_wheel_joint(
                body_a=ground,
                body_b=body,
                **anchors(body, (x - 1.0, y)),
                hertz=1.0,
                damping_ratio=0.7,
                lower_translation=-1.0,
                upper_translation=1.0,
                enable_limit=True,
                enable_motor=True,
                max_motor_torque=10.0,
                motor_speed=1.0,
                **common,
            )
        )

        for index, joint in enumerate(self.joints):
            joint.user_data = index

    def post_update(self, dt):
        for event in self.world.get_joint_events().events():
            # Destroy the joint if it is still valid
            if event.joint.is_valid:
                event.joint.destroy()
                self.joints[event.user_data] = None


@register_sample("Events", "Persistent Contact")
class PersistentContact(Box2dSample):
    """Track a contact across time steps (e.g. for rolling or sliding sounds)."""

    camera_center = (0.0, 6.0)
    camera_zoom = 7.5

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        points = [(10.0 - i, 0.0) for i in range(20)] + [(-9.0, 10.0), (10.0, 10.0)]
        ground = self.world.create_static_body()
        ground.create_chain(b2d.chain_def(points, is_loop=True))

        body = self.world.create_dynamic_body(position=(-8.0, 1.0), linear_velocity=(2.0, 0.0))
        body.create_shape(b2d.shape_def(enable_contact_events=True), b2d.circle(radius=0.5))

        self.contact = None
        self.impulses = []  # (p1, p2, total normal impulse)

    def post_update(self, dt):
        events = self.world.get_contact_events()
        begin_events = events.begin_events()
        if begin_events:
            self.contact = begin_events[0].contact
        if any(self.contact == event.contact for event in events.end_events()):
            self.contact = None

        # Contacts are created and destroyed by Box2D, so it is important to make
        # sure a contact id is valid before accessing contact data.
        self.impulses = []
        if self.contact is None or not self.contact.is_valid:
            self.contact = None
            return
        data = self.contact.data
        center = data.shape_a.body.world_center
        for point in data.manifold.points:
            p1 = center + point.anchor_a
            p2 = p1 + point.total_normal_impulse * data.manifold.normal
            self.impulses.append((p1, p2, point.total_normal_impulse))

    def post_debug_draw(self):
        crimson = b2d.HexColor.Crimson.value
        for p1, p2, impulse in self.impulses:
            self.debug_draw.draw_segment(p1, p2, crimson)
            self.debug_draw.draw_point(p1, 6.0, crimson)
            self.debug_draw.draw_string(p1, f"{impulse:.2f}", WHITE)


@register_sample("Events", "Sensor Hits")
class SensorHits(Box2dSample):
    """Sensor events for fast (bullet) bodies passing static, kinematic and dynamic sensors. Press 'b' to launch."""

    camera_center = (0.0, 5.0)
    camera_zoom = 7.5
    transform_capacity = 20

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        world = self.world

        ground = world.create_static_body(name="ground")
        ground.create_shape(b2d.shape_def(), b2d.segment((-10.0, 0.0), (10.0, 0.0)))
        ground.create_shape(b2d.shape_def(), b2d.segment((10.0, 0.0), (10.0, 10.0)))

        segment = b2d.segment((0.0, 0.0), (0.0, 10.0))

        static_body = world.create_static_body(name="static sensor", position=(-4.0, 1.0))
        self.static_sensor = static_body.create_shape(_sensor_def(), segment)

        self.kinematic_body = world.create_kinematic_body(
            name="kinematic sensor", position=(0.0, 1.0), linear_velocity=(0.5, 0.0)
        )
        self.kinematic_sensor = self.kinematic_body.create_shape(_sensor_def(), segment)

        position = (4.0, 1.0)
        self.dynamic_body = world.create_dynamic_body(name="dynamic sensor", position=position)
        self.dynamic_sensor = self.dynamic_body.create_shape(
            _sensor_def(), b2d.capsule((0.0, 1.0), (0.0, 9.0), 0.1)
        )
        pivot = (position[0], position[1] + 6.0)
        # the joint axis is the x axis of the local frames: (1, 0)
        self.joint = world.create_prismatic_joint(
            body_a=ground,
            body_b=self.dynamic_body,
            local_anchor_a=ground.local_point(pivot),
            local_anchor_b=self.dynamic_body.local_point(pivot),
            enable_motor=True,
            max_motor_force=1000.0,
            motor_speed=0.5,
        )

        self.is_bullet = True
        self.body = None
        self.transforms = []
        self.begin_count = 0
        self.end_count = 0
        self.launch()

        self.frontend.add_widget(
            widgets.Checkbox(label="Bullet", value=self.is_bullet, callback=lambda v: setattr(self, "is_bullet", v))
        )
        self.frontend.add_widget(widgets.Button(label="Launch", callback=self.launch))

    def launch(self):
        if self.body is not None and self.body.is_valid:
            self.body.destroy()
        self.transforms = []
        self.begin_count = 0
        self.end_count = 0

        self.body = launch_body(self.world, (-26.7, 6.0), self.is_bullet)
        shape_def = b2d.shape_def(
            enable_sensor_events=True, material=b2d.surface_material(friction=0.8, rolling_resistance=0.01)
        )
        self.body.create_shape(shape_def, b2d.circle(radius=0.25))

    def on_key_down(self, event):
        if event.key == "b":
            self.launch()

    def collect_transforms(self, sensor):
        capacity = 5
        for _ in sensor.sensor_overlaps[:capacity]:
            if len(self.transforms) >= self.transform_capacity:
                break
            self.transforms.append(sensor.body.transform)

    def pre_update(self, dt):
        x = self.kinematic_body.position.x
        if x > 1.0:
            self.kinematic_body.linear_velocity = (-0.5, 0.0)
        elif x < -1.0:
            self.kinematic_body.linear_velocity = (0.5, 0.0)

        translation = self.joint.current_translation
        if translation > 1.0:
            self.joint.target_motor_speed = -0.5
        elif translation < -1.0:
            self.joint.target_motor_speed = 0.5

    def post_update(self, dt):
        events = self.world.get_sensor_events()
        self.begin_count += events.begin_count
        self.end_count += events.end_count
        for event in events.begin_events():
            if event.sensor_shape.is_valid:
                self.collect_transforms(event.sensor_shape)

    def post_debug_draw(self):
        for transform in self.transforms:
            self.debug_draw.draw_transform(transform)


@register_sample("Events", "Projectile Event")
class ProjectileEvent(Box2dSample):
    """A projectile that explodes on impact.

    Drag from empty space to aim and release to shoot (box2d uses Ctrl + left mouse).
    """

    camera_center = (-7.0, 9.0)
    camera_zoom = 14.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        ground = self.world.create_static_body()
        ground_def = b2d.shape_def(enable_sensor_events=True)
        ground.create_shape(ground_def, b2d.segment((10.0, 0.0), (10.0, 20.0)))
        ground.create_shape(ground_def, b2d.segment((-30.0, 0.0), (30.0, 0.0)))

        create_column(self.world, 8.0, 8, b2d.shape_def(enable_sensor_events=True), ROUNDED_BOX, offset=0.01)

        self.projectile = None
        self.projectile_shape = None
        self.dragging = False
        self.point1 = (0.0, 0.0)
        self.point2 = (0.0, 0.0)

    def fire_projectile(self):
        if self.projectile is not None and self.projectile.is_valid:
            self.projectile.destroy()
        (x1, y1), (x2, y2) = self.point1, self.point2
        self.projectile = self.world.create_dynamic_body(
            position=self.point1, linear_velocity=(4.0 * (x2 - x1), 4.0 * (y2 - y1)), is_bullet=True
        )
        self.projectile_shape = self.projectile.create_shape(
            b2d.shape_def(enable_contact_events=True), b2d.circle(radius=0.25)
        )

    def on_mouse_down(self, event):
        super().on_mouse_down(event)
        if self.mouse_joint_body is None:
            self._camera_drag = False
            self.dragging = True
            self.point1 = self.point2 = tuple(event.world_position)

    def on_mouse_move(self, event):
        super().on_mouse_move(event)
        if self.dragging:
            self.point2 = tuple(event.world_position)

    def on_mouse_up(self, event):
        super().on_mouse_up(event)
        if self.dragging:
            self.dragging = False
            self.fire_projectile()

    def on_mouse_leave(self, event):
        super().on_mouse_leave(event)
        self.dragging = False

    def post_update(self, dt):
        if self.projectile_shape is None:
            return
        for event in self.world.get_contact_events().begin_events():
            if self.projectile_shape not in (event.shape_a, event.shape_b):
                continue
            if event.contact.is_valid:
                data = event.contact.data
                if data.manifold.point_count > 0:
                    position = data.shape_a.body.world_center + data.manifold.points[0].anchor_a
                    self.world.explode(position=position, radius=1.0, impulse_per_length=20.0)
                    self.projectile.destroy()
                    self.projectile = None
            break

    def post_debug_draw(self):
        if self.dragging:
            self.debug_draw.draw_segment(self.point1, self.point2, WHITE)
            self.debug_draw.draw_point(self.point1, 5.0, b2d.HexColor.Green.value)
            self.debug_draw.draw_point(self.point2, 5.0, b2d.HexColor.Red.value)


@register_sample("Events", "Circle Impulse")
class CircleImpulse(Box2dSample):
    """Hit events and contact impulses of a circle hitting the ground."""

    camera_center = (0.0, 2.7)
    camera_zoom = 3.4

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.create_ground_segment(-10.0, 10.0)

        self.restitution = 0.25
        self.use_gravity = False
        self.use_restitution = False
        self.mass = 1.0
        self.body = None
        self.events = []  # (approach speed, impulse, total impulse)
        self.hit_points = []
        self.spawn()

        self.frontend.add_widget(widgets.Checkbox(label="gravity", value=self.use_gravity,
                                                  callback=lambda v: self.spawn(use_gravity=v)))
        self.frontend.add_widget(widgets.Checkbox(label="restitution", value=self.use_restitution,
                                                  callback=lambda v: self.spawn(use_restitution=v)))

    def spawn(self, **changes):
        for name, value in changes.items():
            setattr(self, name, value)
        if self.body is not None:
            self.body.destroy()
        self.events = []

        self.body = self.world.create_dynamic_body(
            position=(0.0, 5.5),
            linear_velocity=(0.0, -25.0),
            gravity_scale=1.0 if self.use_gravity else 0.0,
        )
        shape_def = b2d.shape_def(
            enable_hit_events=True,
            material=b2d.surface_material(
                friction=0.0, restitution=self.restitution if self.use_restitution else 0.0
            ),
        )
        self.body.create_shape(shape_def, b2d.circle(radius=0.25))

        # Override mass
        mass_data = self.body.mass_data
        ratio = self.mass / mass_data.mass
        mass_data.mass = self.mass
        mass_data.rotational_inertia *= ratio
        self.body.mass_data = mass_data

    def post_update(self, dt):
        self.hit_points = []
        for hit in self.world.get_contact_events().hit_events():
            self.hit_points.append(hit.point)
            impulse = total_impulse = 0.0
            data = hit.contact.data
            if data.manifold.point_count > 0:
                impulse = data.manifold.points[0].normal_impulse
                total_impulse = data.manifold.points[0].total_normal_impulse
            self.events.append((hit.approach_speed, impulse, total_impulse))

    def post_debug_draw(self):
        for point in self.hit_points:
            self.debug_draw.draw_point(point, 10.0, WHITE)
        for i, (speed, impulse, total_impulse) in enumerate(self.events):
            line = (
                f"hit speed = {speed:g}, hit momentum = {self.mass * speed:g}, "
                f"final impulse = {impulse:g}, total impulse = {total_impulse:g}"
            )
            self.debug_draw.draw_string((0.0, 5.8 - 0.25 * i), line, WHITE)
