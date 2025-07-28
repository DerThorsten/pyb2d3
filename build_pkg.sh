#!/bin/bash


set -e





DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYB2D3_SRC_DIR=$DIR
BUILD_TYPE=Release

if true; then

    pushd $PYB2D3_SRC_DIR
    mkdir -p build
    pushd build

    cmake .. \
        -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX \
        -DCMAKE_BUILD_TYPE=$BUILD_TYPE \
        -DFETCH_BOX2D=OFF \
        -Dnanobind_DIR=$(python -m nanobind --cmake_dir)\
        -DPYB2D_LINK_NANOBIND_STATICALLY=OFF

    make -j$(nproc)
    popd

    # PYTHONPATH="$PYTHONPATH:$PYB2D3_SRC_DIR/src/module" pytest

    # PYTHONPATH="$PYTHONPATH:$PYB2D3_SRC_DIR/src/module" pytest benchmark

    popd

fi
