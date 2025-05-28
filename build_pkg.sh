#!/bin/bash


set -e





DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYB2D_SRC_DIR=$DIR
PYB2D_PLAYGROUND_SRC_DIR=$DIR/playground
BUILD_TYPE=Release

if true; then

    pushd $PYB2D_SRC_DIR
    mkdir -p build
    pushd build

    cmake .. \
        -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX \
        -DCMAKE_BUILD_TYPE=$BUILD_TYPE \
        -Dnanobind_DIR=$(python -m nanobind --cmake_dir)

    make -j$(nproc)
    popd

    PYTHONPATH="$PYTHONPATH:$PYB2D_SRC_DIR/src/module" pytest

    popd

fi


PYTHONPATH="$PYTHONPATH:$PYB2D_SRC_DIR/src/module"
PYTHONPATH="$PYTHONPATH:$PYB2D_PLAYGROUND_SRC_DIR/src/module"
