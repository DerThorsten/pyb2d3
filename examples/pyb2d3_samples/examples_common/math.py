import numpy as np


def truncated_vector_diff(vec_a, vec_b, max_length):
    """Returns the vector difference vec_b - vec_a, truncated to max_length."""

    diff = np.array(vec_b) - np.array(vec_a)
    length = np.linalg.norm(diff)
    if length > max_length:
        diff = (diff / length) * max_length
    return diff


def interpolate_color(color_a, color_b, t):
    """Interpolate between two colors given as (r, g, b) tuples with t in [0, 1]."""
    return (
        int(color_a[0] + (color_b[0] - color_a[0]) * t),
        int(color_a[1] + (color_b[1] - color_a[1]) * t),
        int(color_a[2] + (color_b[2] - color_a[2]) * t),
    )
