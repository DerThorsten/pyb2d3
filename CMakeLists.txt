cmake_minimum_required(VERSION 3.22)
project(pyb2d)
include(FetchContent)


OPTION(BUILD_SHARED_LIBS "Build shared libraries" OFF)
OPTION(PYB2D3_NO_THREADING "Disable threading support" OFF)


# this is only relevant if we are building box2d
# (ie if FETCH_BOX2D is ON)
OPTION(FETCH_BOX2D          "Download/Fetch Box2D" ON)
option(BUILD_SHARED_LIBS    "Build using shared libraries" OFF)

if(FETCH_BOX2D)
    set(CMAKE_POSITION_INDEPENDENT_CODE ON)
    FetchContent_Declare(
        box2d
        GIT_REPOSITORY https://github.com/erincatto/box2d.git
        GIT_TAG v3.1.1
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
    # Find Python

    find_package(Python 3.9
        REQUIRED COMPONENTS Interpreter Development.Module
        OPTIONAL_COMPONENTS Development.SABIModule)
        # Import nanobind through CMake's find_package mechanism
        find_package(nanobind CONFIG REQUIRED)

endif()



# find_package(box2d REQUIRED)
find_package(nanobind CONFIG REQUIRED)


SET(PY_SOURCES
    src/main.cpp
    src/export_box2d_types.cpp
    src/export_box2d_wrapper_structs.cpp
    src/export_collision.cpp
    src/export_math_functions.cpp
    src/export_batch_api.cpp
    src/export_world_to_canvas.cpp
    src/export_extras.cpp
    src/py_debug_draw.cpp
)
if(NOT PYB2D3_NO_THREADING)
    # if not emscripten, add the main.cpp file
    list(APPEND PY_SOURCES src/export_threadpool.cpp)
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

# link box2d
target_link_libraries(_pyb2d3 PRIVATE box2d::box2d)

# after each build, copy the extension to the python package directory
add_custom_command(TARGET _pyb2d3 POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:_pyb2d3> ${CMAKE_SOURCE_DIR}/src/module/pyb2d3
    COMMENT "Copying _pyb2d3 to python package directory"
)

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
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/src/module/pyb2d3/ DESTINATION ${SKBUILD_PROJECT_NAME})
else()
    message(STATUS "not using SKBUILD")
endif()
