"""A message written in a pixel font, made of balls, squares, rigid or soft letters."""

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

BOX = 15.0  # half size of the box (m)
STYLES = ["balls", "squares", "rigid letters", "soft letters"]
COLOR = b2d.HexColor.Gold
LINE_LENGTH = 20  # characters; longer lines are wrapped


@register_sample("Demos", "Text", video=True)
class Text(SampleBase):
    """A message in a pixel font: loose balls / squares, rigid or soft letters
    (springs between the blocks); "blocks per pixel" refines each font pixel.
    "rebuild" starts over with the current settings.

    Mouse: drag the letters around.
    """

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.text = get_extra_options().get("text", "pyb2d3")
        self.font = "5x7"
        self.style = "soft letters"
        self.subdivision = 2  # blocks per font pixel (n x n)
        # spring hertz of the soft letters (higher: the over-constrained letters get unstable)
        self.stiffness = 1.0
        self.randomness = 0.025  # jitter of the block positions (in block sizes)
        self.bodies = b2d.Bodies()
        self.springs = []
        self.debug_draw.draw_joints = False  # thousands of springs: just draw the blocks

        self.anchor_body.create_chain(b2d.chain_box(center=(0, 0), hx=BOX, hy=BOX))
        self.build()
        self.add_widgets()

    def add_widgets(self):
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
        """(re)create the text, as large as fits the box, in its upper part"""
        self.bodies.destroy()  # destroys their springs too
        self.springs = []

        text = wrap_text(self.text, LINE_LENGTH)
        columns, rows = text_size(text, self.font)
        pixel = min(1.8 * BOX / max(columns, 1), 0.9 * BOX / max(rows, 1))  # font pixel (m)
        size = pixel / self.subdivision  # block (m)
        # the first line is at y = 0..height above the origin, later lines go down
        origin = (-0.5 * columns * pixel, BOX - 1.0 - FONTS[self.font].height * pixel)

        cells, letters = text_blocks(text, self.font, self.subdivision)
        cells = cells + np.random.uniform(-self.randomness, self.randomness, cells.shape)

        if self.style == "balls":
            self.bodies = create_blocks(self.world, cells, origin, size, "ball", COLOR)
        elif self.style == "squares":
            self.bodies = create_blocks(self.world, cells, origin, size, "square", COLOR)
        elif self.style == "rigid letters":
            self.bodies = create_letters(self.world, cells, letters, origin, size, COLOR)
        else:
            # springs between all blocks of a letter up to 4 font pixels apart (nearly
            # all pairs, but bounded for fine blocks / long texts)
            self.bodies, self.springs = create_soft_letters(
                self.world,
                cells,
                letters,
                origin,
                size,
                hertz=self.stiffness,
                damping_ratio=0.7,
                reach=4 * self.subdivision,
                colors=COLOR,
            )

    def set_text(self, value):
        self.text = value
        self.build()

    def set_font(self, value):
        self.font = value
        self.build()

    def set_style(self, value):
        self.style = value
        self.build()

    def set_subdivision(self, value):
        self.subdivision = int(value)
        self.build()

    def set_stiffness(self, value):
        """changes the springs in place, no rebuild"""
        self.stiffness = float(value)
        for spring in self.springs:
            spring.spring_hertz = self.stiffness

    def set_randomness(self, value):
        self.randomness = float(value)
        self.build()

    def aabb(self):
        return b2d.aabb(lower_bound=(-BOX, -BOX), upper_bound=(BOX, BOX))
