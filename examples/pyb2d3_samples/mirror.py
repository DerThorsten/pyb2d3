# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


import random
import math


class Mirror(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, 0)))
        self.box_radius = 10

        # attach the chain shape to a static body
        self.box_body = self.world.create_static_body(position=(0, 0))
        chain_def = b2d.chain_box(center=(0, 0), hx=self.box_radius, hy=self.box_radius)
        chain_def.filter = b2d.make_filter(category_bits=0x0001, mask_bits=0x0001)
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
            ),
            b2d.box(hx=0.4, hy=1.0),
        )

        # n random boxes
        for _ in range(10):
            x = random.uniform(-self.box_radius, self.box_radius)
            y = random.uniform(-self.box_radius, self.box_radius)
            random_angle = random.uniform(0, 2 * math.pi)
            box_body = self.world.create_dynamic_body(
                position=(x, y),
                linear_damping=10.0,
                angular_damping=10.0,
                rotation=random_angle,
            )
            box_body.create_shape(
                b2d.shape_def(density=1, material=b2d.surface_material(restitution=0.5)),
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

    def pre_update(self, dt):
        if self.frontend.settings.headless:
            # to have some movement when running headless (ie for rendering a video of the sample)
            torque = 2
            self.laser_body.apply_torque(torque, wake=True)

        ray_length = self.box_radius * 2 * math.sqrt(2)
        ray_length = max(ray_length, 1)

        def draw_laser_line(start, end, reflection_count=0, color=(255, 40, 40)):
            self.debug_draw.draw_segment(start, end, color=(255, 40, 40))

        eps = 1e-5
        pos = self.laser_body.world_point((0, -(1 - eps)))
        body_angle = self.laser_body.angle + math.pi / 2  # laser points upwards
        # cast the first ray from the laser body
        translation = (
            math.cos(body_angle) * ray_length,
            math.sin(body_angle) * ray_length,
        )
        ray_result = self.world.cast_ray_closest(origin=pos, translation=translation)
        # by construction the ray should hit the box
        last_ray_result = ray_result

        if not ray_result.hit:
            return

        draw_laser_line(
            pos,
            ray_result.point,
        )

        for i in range(3):
            # NOTE: RayResult.normal seems to be broken for chain shapes therefore we use a pyb2d3 custom compute_normal function
            # which computes the normal "by hand" when RayResult.shape is a ChainSegmentShape
            normal = last_ray_result.compute_normal(translation)

            # reflect the translation vector
            translation = (normal[0] * ray_length, normal[1] * ray_length)
            # cast the reflected ray
            ray_result = self.world.cast_ray_closest(
                origin=last_ray_result.point, translation=translation
            )

            if ray_result.hit:
                draw_laser_line(
                    last_ray_result.point,
                    ray_result.point,
                    reflection_count=i + 1,
                )
                body_angle += math.pi
            last_ray_result = ray_result


if __name__ == "__main__":
    Mirror.run()
