cmake_minimum_required(VERSION 3.22)
project(${SKBUILD_PROJECT_NAME})

find_package(box2d REQUIRED)
find_package(Python COMPONENTS Interpreter Development
        REQUIRED)

# add compile definitions
add_compile_definitions(B2_DISABLE_CXX_OPERATORS)


message(STATUS "Python_INCLUDE_DIRS: ${PYTHON_INCLUDE_DIRS}")
message(STATUS "Python_INCLUDE_DIRS: ${Python_INCLUDE_DIRS}")
find_package(nanobind CONFIG REQUIRED)


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


install(TARGETS _pyb2d LIBRARY DESTINATION pyb2d)
install(DIRECTORY ${CMAKE_SOURCE_DIR}/src/pyb2d/ DESTINATION pyb2d)
