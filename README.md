# pyb2d3

Python bindings for [Box2D](https://box2d.org) v3.2, the 2D physics engine.

- the complete public Box2D API, typed and Pythonic
- a numpy batch API to simulate and read out thousands of bodies with a few calls
- snapshots, recording and deterministic replay
- a sandbox with OpenGL and pygame frontends and ~140 interactive samples, including ports of
  Box2D's own sample browser

```python
import pyb2d3 as b2d

world = b2d.World(gravity=(0, -10))
ground = world.create_static_body(position=(0, -1))
ground.create_shape(b2d.shape_def(), b2d.box(50, 1))

body = world.create_dynamic_body(position=(0, 4))
body.create_shape(b2d.shape_def(density=1), b2d.box(0.5, 0.5))

for _ in range(60):
    world.step(1 / 60, 4)
print(body.position)
```

## Documentation

[derthorsten.github.io/pyb2d3](https://derthorsten.github.io/pyb2d3/)

## Installation

```bash
pip install pyb2d3
# or
conda install -c conda-forge pyb2d3
```

## Sandbox and samples

The sandbox, its frontends and the samples live in `examples/` (they are not packages).
With [pixi](https://pixi.sh), from a checkout:

```bash
pixi run sandbox                    # OpenGL frontend, samples grouped by category
pixi run sandbox "Joints/Ragdoll"   # start at a sample
pixi run sandbox-pygame             # pygame frontend
```

## Development

Everything is a pixi task (`pixi.toml`):

```bash
pixi run build        # build the extension in place
pixi run test         # build + tests
pixi run install      # build with pip and install into the pixi environment
pixi run test-installed  # install + tests against the installed package
pixi run wheel        # build a wheel with pip into dist/
pixi run docs-quick   # docs without the sample videos (docs/_build/html)
pixi run docs         # docs with the sample videos
pixi run docs-serve   # serve the built docs and open them in the browser
pixi run smoke-opengl # every sample a few frames in the OpenGL frontend (needs a display)
pixi run emscripten   # emscripten-forge package
```

See the [developer guide](https://derthorsten.github.io/pyb2d3/src/developer.html) for the
architecture of the bindings.
