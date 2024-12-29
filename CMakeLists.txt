cmake_minimum_required(VERSION 3.22)
project(${SKBUILD_PROJECT_NAME})

find_package(box2d REQUIRED)

# add compile definitions
add_compile_definitions(B2_DISABLE_CXX_OPERATORS)

option(WITH_PYTHON_EXTENSION "Build python extension" ON)
option(WITH_PYTHON_TESTS "Build tests" OFF)
option(WITH_PYB2D_PLAYGROUND "Build pyb2d_playground" OFF)
option(BUILD_SHARED_PYB2D_PLAYGROUND "Build shared library for pyb2d_playground" OFF)


add_subdirectory(src)

