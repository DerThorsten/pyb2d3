"""Helpers shared by the ports of sample_continuous.cpp and sample_robustness.cpp."""

import pyb2d3 as b2d
from pyb2d3_sandbox import widgets


def attr_slider(sample, label, attr, min_value, max_value, step, on_change=None, cls=widgets.FloatSlider):
    """A slider bound to `sample.<attr>`; `on_change()` runs after every change."""

    def callback(value):
        setattr(sample, attr, value)
        if on_change is not None:
            on_change()

    return cls(
        label=label,
        min_value=min_value,
        max_value=max_value,
        step=step,
        value=getattr(sample, attr),
        callback=callback,
    )


def create_box_walls(body, shape_def, half_extent=10.0):
    """Four segments enclosing the square [-half_extent, half_extent]^2."""
    h = half_extent
    corners = [(-h, -h), (h, -h), (h, h), (-h, h)]
    for p1, p2 in zip(corners, corners[1:] + corners[:1]):
        body.create_shape(shape_def, b2d.segment(p1, p2))

