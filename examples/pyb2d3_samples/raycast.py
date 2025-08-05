# +
import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase


import random
import math


class Raycast(SampleBase):
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

        # a ball
        self.ball_body = self.world.create_dynamic_body(
            position=(0, 0), linear_damping=10, angular_damping=10.0
        )
        self.ball_body.create_shape(
            b2d.shape_def(density=1, material=b2d.surface_material(restitution=0.5)),
            b2d.circle(radius=1),
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

    def post_debug_draw(self):
        # to get some action for the headless frontend
        # where we dont get mouse inputs
        # (this is usefull when rendering videos for the docs)
        if self.frontend.settings.headless:
            self.ball_body.apply_force_to_center((40, -40), wake=True)

        pos = self.ball_body.position
        body_angle = self.ball_body.angle
        # print(f"Ball position: {pos}")

        # cast N radidal rays from the ball position
        n_rays = 100
        ray_length = self.box_radius * 2 * math.sqrt(2)
        for i in range(n_rays):
            angle = body_angle + 2 * math.pi * i / n_rays
            translation = (math.cos(angle) * ray_length, math.sin(angle) * ray_length)
            ray_result = self.world.cast_ray_closest(origin=pos, translation=translation)
            # move start in translation direction by radius
            start = b2d.Vec2(pos) + b2d.Vec2(translation).normalize()

            if ray_result.hit:
                self.debug_draw.draw_segment(
                    b2d.Vec2(start), ray_result.point, color=(255, 255, 125)
                )


if __name__ == "__main__":
    Raycast.run()
