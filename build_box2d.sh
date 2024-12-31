#!/bin/bash

# this dir
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#  try to remove the old build
rm -rf $DIR/deps/box2d

mkdir -p $DIR/deps/box2d &&
cd $DIR/deps &&
curl -L -o box2d-commit.tar.gz https://github.com/erincatto/box2d/archive/f377034920c42a26cd498c0a0b1b2e9f2b064989.tar.gz &&
tar --strip-components=1 -xvzf box2d-commit.tar.gz -C box2d &&
cd box2d &&
patch  -p1 -i ../box2d_patches/conditional_disable_cxx_operators.patch

cd $DIR


cmake -S deps/box2d -B $DIR/deps/box2d/build \
    -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX \
    -DCMAKE_INSTALL_LIBDIR=$CONDA_PREFIX/lib \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON \
    -DBOX2D_UNIT_TESTS=OFF \
    -DBOX2D_BENCHMARKS=OFF \
    -DBOX2D_SAMPLES=OFF

cmake --build $DIR/deps/box2d/build \
      --config Release --target install
