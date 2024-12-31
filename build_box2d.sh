#!/bin/bash

# exit on error
set -e

# get the first argument: its either SHARED or STATIC
# if not provided, we default to SHARED
BUILD_TYPE=$1
if [ -z "$BUILD_TYPE" ]; then
    BUILD_TYPE=SHARED
fi

BUILD_SHARED_LIBS=ON
if [ "$BUILD_TYPE" == "STATIC" ]; then
    BUILD_SHARED_LIBS=OFF
fi

echo "Building Box2D as $BUILD_TYPE"


# this dir
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

COMMIT_HASH=f377034920c42a26cd498c0a0b1b2e9f2b064989

#  try to remove the old build
rm -rf $DIR/deps/box2d/
mkdir -p $DIR/deps/box2d/build

cd $DIR/deps
curl -L -o box2d-commit.tar.gz \
    https://github.com/erincatto/box2d/archive/$COMMIT_HASH.tar.gz

# extract the archive
tar --strip-components=1 -xvzf box2d-commit.tar.gz -C box2d

# apply patches
cd box2d
patch  -p1 -i ../box2d_patches/conditional_disable_cxx_operators.patch


cmake -S . -B build \
    -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX \
    -DCMAKE_INSTALL_LIBDIR=$CONDA_PREFIX/lib \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=$BUILD_SHARED_LIBS \
    -DBOX2D_UNIT_TESTS=OFF \
    -DBOX2D_BENCHMARKS=OFF \
    -DBOX2D_SAMPLES=OFF

cmake --build build \
      --config Release --target install
