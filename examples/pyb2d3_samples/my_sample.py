"""A (nearly) empty sample to start your own: edit it and run it.

In the browser sandbox: open the code pane ("</> Code"), change this file and press
Run (Ctrl/Cmd+Enter). The edits live in the page only (a reload restores this file).
"""

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets  # noqa: F401  (widgets: see below)


# register_sample(category, name) puts the sample into the sample browser
@register_sample("Playground", "My Sample")
class MySample(SampleBase):
    """Your own sample: a ground, a few boxes and a bouncy ball.

    Edit: open the code pane (</> Code), change my_sample.py, Run restarts it.
    The commented hooks at the end of the file are examples to start from.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)  # creates self.world

        # the ground: a static body never moves
        ground = self.world.create_static_body(position=(0, -1))
        ground.create_shape(b2d.shape_def(), b2d.box(20, 1))

        # a staircase of dynamic boxes: bodies with a density fall and collide
        for i in range(5):
            box = self.world.create_dynamic_body(position=(-4 + 2 * i, 2 + i))
            box.create_shape(b2d.shape_def(density=1), b2d.box(0.5, 0.5))

        # a ball; restitution makes it bounce
        ball = self.world.create_dynamic_body(position=(0, 10))
        bouncy = b2d.surface_material(restitution=0.6)
        ball.create_shape(b2d.shape_def(density=1, material=bouncy), b2d.circle(radius=0.7))

        # a slider in the sample's panel (uncomment set_gravity_y below too):
        # self.frontend.add_widget(widgets.FloatSlider("gravity", -20, 0, 0.5, -10, self.set_gravity_y))

    def aabb(self):
        """the region of the world the frontend shows"""
        return b2d.aabb(lower_bound=(-15, -2), upper_bound=(15, 15))

    # Hooks: uncomment and change.
    # def set_gravity_y(self, value):
    #     """slider callback"""
    #     self.world.gravity = (0, value)

    # def pre_update(self, dt):
    #     """called before each world step: apply forces, move kinematic bodies, ..."""

    # def post_debug_draw(self):
    #     """draw extra things on top of the world"""
    #     self.debug_draw.draw_string((-14, 14), "hello pyb2d3", b2d.HexColor.White)

    # def on_key_down(self, event):
    #     """keys: event.key is "a".."z", "0".."9", "space", "left", ..."""
    #     if event.key == "space":
    #         body = self.world.create_dynamic_body(position=(0, 12))
    #         body.create_shape(b2d.shape_def(density=1), b2d.circle(radius=0.5))

    # def on_double_click(self, event):
    #     """mouse: event.world_position is the clicked point in world coordinates"""
    #     self.world.explode(position=event.world_position, radius=5, impulse_per_length=10)
