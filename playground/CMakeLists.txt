cmake_minimum_required(VERSION 3.22)
project(pyb2d_playground)
include(FetchContent)


OPTION(BUILD_SHARED_LIBS "Build shared libraries" OFF)

if(DEFINED SKBUILD)
    SET(CMAKE_INSTALL_LIBDIR ${SKBUILD_PROJECT_NAME}/lib)
else()
    SET(INSTALL_DIR  ${CMAKE_INSTALL_PREFIX})
    SET(CMAKE_INSTALL_LIBDIR lib)
endif()

message("INSTALL_DIR: ${INSTALL_DIR}")
message("PYB2D_INCLUDE_DIR  ${PYB2D_INCLUDE_DIR}")


find_package(box2d REQUIRED)
find_package(enkiTS REQUIRED)
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(glfw3 REQUIRED)
find_package(glad REQUIRED)
find_package(imgui REQUIRED)
find_package(nanobind CONFIG REQUIRED)

# # add compile definitions
add_compile_definitions(B2_DISABLE_CXX_OPERATORS)

nanobind_add_module(_pyb2d_playground
    src/cpp/main.cpp
    src/cpp/opengl_frontend/draw.cpp
    src/cpp/opengl_frontend/opengl_frontend.cpp
    src/cpp/opengl_frontend/not_main.cpp
    src/cpp/opengl_frontend/shader.cpp
    src/cpp/sample.cpp
    src/cpp/frontend_base.cpp
)

# include directories
target_include_directories(_pyb2d_playground
    PRIVATE ${CMAKE_SOURCE_DIR}/include
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src/cpp
    PRIVATE ${PYB2D_INCLUDE_DIR}
)

# link box2d
target_link_libraries(_pyb2d_playground PRIVATE box2d::box2d
    enkiTS
    glfw
    glad
    imgui::imgui
)

# after each build, copy the extension to the python package directory
add_custom_command(TARGET _pyb2d_playground POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:_pyb2d_playground> ${CMAKE_SOURCE_DIR}/src/module/pyb2d_playground
    COMMENT "Copying _pyb2d_playground to python package directory"
)

if(NOT DEFINED SKBUILD)
    # on mac or linux, set the shared library suffix to .so
    if(APPLE OR UNIX)
        set_target_properties(_pyb2d_playground PROPERTIES SUFFIX ".so")
    endif()
else()
    message(STATUS "using SKBUILD" ${SKBUILD})
endif()

# INSTALL
###################
# if SKBUILD is defined, install to the python package directory
if(DEFINED SKBUILD)
    message(STATUS "using SKBUILD" ${SKBUILD})
    install(TARGETS _pyb2d_playground LIBRARY DESTINATION ${SKBUILD_PROJECT_NAME})
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/src/module/pyb2d_playground/ DESTINATION ${SKBUILD_PROJECT_NAME})
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/include/ DESTINATION ${SKBUILD_PROJECT_NAME}/include)
else()
    message(STATUS "not using SKBUILD")
endif()
