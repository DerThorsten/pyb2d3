#include <nanobind/nanobind.h>

#include "converter.hpp"

namespace py = nanobind;

void export_box2d_types(py::module_ &m);
void export_box2d_functions(py::module_ &m);
void export_collision(py::module_ & m);

NB_MODULE(_bb2d, m) {
    export_box2d_types(m);
    export_box2d_functions(m);
    export_collision(m);
}