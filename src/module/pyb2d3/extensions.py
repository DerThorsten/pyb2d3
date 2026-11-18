"""pyb2d3's own extensions on top of Box2D (not part of Box2D).

C++ helpers for things that need work on many objects every step and would be too slow in
python: particle emitters and a neighbor search. ::

    from pyb2d3 import extensions as ext

    nozzle = ext.RadialEmitter(world, b2d.shape_def(density=1), b2d.circle(radius=0.05),
                               rate=200, capacity=500, angle_min=-0.2, angle_max=0.2,
                               speed=ext.uniform(8, 10), lifetime=ext.normal(0.5, 0.1),
                               max_lifetime=1.0, body=lander, local_frame=nozzle_frame)
    impulse, angular_impulse = nozzle.step(dt)      # before world.step
    lander.apply_linear_impulse_to_center(impulse)  # thrust: the reaction of the particles

    i, j, delta, distance = bodies.neighbor_pairs(radius=1.0)  # all close pairs, each once
"""

import numpy as np

from ._pyb2d3 import Bodies
from ._pyb2d3 import extensions as _ext
from ._pyb2d3.extensions import (  # noqa: F401
    Distribution,
    Emitter,
    OnCapacityReached,
    constant,
    normal,
    uniform,
)

__all__ = [
    "Distribution",
    "Emitter",
    "LinearEmitter",
    "OnCapacityReached",
    "RadialEmitter",
    "constant",
    "neighbor_pairs",
    "normal",
    "uniform",
]


def neighbor_pairs(positions, radius):
    """All pairs of points closer than `radius`, each pair once (a pyb2d3 extension, not
    part of Box2D; C++, a grid of radius-sized cells: fast for thousands of points).

    `positions`: (n, 2) array-like. Returns `(i, j, delta, distance)`: index arrays with
    i < j, `delta = positions[j] - positions[i]` (n_pairs, 2) and its length.
    """
    positions = np.ascontiguousarray(positions, dtype=np.float64).reshape(-1, 2)
    return _ext._neighbor_pairs(positions, float(radius))


def _bodies_neighbor_pairs(self, radius):
    """All pairs of these bodies whose positions are closer than `radius`, each pair once:
    `(i, j, delta, distance)` with indices into this batch (see
    `pyb2d3.extensions.neighbor_pairs`)."""
    return neighbor_pairs(self.position, radius)


Bodies.neighbor_pairs = _bodies_neighbor_pairs


def _keyword_init(cls):
    """`cls(world, shape_def, geometry, *, body=None, body_def=None, seed=0, **settings)`:
    every other keyword is one of the emitter's properties (rate, capacity, speed, ...)"""

    class KeywordInit(cls):
        __doc__ = cls.__doc__

        def __init__(
            self, world, shape_def, geometry, *, body=None, body_def=None, seed=0, **settings
        ):
            super().__init__(world, shape_def, geometry, body, body_def, seed)
            for name, value in settings.items():
                if not hasattr(cls, name):
                    raise TypeError(f"{cls.__name__} has no setting {name!r}")
                setattr(self, name, value)

    KeywordInit.__name__ = KeywordInit.__qualname__ = cls.__name__
    KeywordInit.__module__ = __name__
    return KeywordInit


RadialEmitter = _keyword_init(_ext.RadialEmitter)
LinearEmitter = _keyword_init(_ext.LinearEmitter)
