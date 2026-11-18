import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, get_extra_options, register_sample, widgets
from .examples_common.font import (
    FONTS,
    create_blocks,
    create_letters,
    create_soft_letters,
    text_blocks,
    text_size,
    wrap_text,
)

STYLES = ["balls", "squares", "rigid letters", "soft letters"]


@register_sample("Demos", "Text", video=True)
class Text(SampleBase):
    """A message in a pixel font: loose balls / squares, rigid or soft letters
    (springs between the blocks); "blocks per pixel" refines each font pixel.
    "rebuild" starts over with the current settings.

    Mouse: drag the letters around.
    """

    half = 15.0  # half size of the box (m)

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.text = get_extra_options().get("text", "pyb2d3")
        self.font = "5x7"
        self.style = "soft letters"
        self.subdivision = 2
        # spring hertz of the soft letters (higher: the over-constrained letters get unstable)
        self.stiffness = 1.0
        self.randomness = 0.025  # jitter of the block positions (in block sizes)
        self.rng = np.random.default_rng()
        self.bodies = b2d.Bodies()
        self.debug_draw.draw_joints = False  # thousands of springs: just the blocks
        self.world.create_static_body().create_chain(
            b2d.chain_box(center=(0, 0), hx=self.half, hy=self.half)
        )
        self.build()
        for widget in (
            widgets.TextInput("text", self.text, self.set_text),
            widgets.RadioButtons("font", list(FONTS), self.font, self.set_font),
            widgets.RadioButtons("style", STYLES, self.style, self.set_style),
            widgets.IntSlider("blocks per pixel", 1, 3, 1, self.subdivision, self.set_subdivision),
            widgets.FloatSlider(
                "stiffness (soft)", 0.5, 10.0, 0.5, self.stiffness, self.set_stiffness
            ),
            widgets.FloatSlider(
                "randomness", 0.0, 0.2, 0.005, self.randomness, self.set_randomness
            ),
            widgets.Button("rebuild", self.build),
        ):
            self.frontend.add_widget(widget)

    def build(self):
        """the text, as large as fits the box, in its upper part"""
        self.bodies.destroy()  # destroys their springs too
        self.springs = []
        text = wrap_text(self.text, 20)
        columns, rows = text_size(text, self.font)
        pixel = min(1.8 * self.half / max(columns, 1), 0.9 * self.half / max(rows, 1))
        # the first line is at y = 0..height above the origin, later lines go down
        origin = (-0.5 * columns * pixel, self.half - 1.0 - FONTS[self.font].height * pixel)
        cells, letters = text_blocks(text, self.font, self.subdivision)
        if self.randomness > 0:
            cells = cells + self.rng.uniform(-self.randomness, self.randomness, cells.shape)
        size, color = pixel / self.subdivision, b2d.HexColor.Gold
        if self.style == "rigid letters":
            self.bodies = create_letters(self.world, cells, letters, origin, size, color)
        elif self.style == "soft letters":
            # springs between all blocks up to 4 font pixels apart (nearly all pairs of a
            # letter, but bounded for fine blocks / long texts)
            self.bodies, self.springs = create_soft_letters(
                self.world,
                cells,
                letters,
                origin,
                size,
                hertz=self.stiffness,
                damping_ratio=0.7,
                reach=4 * self.subdivision,
                colors=color,
            )
        else:
            shape = "ball" if self.style == "balls" else "square"
            self.bodies = create_blocks(self.world, cells, origin, size, shape, color)

    def set_text(self, value):
        """text field: the message"""
        self.text = value
        self.build()

    def set_font(self, value):
        """radio buttons: the pixel font"""
        self.font = value
        self.build()

    def set_style(self, value):
        """radio buttons: how the blocks are made / connected"""
        self.style = value
        self.build()

    def set_subdivision(self, value):
        """slider: blocks per font pixel (n x n)"""
        self.subdivision = int(value)
        self.build()

    def set_stiffness(self, value):
        """slider: spring frequency (Hz) of the soft letters, changed in place"""
        self.stiffness = float(value)
        for spring in self.springs:
            spring.spring_hertz = self.stiffness

    def set_randomness(self, value):
        """slider: random offsets of the blocks (0: exactly on the grid)"""
        self.randomness = float(value)
        self.build()

    def aabb(self):
        return b2d.aabb(lower_bound=(-self.half, -self.half), upper_bound=(self.half, self.half))
