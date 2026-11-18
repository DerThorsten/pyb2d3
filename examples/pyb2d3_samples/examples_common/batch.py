"""Helpers shared by the batch API samples (batch_*.py)."""

import numpy as np


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


def pair_sum(n, i, j, values):
    """Per-body sums of pairwise (n_pairs, 2) `values`: + on body i, - on body j
    (equal and opposite forces)."""
    out = np.zeros((n, 2))
    for axis in range(2):
        out[:, axis] = np.bincount(i, values[:, axis], n) - np.bincount(j, values[:, axis], n)
    return out
