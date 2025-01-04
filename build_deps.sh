#!/bin/bash
set -e

# create a directory to store the dependencies
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
mkdir -p $DIR/dependencies
cd $DIR/dependencies


# download and build enkiTS
OWNER=dougbinks
REPO=enkiTS
VERSION=1.11
URL=https://github.com/${OWNER}/${REPO}/archive/refs/tags/v${VERSION}.tar.gz
rm -rf enkiTS
curl -L ${URL} | tar zx
mv ${REPO}-${VERSION} enkiTS
pushd enkiTS
mkdir -p build
pushd build
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DENKITS_INSTALL=ON \
    -DCMAKE_INSTALL_PREFIX=${CONDA_PREFIX}

cmake --build . --config Release --target install
popd
popd


# download and build box2d
OWNER=DerThorsten
REPO=box2d
COMMIT=30c080e56efd13ef5aa8872db63d95b816ca23e0
URL=https://github.com/${OWNER}/${REPO}/archive/${COMMIT}.tar.gz
rm -rf box2d
curl -L ${URL} |    tar zx
mv ${REPO}-${COMMIT} box2d
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
    -DBOX2D_UNIT_TESTS=OFF

cmake --build . --config Release --target install
popd
popd
