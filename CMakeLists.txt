cmake_minimum_required(VERSION 3.22)
project(bb2d)

find_package(box2d REQUIRED)

option(WITH_PYTHON_EXTENSION "Build python extension" ON)
option(WITH_PYTHON_TESTS "Build tests" ON)


if(WITH_PYTHON_EXTENSION)
    add_subdirectory(python)
endif()