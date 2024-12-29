

# find imgui
find_package(imgui REQUIRED)
find_package(glfw3 REQUIRED)
find_package(glad REQUIRED)
find_package(enkiTS REQUIRED)

# jsmn for json
set(JSMN_DIR ${CMAKE_SOURCE_DIR}/extern/jsmn)



set(BOX2D_SAMPLE_FILES
	opengl_frontend/draw.cpp
	opengl_frontend/opengl_frontend.cpp
	opengl_frontend/not_main.cpp
	opengl_frontend/shader.cpp
	sample.cpp
	frontend_base.cpp

)

# add_executable(samples ${BOX2D_SAMPLE_FILES})

# set_target_properties(samples PROPERTIES
# 	CXX_STANDARD 17
#     CXX_STANDARD_REQUIRED YES
#     CXX_EXTENSIONS NO
# )


nanobind_add_module(_pyb2d_playground main.cpp
${BOX2D_SAMPLE_FILES}
)

target_include_directories(_pyb2d_playground PRIVATE ${CMAKE_SOURCE_DIR}/include ${CMAKE_CURRENT_SOURCE_DIR})

# Copy font files, etc
add_custom_command(
	TARGET _pyb2d_playground POST_BUILD
	COMMAND ${CMAKE_COMMAND} -E copy_directory
			${CMAKE_CURRENT_SOURCE_DIR}/data/
			${CMAKE_SOURCE_DIR}/python/module/pyb2d_samples/data/)
			

source_group(TREE ${CMAKE_CURRENT_SOURCE_DIR} FILES ${BOX2D_SAMPLE_FILES})


find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(nanobind CONFIG REQUIRED)



target_include_directories(_pyb2d_playground PRIVATE ${CMAKE_CURRENT_SOURCE_DIR} ${JSMN_DIR}
	${ENKITS_INCLUDE_DIRS} ${IMGUI_INCLUDE_DIRS} ${GLFW_INCLUDE_DIRS} ${GLAD_INCLUDE_DIRS} ${SHARED_INCLUDE_DIRS}
)

target_link_libraries(_pyb2d_playground PUBLIC
 box2d imgui glfw glad enkiTS
)


# after each build, copy the extension to the python package directory
add_custom_command(TARGET _pyb2d_playground POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:_pyb2d_playground> ${CMAKE_SOURCE_DIR}/python/module/pyb2d_samples
    COMMENT "Copying _pyb2d_playground to python package directory"
)

install(TARGETS _pyb2d_playground LIBRARY DESTINATION pyb2d/playground)

