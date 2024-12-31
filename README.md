# pyb2d
python bindings for Box2D.


# badges
[![pixi](https://github.com/DerThorsten/bb2d/actions/workflows/pixi.yml/badge.svg)](https://github.com/DerThorsten/bb2d/actions/workflows/pixi.yml)
[![micromamba](https://github.com/DerThorsten/bb2d/actions/workflows/mm.yaml/badge.svg)](https://github.com/DerThorsten/bb2d/actions/workflows/mm.yaml)
[![raw-cmake](https://github.com/DerThorsten/bb2d/actions/workflows/raw-cmake.yaml/badge.svg)](https://github.com/DerThorsten/bb2d/actions/workflows/raw-cmake.yaml)

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

Run the script to dowload and patch build
and install box2d:ß
```bash
./build_box2d.sh
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


## Pixi

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
## With Pixi
Run the tests with:
```bash
pixi run test
```
## micromamba + uv / pip
Run the tests with:
```bash
pytest
```

## raw cmake
Run the tests with:
```bash
PYTHONPATH=$(pwd)/src pytest
```
