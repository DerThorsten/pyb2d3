cmake_minimum_required(VERSION 3.22)
project(pyb2d)
include(FetchContent)


OPTION(BUILD_SHARED_LIBS "Build shared libraries" OFF)



if(DEFINED SKBUILD)
    SET(CMAKE_INSTALL_LIBDIR ${SKBUILD_PROJECT_NAME}/lib)
else()
    SET(INSTALL_DIR  ${CMAKE_INSTALL_PREFIX})
    SET(CMAKE_INSTALL_LIBDIR lib)
endif()

if(EMSCRIPTEN)
    set_property(GLOBAL PROPERTY TARGET_SUPPORTS_SHARED_LIBS TRUE)
    set(CMAKE_SHARED_LIBRARY_CREATE_C_FLAGS "-s SIDE_MODULE=1")
    set(CMAKE_SHARED_LIBRARY_CREATE_CXX_FLAGS "-s SIDE_MODULE=1")
    set(CMAKE_STRIP FALSE)  # used by default in pybind11 on .so modules


    # Create a target that holds Python module information
    add_library(MyFakePythonModule INTERFACE)

    # Define the include directories
    set_target_properties(MyFakePythonModule PROPERTIES
        INTERFACE_INCLUDE_DIRECTORIES "${Python_INCLUDE_DIRS}"
    )

    # Define the link libraries (the actual Python library)
    set_target_properties(MyFakePythonModule PROPERTIES
        INTERFACE_LINK_LIBRARIES "${Python_LIBRARIES}"
    )

    # Optionally, if nanobind uses the Python executable path:
    set_target_properties(MyFakePythonModule PROPERTIES
        INTERFACE_COMPILE_DEFINITIONS "PYTHON_EXECUTABLE=\"${Python_EXECUTABLE}\""
    )

    # Attempt to create an alias (might not fully satisfy the check)
    add_library(Python::Module ALIAS MyFakePythonModule)
else()
    # Find Python
    find_package(Python COMPONENTS Interpreter Development REQUIRED)
endif()

find_package(box2d REQUIRED)
find_package(nanobind CONFIG REQUIRED)

# add compile definitions
add_compile_definitions(B2_DISABLE_CXX_OPERATORS)

nanobind_add_module(_pyb2d
    src/main.cpp
    src/export_box2d_types.cpp
    src/export_box2d_wrapper_structs.cpp
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
