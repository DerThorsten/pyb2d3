find_package(Python COMPONENTS Interpreter Development
        REQUIRED)
message(STATUS "Python_INCLUDE_DIRS: ${PYTHON_INCLUDE_DIRS}")
message(STATUS "Python_INCLUDE_DIRS: ${Python_INCLUDE_DIRS}")
find_package(nanobind CONFIG REQUIRED)

include_directories(${Python_INCLUDE_DIRS})



nanobind_add_module(_pyb2d
    # Target the stable ABI for Python 3.12+, which reduces
    # the number of binary wheels that must be built. This
    # does nothing on older Python versions

    main.cpp

    export_box2d_types.cpp
    export_box2d_functions.cpp
    export_collision.cpp
    export_math_functions.cpp
    py_debug_draw.cpp
)

# include directories
target_include_directories(_pyb2d
    PRIVATE ${CMAKE_SOURCE_DIR}/include
#python include
    PRIVATE ${PYTHON_INCLUDE_DIRS}
    )

# link box2d
target_link_libraries(_pyb2d PRIVATE box2d::box2d)


install(TARGETS _pyb2d LIBRARY DESTINATION pyb2d)

#  install everything from ${CMAKE_SOURCE_DIR}/src/pyb2d to the python package directory
install(DIRECTORY ${CMAKE_SOURCE_DIR}/src/pyb2d/ DESTINATION pyb2d)

# # after each build, copy the extension to the python package directory
# add_custom_command(TARGET _pyb2d POST_BUILD
#     COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:_pyb2d> ${CMAKE_SOURCE_DIR}/python/module/pyb2d
#     COMMENT "Copying _pyb2d to python package directory"
# )


# add_custom_command(OUTPUT ${CMAKE_SOURCE_DIR}/python/module/pyb2d
#     COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:_pyb2d> ${CMAKE_SOURCE_DIR}/python/module/pyb2d
#     DEPENDS _pyb2d
#     COMMENT "Copying _pyb2d to python package directory2"
# )
# add_custom_target(copy_pyb2d ALL DEPENDS ${CMAKE_SOURCE_DIR}/python/module/pyb2d)


# install(TARGETS _pyb2d DESTINATION ${SKBUILD_PROJECT_NAME})

# # install pure python module
# install(DIRECTORY ${CMAKE_SOURCE_DIR}/python/module/ DESTINATION ${SKBUILD_PROJECT_NAME})


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
