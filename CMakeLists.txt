cmake_minimum_required(VERSION 3.22)
project(pyb2d)

find_package(box2d REQUIRED)

option(WITH_PYTHON_EXTENSION "Build python extension" ON)
option(WITH_PYTHON_TESTS "Build tests" ON)
option(WITH_PYB2D_PLAYGROUND "Build pyb2d_playground" ON)
option(BUILD_SHARED_PYB2D_PLAYGROUND "Build shared library for pyb2d_playground" OFF)


add_subdirectory(python)

