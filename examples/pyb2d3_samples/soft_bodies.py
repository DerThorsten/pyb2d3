"""A soft body: a grid of balls held together by springs."""

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, register_sample, widgets

BOX = 10  # half size of the box (m)
GRID = 4  # GRID x GRID balls
SPACING = 2  # distance between neighboring balls (m)
HERTZ = 5.0
DAMPING_RATIO = 0.0


@register_sample("Demos", "Soft Bodies", video=True)
class SoftBodies(SampleBase):
    """A soft body: a 4 x 4 grid of balls linked by spring distance joints.
    Sliders: spring hertz (low: very wobbly) and damping.
    Mouse: drag a ball; double click explodes, triple click pulls in.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=BOX, hy=BOX))
        self.create_soft_body()
        self.frontend.add_widget(
            widgets.FloatSlider("Hertz", 0.1, 10.0, 0.1, HERTZ, self.set_hertz)
        )
        self.frontend.add_widget(
            widgets.FloatSlider("Damping", 0.0, 1.0, 0.01, DAMPING_RATIO, self.set_damping)
        )

    def create_soft_body(self):
        """the balls, and springs to the right, upper and both diagonal neighbors"""
        balls = {}
        for i in range(GRID):
            for j in range(GRID):
                ball = self.world.create_dynamic_body(
                    position=(i * SPACING, j * SPACING),
                    linear_damping=0.1,
                    fixed_rotation=True,
                )
                material = b2d.surface_material(
                    restitution=0.5, custom_color=b2d.random_hex_color()
                )
                ball.create_shape(
                    b2d.shape_def(density=1, material=material), b2d.circle(radius=0.5)
                )
                balls[i, j] = ball

        self.springs = []
        for (i, j), ball in balls.items():
            for neighbor in [(i + 1, j), (i, j + 1), (i + 1, j + 1), (i - 1, j + 1)]:
                if neighbor not in balls:
                    continue
                other = balls[neighbor]
                spring = self.world.create_distance_joint(
                    body_a=ball,
                    body_b=other,
                    length=(other.position - ball.position).length(),  # relaxed at the start
                    enable_spring=True,
                    hertz=HERTZ,
                    damping_ratio=DAMPING_RATIO,
                )
                self.springs.append(spring)

    def set_hertz(self, value):
        for spring in self.springs:
            spring.spring_hertz = value
        self.wake_up()

    def set_damping(self, value):
        for spring in self.springs:
            spring.spring_damping_ratio = value
        self.wake_up()

    def wake_up(self):
        """a sleeping body would not notice the changed springs"""
        for spring in self.springs:
            spring.body_a.awake = True
            spring.body_b.awake = True

    def on_double_click(self, event):
        self.world.explode(position=event.world_position, radius=7, impulse_per_length=20)

    def on_triple_click(self, event):
        # a negative impulse pulls the bodies towards the click
        self.world.explode(position=event.world_position, radius=7, impulse_per_length=-20)

    def aabb(self):
        r = BOX + 0.01
        return b2d.aabb(lower_bound=(-r, -r), upper_bound=(r, r))
