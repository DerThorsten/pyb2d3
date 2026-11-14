cmake_minimum_required(VERSION 3.22)
project(pyb2d)
include(FetchContent)

# compile_commands.json for clangd / IDEs
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)


OPTION(BUILD_SHARED_LIBS "Build shared libraries" OFF)
OPTION(PYB2D3_NO_THREADING "Disable threading support" OFF)
OPTION(PYB2D3_BATCH_API "Build the numpy batch API (Bodies, Shapes, ...)" ON)


# this is only relevant if we are building box2d
# (ie if FETCH_BOX2D is ON)
OPTION(FETCH_BOX2D          "Download/Fetch Box2D" ON)
option(BUILD_SHARED_LIBS    "Build using shared libraries" OFF)

if(FETCH_BOX2D)
    set(CMAKE_POSITION_INDEPENDENT_CODE ON)
    FetchContent_Declare(
        box2d
        GIT_REPOSITORY https://github.com/erincatto/box2d.git
        GIT_TAG v3.2.0
        GIT_SHALLOW TRUE
        GIT_PROGRESS TRUE
    )
    FetchContent_MakeAvailable(box2d)
else()
    find_package(box2d REQUIRED)
endif()


if(DEFINED SKBUILD)
    SET(CMAKE_INSTALL_LIBDIR ${SKBUILD_PROJECT_NAME}/lib)
else()
    SET(INSTALL_DIR  ${CMAKE_INSTALL_PREFIX})
    SET(CMAKE_INSTALL_LIBDIR lib)
endif()

if(EMSCRIPTEN)

    find_package(Python COMPONENTS Interpreter Development REQUIRED)
else()
    # Find Python (keep the minimum in sync with requires-python in pyproject.toml)
    find_package(Python 3.12
        REQUIRED COMPONENTS Interpreter Development.Module
        OPTIONAL_COMPONENTS Development.SABIModule)
endif()

# Locate nanobind's CMake config via the Python interpreter (the approach
# recommended by the nanobind docs), unless the caller already provided it.
if(NOT nanobind_DIR AND NOT nanobind_ROOT)
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
        OUTPUT_STRIP_TRAILING_WHITESPACE
        OUTPUT_VARIABLE nanobind_ROOT
        RESULT_VARIABLE _nanobind_cmake_dir_result)
    if(NOT _nanobind_cmake_dir_result EQUAL 0)
        unset(nanobind_ROOT)
    endif()
endif()
find_package(nanobind CONFIG REQUIRED)


# one binding file per domain (see src/bind/bind.hpp)
SET(PY_SOURCES
    src/bind/module.cpp
    src/bind/base.cpp
    src/bind/vec2.cpp
    src/bind/math.cpp
    src/bind/collision.cpp
    src/bind/dynamic_tree.cpp
    src/bind/defs.cpp
    src/bind/joint_defs.cpp
    src/bind/world.cpp
    src/bind/body.cpp
    src/bind/shape.cpp
    src/bind/chain.cpp
    src/bind/joint.cpp
    src/bind/events.cpp
    src/bind/recording.cpp
    src/bind/debug_draw.cpp
    src/bind/world_to_canvas.cpp
    src/bind/extras.cpp
)
if(NOT PYB2D3_NO_THREADING)
    list(APPEND PY_SOURCES src/bind/threadpool.cpp)
endif()


if(NOT EMSCRIPTEN)
    nanobind_add_module(_pyb2d3 STABLE_ABI ${PY_SOURCES})
else()
    nanobind_add_module(_pyb2d3 ${PY_SOURCES})
endif()


# pass side module flags
if(EMSCRIPTEN)
    set_target_properties(_pyb2d3 PROPERTIES  LINK_FLAGS "-sSIDE_MODULE=1")
endif()


if(NOT PYB2D3_NO_THREADING)
    set(THREADS_PREFER_PTHREAD_FLAG ON)
    find_package(Threads REQUIRED)
    target_link_libraries(_pyb2d3 PRIVATE Threads::Threads)
endif()

# include directories
target_include_directories(_pyb2d3
    PRIVATE ${CMAKE_SOURCE_DIR}/include)

if(PYB2D3_NO_THREADING)
    target_compile_definitions(_pyb2d3 PRIVATE PYB2D3_NO_THREADING)
endif()
if(NOT PYB2D3_BATCH_API)
    target_compile_definitions(_pyb2d3 PRIVATE PYB2D3_NO_BATCH_API)
endif()

# link box2d
target_link_libraries(_pyb2d3 PRIVATE box2d::box2d)

# in-place builds: after each build, copy the extension next to the python sources.
# Not for pip / scikit-build builds: a stray _pyb2d3.abi3.so there would shadow later
# in-place builds (python prefers the abi3 suffix over a plain .so)
if(NOT DEFINED SKBUILD)
    add_custom_command(TARGET _pyb2d3 POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:_pyb2d3> ${CMAKE_SOURCE_DIR}/src/module/pyb2d3
        COMMENT "Copying _pyb2d3 to python package directory"
    )
endif()

if(NOT DEFINED SKBUILD)
    # on mac or linux, set the shared library suffix to .so
    if(APPLE OR UNIX)
        set_target_properties(_pyb2d3 PROPERTIES SUFFIX ".so")
    endif()
else()
    message(STATUS "using SKBUILD" ${SKBUILD})
endif()

# INSTALL
###################
# if SKBUILD is defined, install to the python package directory
if(DEFINED SKBUILD)
    message(STATUS "using SKBUILD" ${SKBUILD})
    install(TARGETS _pyb2d3 LIBRARY DESTINATION ${SKBUILD_PROJECT_NAME})
    # skip in-place build products (e.g. a native _pyb2d3.so copied there by a dev build)
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/src/module/pyb2d3/ DESTINATION ${SKBUILD_PROJECT_NAME}
        PATTERN "_pyb2d3*.so" EXCLUDE
        PATTERN "_pyb2d3*.pyd" EXCLUDE
        PATTERN "__pycache__" EXCLUDE)
else()
    message(STATUS "not using SKBUILD")
endif()
