# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


import random
import math


class CastRayCallback(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.box_radius = 10

        # we create shapes of 4 categories:
        # wall
        # laser
        # box

        wall_category_bits = 0 | (1 << 0)  # 0x00000001
        laser_category_bits = 0 | (1 << 1)  # 0x00000002
        box_green_category_bits = 0 | (1 << 2)  # 0x00000004
        box_blue_category_bits = 0 | (1 << 3)  # 0x00000008

        self.laser_category_bits = laser_category_bits
        self.box_green_category_bits = box_green_category_bits
        self.box_blue_category_bits = box_blue_category_bits
        self.wall_category_bits = wall_category_bits

        # set 0 bits for the wall

        # attach the chain shape to a static body
        self.box_body = self.world.create_static_body(position=(0, 0))
        chain_def = b2d.chain_box(center=(0, 0), hx=self.box_radius, hy=self.box_radius)
        chain_def.filter = b2d.make_filter(category_bits=wall_category_bits)
        self.box_body.create_chain(
            b2d.chain_box(center=(0, 0), hx=self.box_radius, hy=self.box_radius)
        )

        # creating a box serving as "laser"
        self.laser_body = self.world.create_dynamic_body(
            position=(0, 0),
            linear_damping=10,
            angular_damping=10.0,
            rotation=math.pi / 2.1,  # some funky angle
        )
        self.laser_body.create_shape(
            b2d.shape_def(
                density=1,
                material=b2d.surface_material(
                    restitution=0.5, custom_color=b2d.rgb_to_hex_color(255, 240, 40)
                ),
                filter=b2d.make_filter(category_bits=laser_category_bits),
            ),
            b2d.box(hx=0.4, hy=1.0),
        )

        # some random boxes
        for i in range(20):
            x = random.uniform(-self.box_radius, self.box_radius)
            y = random.uniform(-self.box_radius, self.box_radius)
            random_angle = random.uniform(0, 2 * math.pi)
            box_body = self.world.create_dynamic_body(
                position=(x, y),
                linear_damping=10.0,
                angular_damping=10.0,
                rotation=random_angle,
            )
            if i % 2 == 0:
                category_bits = self.box_green_category_bits
                color = b2d.rgb_to_hex_color(40, 240, 40)
            else:
                category_bits = self.box_blue_category_bits
                color = b2d.rgb_to_hex_color(40, 40, 240)

            box_body.create_shape(
                b2d.shape_def(
                    density=1,
                    material=b2d.surface_material(restitution=0.5, custom_color=color),
                    filter=b2d.make_filter(category_bits=category_bits),
                ),
                b2d.box(hx=0.5, hy=1.0),
            )

        # we make the mouse joint(created in the base class) more stiff
        self.mouse_joint_hertz = 10000
        self.mouse_joint_force_multiplier = 10000.0

    def aabb(self):
        return b2d.aabb(
            lower_bound=(-self.box_radius, -self.box_radius),
            upper_bound=(self.box_radius, self.box_radius),
        )

    def post_debug_draw(self):
        if self.frontend.settings.headless:
            # to have some movement when running headless (ie for rendering a video of the sample)
            torque = 2
            self.laser_body.apply_torque(torque, wake=True)

        ray_length = self.box_radius * 2 * math.sqrt(2)
        ray_length = max(ray_length, 1)

        eps = 1e-5
        pos = self.laser_body.world_point((0, 1 - eps))
        body_angle = self.laser_body.angle + math.pi / 2  # laser points upwards
        # cast the first ray from the laser body
        translation = b2d.Vec2(
            math.cos(body_angle) * ray_length,
            math.sin(body_angle) * ray_length,
        )

        # query filter st. hits with the laser shape are ignored
        query_filter = b2d.query_filter(
            mask_bits=self.box_green_category_bits | self.box_blue_category_bits
        )

        def callback(shape, point, normal, fraction):
            # shape: the shape that was hit by the ray
            # point: the point of intersection
            # normal: the normal vector at the point of intersection
            # fraction: the fraction along the ray at which the intersection occurred
            #
            # the return value is a float that determines whether (and where) to continue the ray cast:
            #    -1 to filter,
            #    0 to terminate,
            #    fraction to clip the ray (for closest hit)
            #    1 to continue

            # blue or green box?
            if shape.filter.category_bits == self.box_green_category_bits:
                ret = 1  # continue the ray cast
                self.debug_draw.draw_segment(pos, point, color=(40, 240, 40))
                return 1  # continue the ray cast
            elif shape.filter.category_bits == self.box_blue_category_bits:
                self.debug_draw.draw_segment(pos, point, color=(40, 40, 240))
                #  clip the ray at a fraction of 0.2 (often one would just return "fraction" to
                #  clip the ray at the point of intersection, yet here
                #  we want to continue the ray cast but with a "weakended" ray
                return 0.2

            return ret

        self.world.cast_ray(pos, translation, query_filter=query_filter, callback=callback)


if __name__ == "__main__":
    CastRayCallback.run()
