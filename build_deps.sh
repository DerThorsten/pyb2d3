#!/bin/bash
set -e

# create a directory to store the dependencies
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
mkdir -p $DIR/dependencies
cd $DIR/dependencies


# download and build enkiTS
OWNER=dougbinks
REPO=enkiTS
COMMIT=686d0ec31829e0d9e5edf9ceb68c40f9b9b20ea9
URL=https://github.com/${OWNER}/${REPO}/archive/${COMMIT}.tar.gz
rm -rf enkiTS
curl -L ${URL} | tar zx
mv ${REPO}-${COMMIT} enkiTS
pushd enkiTS
mkdir -p build
pushd build
cmake .. \
    -DCMAKE_INSTALL_PREFIX=${CONDA_PREFIX} \
    -DCMAKE_BUILD_TYPE=Release \
    -DENKITS_INSTALL=ON \
    -DENKITS_BUILD_C_INTERFACE=ON \
    -DENKITS_BUILD_EXAMPLES=OFF \
    -DENKITS_BUILD_SHARED=ON

cmake --build . --config Release --target install
popd
popd


# download and build box2d
# OWNER=erincatto
# REPO=box2d
# COMMIT=30c080e56efd13ef5aa8872db63d95b816ca23e0
# URL=https://github.com/${OWNER}/${REPO}/archive/${COMMIT}.tar.gz

URL=https://github.com/erincatto/box2d/archive/refs/tags/v3.1.0.tar.gz


# rror: '*(float *)((char *)&localPointB + offsetof(b2Vec2, y))' may be used uninitialized [-Werror=maybe-uninitialized]
#  275 |         float dy = b.y - a.y;
# -Wno-error=maybe-uninitialized


rm -rf box2d
curl -L ${URL} |    tar zx
mv box2d-3.1.0 box2d
pushd box2d
mkdir -p build
pushd build
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=${CONDA_PREFIX} \
    -DCMAKE_INSTALL_LIBDIR=${CONDA_PREFIX}/lib \
    -DBOX2D_SAMPLES=OFF \
    -DBOX2D_BENCHMARKS=OFF \
    -DBOX2D_DOCS=OFF \
    -DBOX2D_PROFILE=OFF \
    -DBOX2D_VALIDATE=ON \
    -DBOX2D_UNIT_TESTS=OFF \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_CXX_FLAGS="-Wno-maybe-uninitialized"

cmake --build . --config Release --target install
popd
popd
