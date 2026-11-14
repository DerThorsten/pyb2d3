"""Helpers shared by the batch API samples (batch_*.py)."""

import numpy as np

import pyb2d3 as b2d


def hsv_colors(hue, saturation=0.75, value=0.95):
    """Vectorized HSV -> 0xRRGGBB colors (hue in [0, 1))."""
    hue = np.asarray(hue, dtype=np.float64) % 1.0
    saturation = np.broadcast_to(saturation, hue.shape)
    value = np.broadcast_to(value, hue.shape)
    sector = np.floor(hue * 6.0).astype(int) % 6
    f = hue * 6.0 - np.floor(hue * 6.0)
    p = value * (1.0 - saturation)
    q = value * (1.0 - f * saturation)
    t = value * (1.0 - (1.0 - f) * saturation)
    r = np.choose(sector, [value, q, p, p, t, value])
    g = np.choose(sector, [t, value, value, q, p, p])
    b = np.choose(sector, [p, p, t, value, value, q])
    rgb = (np.stack([r, g, b], axis=-1) * 255).round().astype(np.uint32)
    return (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]


def create_circles(world, positions, radius, colors=None, density=1.0, friction=0.2, restitution=0.0, **body_kwargs):
    """One dynamic circle body per row of `positions`, returned as a `b2d.Bodies` batch.

    `radius` and `colors` are a single value or one value per body. Creating bodies is
    the one thing the batch API cannot do: it is a python loop, but only once.
    """
    n = len(positions)
    radii = np.broadcast_to(np.asarray(radius, dtype=np.float64), (n,))
    colors = np.broadcast_to(np.asarray(0 if colors is None else colors, dtype=np.uint32), (n,))
    bodies = b2d.Bodies()
    for (x, y), r, color in zip(positions, radii, colors):
        body = world.create_dynamic_body(position=(float(x), float(y)), **body_kwargs)
        material = b2d.surface_material(friction=friction, restitution=restitution, custom_color=int(color))
        body.create_shape(b2d.shape_def(density=density, material=material), b2d.circle(radius=float(r)))
        bodies.append(body)
    return bodies


def destroy_bodies(sample, bodies):
    """Destroy every body of a batch (there is no batch version of destroy)."""
    sample.destroy_mouse_joint()
    for body in bodies:
        body.destroy()


def unit_and_length(vectors, eps=1e-6):
    """Row-wise unit vectors and lengths of an (n, 2) array."""
    length = np.linalg.norm(vectors, axis=1)
    return vectors / np.maximum(length, eps)[:, None], length


def perpendicular(vectors):
    """Rotate every row of an (n, 2) array by +90 degrees."""
    return np.stack([-vectors[:, 1], vectors[:, 0]], axis=1)


class Ema:
    """Exponential moving average, for timings shown on screen."""

    def __init__(self, alpha=0.1):
        self.alpha = alpha
        self.value = None

    def __call__(self, sample):
        self.value = sample if self.value is None else (1.0 - self.alpha) * self.value + self.alpha * sample
        return self.value
