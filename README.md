# pyb2d3
python bindings for Box2D 3


# badges
[![pixi](https://github.com/DerThorsten/pyb2d3/actions/workflows/pixi.yml/badge.svg)](https://github.com/DerThorsten/pyb2d3/actions/workflows/pixi.yml)
[![micromamba](https://github.com/DerThorsten/pyb2d3/actions/workflows/mm.yaml/badge.svg)](https://github.com/DerThorsten/pyb2d3/actions/workflows/mm.yaml)
[![raw-cmake](https://github.com/DerThorsten/pyb2d3/actions/workflows/raw-cmake.yaml/badge.svg)](https://github.com/DerThorsten/pyb2d3/actions/workflows/raw-cmake.yaml)

# Building
This may not work on windows!

## micromamba + uv / pip

Create the development environment with:
```bash
micromamba create -f dev-environment.yml
```

Activate the environment with:
```bash
micromamba activate pyb2d
```

### pip

Install the python bindings with:
```bash
pip install .
```
### uv

```bash
uv pip install .
```


### raw cmake

```bash
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX \
    -Dnanobind_DIR=$(python -m nanobind --cmake_dir)
make -j$(nproc)
```


# Testing
## micromamba + uv / pip
Run the tests with:
```bash
pytest
```

## raw cmake
Run the tests with:
```bash
PYTHONPATH=$(pwd)/src/module pytest
```
