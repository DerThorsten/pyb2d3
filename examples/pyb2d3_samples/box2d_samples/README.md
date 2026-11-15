# Box2D samples, ported to Python

The samples in this directory are Python ports of the C++ samples of Box2D's own
sample browser: <https://github.com/erincatto/box2d/tree/v3.2.0/samples>.

- one module per C++ file: `bodies.py` is `sample_bodies.cpp`, `joints.py` is
  `sample_joints.cpp`, ...
- the samples register themselves under Box2D's category names (Bodies, Joints,
  Shapes, Stacking, Events, Collision, ...), so the sandbox groups them like Box2D's
  sample browser
- `_*_helpers.py` / `_common.py`: helpers of the C++ samples (shared code of the
  `sample_*.cpp` files) ported along with them

They follow the C++ code closely (names, numbers, structure), which makes it easy to
compare them with the originals; the samples outside this directory are pyb2d3's own.

Box2D and its samples are Copyright (c) 2022 Erin Catto, MIT license: see
[LICENSE](LICENSE).
