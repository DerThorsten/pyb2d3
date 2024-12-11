cmake_minimum_required(VERSION 3.22)
project(pyb2d)

find_package(box2d REQUIRED)

option(WITH_PYTHON_EXTENSION "Build python extension" ON)
option(WITH_PYTHON_TESTS "Build tests" ON)
option(WITH_PYB2D_PLAYGROUND "Build pyb2d_playground" ON)
option(BUILD_SHARED_PYB2D_PLAYGROUND "Build shared library for pyb2d_playground" OFF)

if(WITH_PYTHON_EXTENSION)
    add_subdirectory(python)
endif()

add_subdirectory(samples)

if(WITH_PYB2D_PLAYGROUND)
    # create a shared library for pyb2d_playground
    SET(PYB2D_PLAYGROUND_SRC
        src/pyb2d_playground/frontend/frontend_base.cpp
    )
    if(BUILD_SHARED_PYB2D_PLAYGROUND)
        add_library(pyb2d_playground SHARED ${PYB2D_PLAYGROUND_SRC})
    else()
        add_library(pyb2d_playground STATIC ${PYB2D_PLAYGROUND_SRC})
    endif()

    # include directories
    target_include_directories(pyb2d_playground PRIVATE include)
endif()