#include <nanobind/nanobind.h>

#include <pyb2d/py_converter.hpp>

namespace py = nanobind;

void export_box2d_types(py::module_ &m);
void export_box2d_functions(py::module_ &m);
void export_collision(py::module_ & m);
void export_py_debug_draw(py::module_ &m);
void export_math_functions(py::module_ & m);

NB_MODULE(_pyb2d, m) {
    export_box2d_types(m);
    export_box2d_functions(m);
    export_collision(m);
    export_py_debug_draw(m);
    export_math_functions(m);
}
