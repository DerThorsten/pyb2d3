import pyb2d3 as b2d


def pinned(body_a, body_b, pivot_a, pivot_b=None, q_a=None, q_b=None):
    """Joint def fields connecting two bodies at world space pivots (with optional frame rotations)."""
    pivot_b = pivot_a if pivot_b is None else pivot_b
    return dict(
        body_a=body_a,
        body_b=body_b,
        local_frame_a=b2d.transform(p=body_a.local_point(pivot_a), q=q_a),
        local_frame_b=b2d.transform(p=body_b.local_point(pivot_b), q=q_b),
    )
