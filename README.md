# pyb2d
python bindings for Box2D.


# Building

Since box2d 3 is not yet published on conda-forge, we build it from source.
Furthermore we apply a patch.
This command should only be run once.
```bash
pixi run build-box2d
```

To build and install the python bindings, run:
```bash
pixi run install .
```

# Testing
Run the tests with:
```bash
pixi run test
```
