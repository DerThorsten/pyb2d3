# +
import pyb2d3 as b2d
import numpy as np
from pyb2d3_sandbox import SampleBase
import pyb2d3_sandbox.widgets as widgets

from dataclasses import dataclass

# some constants to not overcomplicate the example
BALL_RADIUS = 0.1
HOLE_RADIUS = 0.2
FORCE_VECTOR_DRAW_WIDTH = 0.05
MAX_FORCE_VECTOR_LENGTH = 2


@dataclass
class LevelData:
    pass


Levels = [LevelData(), LevelData()]


class UserDataStore(object):
    def __init__(self):
        self.id = 0
        self.data = {}

    def add(self, data):
        self.id += 1
        self.data[self.id] = data
        return self.id

    def __getitem__(self, key):
        if key == 0:
            return None
        return self.data.get(key, None)

    def __delitem__(self, key):
        if key == 0:
            raise KeyError("Cannot delete key 0 from UserData")
        if key in self.data:
            del self.data[key]
        else:
            raise KeyError(f"Key {key} not found in UserData")


class Goo(object):
    def __init__(self, sample):
        self.sample = sample
        self.world = sample.world
        self.ud = sample.ud
        self.body = None
        self.hertz = 4.0
        self.gravity_scale = 1.0
        self.density = 1.0
        self.friction = 0.5
        self.restitution = 0.2
        self.radius = 0.5
        self.enable_spring = True
        self.proto_edge_length = 2  # prototypical edge length for the goo ball
        self.discover_radius = self.proto_edge_length
        self.as_edge_max_distance = self.proto_edge_length
        self.as_goo_max_distance = (
            self.proto_edge_length * 2
        ) ** 2  # maximum distance to place as goo ball
        self.auto_expand = False
        self.connections = []  # list of connections to other goo balls
        self.max_degree = 40  # maximum number of connections per goo ball
        self.place_as_edge_squared_distance_threshold = (
            self.radius / 2
        ) ** 2  # threshold for placing as edge

    @property
    def debug_draw(self):
        return self.sample.debug_draw

    def has_capacity(self):
        # check if this goo ball can add more connections
        return len(self.connections) < self.max_degree

    def degrees(self):
        # return the number of connections this goo ball has
        return len(self.connections)

    def is_object_between_me_and_point(self, world_point):
        assert self.body is not None, "Goo ball not created yet. Cannot check for objects."

        own_pos = self.body.position
        translation = (world_point[0] - own_pos[0], world_point[1] - own_pos[1])

        # cast a ray from the goo ball to the world point
        ray_result = self.world.cast_ray_closest(origin=own_pos, translation=translation)
        return ray_result.hit

    def can_be_placed_here(self, world, pos):
        assert self.body is None, "Goo ball already created. Cannot place again."
        goos = self.sample.find_all_goos_in_radius(pos, self.discover_radius * 2)
        if not goos:
            return (False, False, None, None)

        # filter out goos that cannot add more connections
        goos = [(goo, dist) for goo, dist in goos if goo.degrees() < goo.max_degree]

        # filter out goos where there is an object between the goo and the position
        goos = [(goo, dist) for goo, dist in goos if not goo.is_object_between_me_and_point(pos)]

        # check if we can place as edge
        if len(goos) >= 2:
            # compute the best mid point between all pairs of goo balls
            # and the "pos" point
            best_pair = None
            best_distance = float("inf")
            for i in range(len(goos)):
                goo_a = goos[i][0]

                for j in range(i + 1, len(goos)):
                    goo_b = goos[j][0]

                    if goo_a.is_conncted_to(goo_b):
                        continue

                    d = b2d.mid_point_squared_distance(
                        goo_a.get_position(), goo_b.get_position(), pos
                    )

                    if d < best_distance:
                        best_distance = d
                        best_pair = (goo_a, goo_b)

            if best_distance <= self.place_as_edge_squared_distance_threshold:
                # we can place as edge
                return (True, True, best_pair, pos)

        # check if we can place as ball
        if len(goos) >= 2:
            best_pair = None
            best_distance = float("inf")
            for i in range(len(goos)):
                goo_a = goos[i][0]

                for j in range(i + 1, len(goos)):
                    goo_b = goos[j][0]

                    if not goo_a.is_conncted_to(goo_b):
                        continue

                    d = goos[i][1] + goos[j][1]
                    if d < best_distance:
                        best_distance = d
                        best_pair = (goo_a, goo_b)

            if best_distance <= self.as_goo_max_distance:
                # we can place as goo ball
                # return the two goo balls and the position
                return (True, False, best_pair, pos)

        return (False, False, None, None)

    def get_position(self):
        if self.body is not None:
            return self.body.position
        return None

    def create(self, world, pos):
        # create a dynamic body with a circle shape
        self.body = world.create_dynamic_body(
            position=pos, gravity_scale=self.gravity_scale, fixed_rotation=True
        )

        material = b2d.surface_material(
            restitution=self.restitution,
            friction=self.friction,
            custom_color=type(self).color_hex,
        )
        self.body.create_shape(
            b2d.shape_def(density=self.density, material=material, enable_contact_events=False),
            b2d.circle(radius=self.radius),
        )
        # set the user data to the Goo object itself
        self.body.user_data = self.ud.add(self)

        return self

    def connect(self, other_goo):
        # connect this goo ball to another goo ball with a distance joint
        if self.body is None or other_goo.body is None:
            raise ValueError("Both goo balls must be created before connecting them.")

        body_a = self.body
        body_b = other_goo.body

        if not self.auto_expand:
            edge_length = body_a.get_distance_to(body_b.position)
        else:
            edge_length = self.proto_edge_length

        joint_def = b2d.distance_joint_def(
            body_a=self.body,
            body_b=other_goo.body,
            length=edge_length,
            hertz=self.hertz,
            damping_ratio=0.5,
            enable_spring=self.enable_spring,
            collide_connected=True,
        )
        j = self.body.world.create_joint(joint_def)
        # set the user data to the joint

        # we store a "direction" st. we only
        # draw the edges once
        self.connections.append((other_goo, j, True))
        other_goo.connections.append((self, j, False))

    def is_conncted_to(self, other_goo):
        # check if this goo ball is connected to another goo ball
        for item in self.connections:
            if item[0] == other_goo:
                return True
        return False

    def draw_at(self, world_pos, angle=0):
        self.debug_draw.draw_solid_circle(
            transform=b2d.transform(world_pos),
            radius=self.radius,
            color=type(self).color_rgb,
        )
        self.debug_draw.draw_circle(world_pos, radius=self.radius, color=(0, 0, 0))

        eye_radius = self.radius / 4
        eye_offset = self.radius / 2.5
        local_left_eye_pos = (-eye_offset, -eye_offset / 2)
        local_right_eye_pos = (eye_offset, -eye_offset / 2)
        local_left_pupil_pos = (
            local_left_eye_pos[0] + eye_radius / 2,
            local_left_eye_pos[1],
        )
        local_right_pupil_pos = (
            local_right_eye_pos[0] + eye_radius / 2,
            local_right_eye_pos[1],
        )

        if self.body is not None:
            # get eye position in world coordinates
            left_eye_pos = self.body.world_point(local_left_eye_pos)
            right_eye_pos = self.body.world_point(local_right_eye_pos)
            left_pupil_pos = self.body.world_point(local_left_pupil_pos)
            right_pupil_pos = self.body.world_point(local_right_pupil_pos)
        else:
            left_eye_pos = world_pos + local_left_eye_pos
            right_eye_pos = world_pos + local_right_eye_pos
            left_pupil_pos = world_pos + local_left_pupil_pos
            right_pupil_pos = world_pos + local_right_pupil_pos

        # draw the eyes
        self.debug_draw.draw_solid_circle(
            transform=b2d.transform(left_eye_pos),
            radius=eye_radius,
            color=(255, 255, 255),
        )
        self.debug_draw.draw_solid_circle(
            transform=b2d.transform(right_eye_pos),
            radius=eye_radius,
            color=(255, 255, 255),
        )
        # draw the pupils
        self.debug_draw.draw_solid_circle(
            transform=b2d.transform(left_pupil_pos),
            radius=eye_radius / 2,
            color=(0, 0, 0),
        )
        self.debug_draw.draw_solid_circle(
            transform=b2d.transform(right_pupil_pos),
            radius=eye_radius / 2,
            color=(0, 0, 0),
        )

    def draw(self):
        assert self.body is not None, "Goo ball not created yet. Cannot draw."
        self.draw_at(self.body.position, self.body.angle)

    def draw_edge(self, p1, p2):
        self.debug_draw.draw_segment(p1, p2, color=(100, 100, 100))

    def draw_tentative_as_goo(self, pos, other_goos):
        for goo in other_goos:
            # draw the edge to the other goo ball
            self.draw_edge(goo.get_position(), pos)

        # draw the goo via draw_at
        self.draw_at(pos)

    def draw_tentative_as_edge(self, goo_a, goo_b):
        # draw via draw_edge
        self.draw_edge(goo_a.get_position(), goo_b.get_position())


class BlueGoo(Goo):
    color_rgb = (50, 50, 255)  # dark blue
    color_hex = b2d.hex_color(*color_rgb)
    text_color = (255, 255, 255)  # white text color
    name = "Plain Goo"

    def __init__(self, sample):
        super().__init__(sample)

    def draw_edge(self, p1, p2):
        self.debug_draw.draw_segment(p1=p1, p2=p2, color=BlueGoo.color_rgb)


class WhiteGoo(Goo):
    color_rgb = (200, 200, 200)  # light gray
    color_hex = b2d.hex_color(*color_rgb)
    text_color = (0, 0, 0)  # black text color
    name = "Drip Goo"

    def __init__(self, sample):
        super().__init__(sample)
        self.max_degree = 2  # white goo can connect to two other goo ball, ie forming line segments
        self.hertz = 2.0  # white goo is very elastic
        self.density = 0.25  # white goo is very light

    def draw_edge(self, p1, p2):
        self.debug_draw.draw_segment(p1=p1, p2=p2, color=WhiteGoo.color_rgb)

    def can_be_placed_here(self, world, pos):
        assert self.body is None, "Goo ball already created. Cannot place again."
        goos = self.sample.find_all_goos_in_radius(pos, self.discover_radius * 2)

        close_goo = None
        closest_distance = float("inf")

        for goo, dist in goos:
            # check if ther is an object between the goo and the position
            if goo.is_object_between_me_and_point(pos):
                continue
            if goo.has_capacity():
                if dist < closest_distance:
                    closest_distance = dist
                    close_goo = goo
        if close_goo is not None:
            # we can place as goo ball
            return (True, False, (close_goo,), pos)
        return (False, False, None, None)


# ballon, can only be connected to a single other goo
class RedGoo(Goo):
    color_rgb = (255, 0, 0)  # red
    color_hex = b2d.hex_color(*color_rgb)
    text_color = (255, 255, 255)  # white text color
    name = "Ballon Goo"

    def __init__(self, sample):
        super().__init__(sample)
        self.density = 0.5  # less dense than blue goo
        self.gravity_scale = -1.0
        self.hertz = 8.0
        self.enable_spring = False
        self.max_degree = 1  # red goo can only connect to one other goo ball
        self.auto_expand = True

    def draw_edge(self, p1, p2):
        self.debug_draw.draw_segment(
            p1=p1,
            p2=p2,
            # rope like color (ie brown orangish)
            color=(255, 100, 0),
        )

    def can_be_placed_here(self, world, pos):
        assert self.body is None, "Goo ball already created. Cannot place again."
        goos = self.sample.find_all_goos_in_radius(pos, self.discover_radius * 2)

        close_goo = None
        closest_distance = float("inf")

        for goo, dist in goos:
            if goo.is_object_between_me_and_point(pos):
                continue
            if goo.has_capacity():
                if dist < closest_distance:
                    closest_distance = dist
                    close_goo = goo
        if close_goo is not None:
            # we can place as goo ball
            return (True, False, (close_goo,), pos)
        return (False, False, None, None)


class BlackGoo(Goo):
    color_rgb = (10, 10, 0)  # almost black
    color_hex = b2d.hex_color(*color_rgb)
    text_color = (255, 255, 255)  # white text color
    name = "Heavy Goo"

    def __init__(self, sample):
        super().__init__(sample)
        self.density = 15
        self.hertz = 10  # very stiff

    def draw_edge(self, p1, p2):
        self.debug_draw.draw_segment(
            p1=p1,
            p2=p2,
            color=BlackGoo.color_rgb,
        )


class GooGame(SampleBase):
    @dataclass
    class Settings(SampleBase.Settings):
        current_level: int = 0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)

        # goo classes
        self.goo_classes = [BlueGoo, RedGoo, WhiteGoo, BlackGoo]
        self.goo_name_to_index = {goo_cls.name: i for i, goo_cls in enumerate(self.goo_classes)}

        self.selected_goo_cls = BlueGoo

        # the user data store
        self.ud = UserDataStore()

        # some state
        self.next_goo = self.selected_goo_cls(self)
        self.tentative_placement = (False, None, None, None)
        self.mouse_is_down = False
        self.drag_camera = False

        # add ui-elements
        self.frontend.add_widget(
            widgets.RadioButtons(
                label="Goo Type",
                options=[goo_cls.name for goo_cls in self.goo_classes],
                value=self.selected_goo_cls.name,
                callback=lambda goo_name: self.on_goo_change(self.goo_name_to_index[goo_name]),
            )
        )

    def on_goo_change(self, new_goo_type):
        # change the next goo type
        self.selected_goo_cls = self.goo_classes[new_goo_type]
        self.next_goo = self.selected_goo_cls(self)

    def on_mouse_down(self, event):
        self.mouse_is_down = True
        # self.last_canvas_pos = event.canvas_position
        self.tentative_placement = self.next_goo.can_be_placed_here(
            self.world, event.world_position
        )

        # if we cannot place the goo ball, we can drag the camera
        if not self.tentative_placement[0]:
            self.drag_camera = True

    def on_mouse_move(self, event):
        if self.mouse_is_down:
            world_point = event.world_position
            if self.drag_camera:
                # drag the camera
                self.frontend.drag_camera(event.world_delta)
            else:
                self.tentative_placement = self.next_goo.can_be_placed_here(self.world, world_point)
        # self.last_canvas_pos = p

    def on_mouse_up(self, event):
        self.mouse_is_down = False
        self.drag_camera = False
        world_point = event.world_position
        self.tentative_placement = self.next_goo.can_be_placed_here(self.world, world_point)
        if self.tentative_placement[0]:
            as_edge, goo_pair = self.tentative_placement[1], self.tentative_placement[2]
            if as_edge:
                # place as edge
                self.place_as_goo_edge(goo_pair[0], goo_pair[1])
            else:
                # place as ball
                self.place_as_goo(goo_pair, world_point)

            self.tentative_placement = (False, None, None)

    def aabb(self):
        margin = 5
        min_x = float("inf")
        max_x = float("-inf")
        min_y = float("inf")
        max_y = float("-inf")
        for goo in self.goo_balls:
            if goo.body is not None:
                pos = goo.get_position()
                margin = max(margin, goo.radius + 0.1)
                min_x = min(min_x, pos[0] - goo.radius - margin)
                max_x = max(max_x, pos[0] + goo.radius + margin)
                min_y = min(min_y, pos[1] - goo.radius - margin)
                max_y = max(max_y, pos[1] + goo.radius + margin)

        # aabb with margin
        return b2d.aabb(
            lower_bound=(min_x - margin, min_y - margin),
            upper_bound=(max_x + margin, max_y + margin),
        )

    # place as goo ball method
    def place_as_goo(self, goos_to_connect, world_point):
        self.next_goo.create(self.world, world_point)
        for g in goos_to_connect:
            self.next_goo.connect(g)
        self.goo_balls.append(self.next_goo)
        self.next_goo = self.selected_goo_cls(self)

    def place_as_goo_edge(self, goo_a, goo_b):
        goo_a.connect(goo_b)
        self.next_goo = self.selected_goo_cls(self)

    def find_all_goos_in_radius(self, pos, radius):
        ud = self.ud
        aabb = b2d.aabb_arround_point(point=pos, radius=radius)
        result = []

        square_radius = radius * radius

        def callback(shape):
            goo = ud[shape.body.user_data]
            if isinstance(goo, Goo):
                goo_pos = goo.get_position()
                distance_squared = (goo_pos[0] - pos[0]) ** 2 + (goo_pos[1] - pos[1]) ** 2
                if distance_squared <= square_radius:
                    result.append((goo, distance_squared))
            return True  # <-- continue searching

        self.world.overlap_aabb(aabb, callback)
        return result

    def post_debug_draw(self):
        # draw edges
        for goo in self.goo_balls:
            for other_goo, joint, created_edge in goo.connections:
                if created_edge:
                    goo.draw_edge(goo.get_position(), other_goo.get_position())

        if self.tentative_placement[0]:
            placable, as_edge, other_goos, pos = self.tentative_placement
            if as_edge:
                # draw the edge between the two goo balls
                goo_a, goo_b = other_goos
                self.next_goo.draw_tentative_as_edge(goo_a, goo_b)
            else:
                self.next_goo.draw_tentative_as_goo(pos, other_goos)

        # draw goos
        for goo in self.goo_balls:
            goo.draw()


class Level1(GooGame):
    @dataclass
    class Settings(GooGame.Settings):
        pass

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)

        self.outer_box_radius = 100

        vertices = np.array(
            [
                (-100, 100),
                (-100, 0),
                (5, 0),
                (5, -100),
                (20, -100),
                (20, 0),
                (60, 0),
                (60, 100),
            ]
        )[::-1]  # reverse the order to make it clockwise
        self.outer_vertices = vertices

        # attach the chain shape to a static body
        self.box_body = self.world.create_static_body(position=(0, 0))
        self.box_body.create_chain(b2d.chain_def(points=vertices, is_loop=True))

        goo_cls = BlueGoo

        g = goo_cls(self)
        edge_length = goo_cls(self).proto_edge_length
        r = g.radius
        # 3 goo balls as equilateral triangle with edge_length as the length of the edges
        self.goo_balls = [
            goo_cls(self).create(self.world, (-edge_length / 2, 0 + r)),
            goo_cls(self).create(self.world, (edge_length / 2, 0 + r)),
            goo_cls(self).create(self.world, (0, (edge_length / 2) * np.sqrt(3) + r)),
        ]
        # connect the goo balls
        self.goo_balls[0].connect(self.goo_balls[1])
        self.goo_balls[1].connect(self.goo_balls[2])
        self.goo_balls[2].connect(self.goo_balls[0])

        # if we are in a headless mode, add one more goo to make it a bit whobbly
        if self.frontend.settings.headless:
            g = goo_cls(self)
            g.create(self.world, (3.5, 3))
            self.goo_balls.append(g)

            self.goo_balls[1].connect(g)
            self.goo_balls[2].connect(g)


if __name__ == "__main__":
    Level1.run()
