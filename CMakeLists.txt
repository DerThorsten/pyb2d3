cmake_minimum_required(VERSION 3.22)
project(pyb2d)
include(FetchContent)

OPTION(USE_SHARED_BOX2D "Use shared box2d library" OFF)
SET(BUILD_SHARED_LIBS ${USE_SHARED_BOX2D})
message("USE_SHARED_BOX2D: ${USE_SHARED_BOX2D}")
FetchContent_Declare(
	box2d
	GIT_REPOSITORY https://github.com/DerThorsten/box2d.git
	GIT_TAG 30c080e56efd13ef5aa8872db63d95b816ca23e0
	GIT_SHALLOW TRUE
	GIT_PROGRESS TRUE
    CMAKE_ARGS
        -DOPTION_ONE=ON
        -DOPTION_TWO=OFF
        -DBOX2D_UNIT_TESTS=OFF
        -DBOX2D_BENCHMARKS=OFF
        -DBOX2D_SAMPLES=OFF
        -DBUILD_SHARED_LIBS=${USE_SHARED_BOX2D}
)
FetchContent_MakeAvailable(box2d)

find_package(box2d REQUIRED)
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(nanobind CONFIG REQUIRED)

# add compile definitions
add_compile_definitions(B2_DISABLE_CXX_OPERATORS)

nanobind_add_module(_pyb2d
    src/main.cpp
    src/export_box2d_types.cpp
    src/export_box2d_functions.cpp
    src/export_collision.cpp
    src/export_math_functions.cpp
    src/py_debug_draw.cpp
)

# include directories
target_include_directories(_pyb2d
    PRIVATE ${CMAKE_SOURCE_DIR}/include)

# link box2d
target_link_libraries(_pyb2d PRIVATE box2d::box2d)

# after each build, copy the extension to the python package directory
add_custom_command(TARGET _pyb2d POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:_pyb2d> ${CMAKE_SOURCE_DIR}/src/module/pyb2d
    COMMENT "Copying _pyb2d to python package directory"
)

if(NOT DEFINED SKBUILD)
    # on mac or linux, set the shared library suffix to .so
    if(APPLE OR UNIX)
        set_target_properties(_pyb2d PROPERTIES SUFFIX ".so")
    endif()
else()
    message(STATUS "using SKBUILD" ${SKBUILD})
endif()

# INSTALL
###################
# if SKBUILD is defined, install to the python package directory
if(DEFINED SKBUILD)
    message(STATUS "using SKBUILD" ${SKBUILD})
    install(TARGETS _pyb2d LIBRARY DESTINATION ${SKBUILD_PROJECT_NAME})
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/src/module/pyb2d/ DESTINATION ${SKBUILD_PROJECT_NAME})
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/include/ DESTINATION ${SKBUILD_PROJECT_NAME}/include)
else()
    message(STATUS "not using SKBUILD")
endif()
