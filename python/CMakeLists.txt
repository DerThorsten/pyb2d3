find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(nanobind CONFIG REQUIRED)


nanobind_add_module(pybb2d pybb2d.cpp)


# link box2d
target_link_libraries(pybb2d PRIVATE box2d::box2d)