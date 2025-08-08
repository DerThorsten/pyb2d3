# pyb2d3
python bindings for Box2D 3


# Documentation

The documentation is avaialable at [derthorsten.github.io/pyb2d3](https://derthorsten.github.io/pyb2d3/).


# Installation

## pip
Install the python bindings with:
```bash
pip install pyb2d3
```



# conda based package

SOON!

# Building from Source

Note:
This may not work on windows!

Create the development environment with:
```bash
micromamba create -f dev-environment.yml
```

Activate the environment with:
```bash
micromamba activate pyb2d
```


Install the python bindings with:
```bash
pip install .
```

If you prefer to build the bindings with raw cmake, you can do so with.
This is particular usefull for iterative development since
the rebuild times are the fastest when building with raw cmake (instead
of using pip which relies on scikit-build-core to invoke cmake).

```bash
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX \
    -Dnanobind_DIR=$(python -m nanobind --cmake_dir)
make -j$(nproc)
```

For iterative development one needs to add
the source directory to the `PYTHONPATH` so that the python bindings can be imported.
That way, changes to the pure python code are immediately available without the need to rebuild the bindings.

```bash
PYTHONPATH=$(pwd)/src/module pytest
```

# Testbed

To install the testbed use:
```bash
python -m pip install "pkg @ git+https://git@github.com/derthorsten/pyb2d3.git#subdirectory=companion_packages/pyb2d3_sandbox"
```

The testbed needs a frontend to run.
There are several frontends available, e.g.:
- opengl-based:
```bash
python -m pip install "pkg @ git+https://git@github.com/derthorsten/pyb2d3.git#subdirectory=companion_packages/pyb2d3_sandbox_opengl"
```

- pygame-based
```bash
python -m pip install "pkg @ git+https://git@github.com/derthorsten/pyb2d3.git#subdirectory=companion_packages/pyb2d3_sandbox_opengl"
```

- ipycanvas-based
```bash
python -m pip install "pkg @ git+https://git@github.com/derthorsten/pyb2d3.git#subdirectory=companion_packages/pyb2d3_sandbox_ipycanvas"
```
