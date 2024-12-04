

# find imgui
find_package(imgui REQUIRED)
find_package(glfw3 REQUIRED)
find_package(glad REQUIRED)
find_package(enkiTS REQUIRED)

# jsmn for json
set(JSMN_DIR ${CMAKE_SOURCE_DIR}/extern/jsmn)

add_library(jsmn INTERFACE ${JSMN_DIR}/jsmn.h)
target_include_directories(jsmn INTERFACE ${JSMN_DIR})

set(BOX2D_SAMPLE_FILES
	draw.cpp
	draw.h
	not_main.cpp
	sample.cpp
	sample.h
	settings.h
	shader.cpp
	shader.h)

# add_executable(samples ${BOX2D_SAMPLE_FILES})

# set_target_properties(samples PROPERTIES
# 	CXX_STANDARD 17
#     CXX_STANDARD_REQUIRED YES
#     CXX_EXTENSIONS NO
# )


nanobind_add_module(_bb2d_samples bb2d_samples.cpp
${BOX2D_SAMPLE_FILES}
)

# Copy font files, etc
add_custom_command(
	TARGET _bb2d_samples POST_BUILD
	COMMAND ${CMAKE_COMMAND} -E copy_directory
			${CMAKE_CURRENT_SOURCE_DIR}/data/
			${CMAKE_CURRENT_BINARY_DIR}/data/)

source_group(TREE ${CMAKE_CURRENT_SOURCE_DIR} FILES ${BOX2D_SAMPLE_FILES})


find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(nanobind CONFIG REQUIRED)



target_include_directories(_bb2d_samples PRIVATE ${CMAKE_CURRENT_SOURCE_DIR} ${JSMN_DIR}
	${ENKITS_INCLUDE_DIRS} ${IMGUI_INCLUDE_DIRS} ${GLFW_INCLUDE_DIRS} ${GLAD_INCLUDE_DIRS} ${SHARED_INCLUDE_DIRS}
)

target_link_libraries(_bb2d_samples PUBLIC box2d  imgui glfw glad enkiTS)


# after each build, copy the extension to the python package directory
add_custom_command(TARGET _bb2d_samples POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:_bb2d_samples> ${CMAKE_SOURCE_DIR}/python/module/bb2d_samples
    COMMENT "Copying _bb2d_samples to python package directory"
)

