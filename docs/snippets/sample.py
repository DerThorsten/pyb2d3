import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, run_sample_browser


@register_sample("My Samples", "Falling Boxes")
class FallingBoxes(SampleBase):
    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)  # creates self.world
        ground = self.world.create_static_body(position=(0, -1))
        ground.create_shape(b2d.shape_def(), b2d.box(10, 1))
        for i in range(10):
            body = self.world.create_dynamic_body(position=(0, 1 + 1.1 * i))
            body.create_shape(b2d.shape_def(), b2d.box(0.5, 0.5))

    def aabb(self):
        # the region the frontend should show
        return b2d.aabb((-10, -2), (10, 15))


if __name__ == "__main__":
    # browse all registered samples, starting with this one
    run_sample_browser(start="My Samples/Falling Boxes")
