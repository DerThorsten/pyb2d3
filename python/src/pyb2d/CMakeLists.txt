find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(nanobind CONFIG REQUIRED)


nanobind_add_module(_pyb2d main.cpp
    export_box2d_types.cpp
    export_box2d_functions.cpp
    export_collision.cpp
    export_math_functions.cpp
    py_debug_draw.cpp
)

# include directories
target_include_directories(_pyb2d PRIVATE ${CMAKE_SOURCE_DIR}/include)

# link box2d
target_link_libraries(_pyb2d PRIVATE box2d::box2d)


# after each build, copy the extension to the python package directory
add_custom_command(TARGET _pyb2d POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:_pyb2d> ${CMAKE_SOURCE_DIR}/python/module/pyb2d
    COMMENT "Copying _pyb2d to python package directory"
)


if(WITH_PYTHON_TESTS)
    # run unit tests via pytest
    add_custom_target(test
        COMMAND ${CMAKE_COMMAND} 
            -E env PYTHONPATH=${CMAKE_SOURCE_DIR}/python/module pytest ${CMAKE_SOURCE_DIR}/python/test -s
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        COMMENT "Running unit tests"
    )
    # make test depend on the extension
    add_dependencies(test _pyb2d)
endif()